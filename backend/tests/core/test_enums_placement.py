import ast
import re
from pathlib import Path
from typing import Final

_CORE_DIR: Final[Path] = Path(__file__).parents[2] / "app" / "core"
_ENUMS: Final[Path] = _CORE_DIR / "enums.py"


def test_every_core_enum_is_used_by_core() -> None:
    # a database column in core/db/models, or core's own code; an enum only modules
    # use belongs to the module that owns it, in its dto.py
    names = [
        node.name for node in ast.parse(_ENUMS.read_text()).body if isinstance(node, ast.ClassDef)
    ]
    core_text = "\n".join(path.read_text() for path in _CORE_DIR.rglob("*.py") if path != _ENUMS)
    unused = [name for name in names if not re.search(rf"\b{name}\b", core_text)]
    assert unused == [], "move these to the module that owns them"
