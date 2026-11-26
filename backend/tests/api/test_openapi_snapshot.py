import json
import os
from pathlib import Path
from typing import Any, Final

from fastapi import FastAPI

# the dashboard's TypeScript types are generated from this file
# (frontend: npm run api:types)
_SNAPSHOT: Final[Path] = (
    Path(__file__).parents[3] / "frontend" / "src" / "shared" / "api" / "openapi.json"
)
_UPDATE_HINT: Final[str] = (
    "API schemas changed: run `UPDATE_OPENAPI=1 uv run pytest tests/api/test_openapi_snapshot.py`"
    " in backend/, then `npm run api:types` in frontend/"
)


def _schemas_document(app: FastAPI) -> str:
    schema = app.openapi()
    # models only: paths repeat every error response per route, and the version
    # would change the file on every release
    document: dict[str, Any] = {
        "openapi": schema["openapi"],
        "info": {"title": schema["info"]["title"], "version": "0"},
        "paths": {},
        "components": {"schemas": schema["components"]["schemas"]},
    }
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def test_openapi_snapshot_matches_the_api(api_app: FastAPI) -> None:
    current = _schemas_document(api_app)
    if os.environ.get("UPDATE_OPENAPI") == "1":
        _SNAPSHOT.write_text(current)
    assert _SNAPSHOT.exists() and _SNAPSHOT.read_text() == current, _UPDATE_HINT
