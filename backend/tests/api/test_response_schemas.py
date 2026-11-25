from typing import Any

from fastapi import FastAPI


def _refs(node: Any, found: set[str]) -> None:
    if isinstance(node, dict):
        if "$ref" in node:
            found.add(node["$ref"].rsplit("/", 1)[-1])
        for value in node.values():
            _refs(value, found)
    elif isinstance(node, list):
        for value in node:
            _refs(value, found)


def test_every_response_model_requires_all_its_fields(api_app: FastAPI) -> None:
    # every response sends every field: one the schema calls optional would be
    # `field?:` in the dashboard's generated types (core.dto.ResponseModel)
    schema = api_app.openapi()
    models = schema["components"]["schemas"]
    pending: set[str] = set()
    for path_item in schema["paths"].values():
        for operation in path_item.values():
            for status, response in operation["responses"].items():
                if status.startswith("2"):
                    _refs(response, pending)
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        _refs(models[name], pending)

    optional = {
        name: sorted(set(models[name]["properties"]) - set(models[name].get("required", [])))
        for name in sorted(seen)
        if "properties" in models[name]
    }
    assert {name: fields for name, fields in optional.items() if fields} == {}
