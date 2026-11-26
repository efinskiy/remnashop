import ast
from pathlib import Path
from typing import Final

_CORE_DIR: Final[Path] = Path(__file__).parents[2] / "app" / "core"
_ENUMS: Final[Path] = _CORE_DIR / "enums.py"


def _names_used(path: Path) -> set[str]:
    # names in code, not in comments or strings
    used: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
        elif isinstance(node, ast.ImportFrom):
            used.update(alias.name for alias in node.names)
    return used


def test_every_core_enum_is_used_by_core() -> None:
    # a database column in core/db/models, or core's own code; an enum only modules
    # use belongs to the module that owns it, in its dto.py
    names = [
        node.name for node in ast.parse(_ENUMS.read_text()).body if isinstance(node, ast.ClassDef)
    ]
    used = set().union(*(_names_used(path) for path in _CORE_DIR.rglob("*.py") if path != _ENUMS))
    unused = [name for name in names if name not in used]
    assert unused == [], "move these to the module that owns them"
