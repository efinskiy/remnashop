import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

import app.modules

_TASK_MODULES: Final[list[str]] = sorted(
    f"app.modules.{path.parent.name}.tasks"
    for path in Path(app.modules.__file__).parent.glob("*/tasks.py")
)


@pytest.mark.parametrize("module_name", _TASK_MODULES)
def test_tasks_module_imports_cleanly_in_a_fresh_interpreter(module_name: str) -> None:
    """A circular import shows up only when a fresh process imports the module
    first; taskiq's --fs-discover imports tasks modules in set order, so any of
    them can be first. pytest's own import order never hits it."""
    result = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
