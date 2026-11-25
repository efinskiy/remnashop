import importlib
import re
import typing
from pathlib import Path
from typing import Any, Final

import pytest
from dishka import Scope
from taskiq import AsyncTaskiqDecoratedTask

import app.modules
from app.core.config import AppConfig
from app.worker.container import create_worker_container

_ENTRYPOINT: Final[Path] = Path(__file__).parents[3] / "docker-entrypoint.sh"
_MODULES_DIR: Final[Path] = Path(app.modules.__file__).parent


_BACKEND_DIR: Final[Path] = _ENTRYPOINT.parent / "backend"


def _discovered_task_modules(command: str) -> set[str]:
    # the pattern taskiq globs from WORKDIR (/opt/remnashop, laid out like backend/)
    line = next(line for line in _ENTRYPOINT.read_text().splitlines() if command in line)
    assert "--fs-discover" in line
    match = re.search(r'--tasks-pattern "([^"]+)"', line)
    assert match is not None, f"{command} has no quoted --tasks-pattern"
    return {
        ".".join(path.relative_to(_BACKEND_DIR).with_suffix("").parts)
        for path in _BACKEND_DIR.glob(match.group(1))
    }


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


@pytest.mark.parametrize("command", ["exec taskiq worker", "exec taskiq scheduler"])
def test_command_discovers_every_tasks_module(command: str) -> None:
    # a module the scheduler misses is never kicked; one the worker misses never runs
    assert _discovered_task_modules(command) == _TASK_MODULES_ON_DISK


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
