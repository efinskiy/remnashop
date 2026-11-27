import importlib
import subprocess
import typing
from pathlib import Path
from typing import Any, Final, Union

import pytest
import taskiq.cli.utils as taskiq_cli_utils
from dishka import Scope
from taskiq import AsyncTaskiqDecoratedTask
from taskiq.cli.scheduler.args import SchedulerArgs
from taskiq.cli.worker.args import WorkerArgs

import app.modules
from app.core.config import AppConfig
from app.modules.event_log import RetryPoisonedOutboxUseCase
from app.worker.container import create_worker_container

_ENTRYPOINT: Final[Path] = Path(__file__).parents[3] / "docker-entrypoint.sh"
_MODULES_DIR: Final[Path] = Path(app.modules.__file__).parent
_BACKEND_DIR: Final[Path] = _ENTRYPOINT.parent / "backend"
_COMMAND_ARGS: Final[dict[str, type[Union[WorkerArgs, SchedulerArgs]]]] = {
    "worker": WorkerArgs,
    "scheduler": SchedulerArgs,
}


def _command_argv(command: str) -> list[str]:
    # the shell's own word splitting and globbing, run from a directory laid out
    # like WORKDIR (/opt/remnashop), so an unquoted pattern would expand here too
    line = next(
        line for line in _ENTRYPOINT.read_text().splitlines() if f"exec taskiq {command}" in line
    )
    script = line.replace(f"exec taskiq {command}", "printf '%s\\n'", 1)
    result = subprocess.run(
        ["sh", "-c", script], cwd=_BACKEND_DIR, capture_output=True, text=True, check=True
    )
    return result.stdout.splitlines()


def _discovered_task_modules(command: str, monkeypatch: pytest.MonkeyPatch) -> set[str]:
    args = _COMMAND_ARGS[command].from_cli(_command_argv(command))
    assert args.fs_discover
    imported: list[str] = []
    monkeypatch.setattr(taskiq_cli_utils, "import_from_modules", imported.extend)
    monkeypatch.chdir(_BACKEND_DIR)
    taskiq_cli_utils.import_tasks([], args.tasks_pattern, args.fs_discover)
    return set(imported)


_TASK_MODULES_ON_DISK: Final[set[str]] = {
    f"app.modules.{path.parent.name}.tasks" for path in _MODULES_DIR.glob("*/tasks.py")
}


def _injected_types(task: AsyncTaskiqDecoratedTask[Any, Any]) -> list[Any]:
    func = task.original_func
    hints = typing.get_type_hints(getattr(func, "__dishka_orig_func__", func), include_extras=True)
    return [
        typing.get_args(hint)[0]
        for hint in hints.values()
        if typing.get_origin(hint) is typing.Annotated
        and type(hint.__metadata__[0]).__name__ == "_FromComponent"
    ]


@pytest.mark.parametrize("command", sorted(_COMMAND_ARGS))
def test_command_discovers_every_tasks_module(
    command: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # a module the scheduler misses is never kicked; one the worker misses never runs
    assert _discovered_task_modules(command, monkeypatch) == _TASK_MODULES_ON_DISK


@pytest.mark.parametrize("module_name", sorted(_TASK_MODULES_ON_DISK))
async def test_worker_container_resolves_every_task_dependency(
    config: AppConfig, module_name: str
) -> None:
    module = importlib.import_module(module_name)
    tasks = [v for v in vars(module).values() if isinstance(v, AsyncTaskiqDecoratedTask)]
    assert tasks, f"{module_name} defines no tasks"

    container = create_worker_container(config)
    async with container(scope=Scope.REQUEST) as request_container:
        for task in tasks:
            for dependency in _injected_types(task):
                await request_container.get(dependency)
    await container.close()


async def test_worker_container_resolves_the_startup_outbox_retry(config: AppConfig) -> None:
    container = create_worker_container(config)
    async with container(scope=Scope.REQUEST) as request_container:
        await request_container.get(RetryPoisonedOutboxUseCase)
    await container.close()
