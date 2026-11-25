from typing import Any

from fastapi import FastAPI


def _inline_enum(schema: dict[str, Any]) -> bool:
    if "enum" in schema:
        return True
    if schema.get("type") == "array":
        return _inline_enum(schema.get("items", {}))
    return any(_inline_enum(option) for option in schema.get("anyOf", []))


def test_every_enum_parameter_is_a_named_schema(api_app: FastAPI) -> None:
    # a Literal parameter is inlined into the route and never reaches the
    # snapshot the dashboard's types are generated from; a StrEnum is a model
    inline = [
        f"{method.upper()} {path} {parameter['name']}"
        for path, path_item in api_app.openapi()["paths"].items()
        for method, operation in path_item.items()
        for parameter in operation.get("parameters", [])
        if _inline_enum(parameter.get("schema", {}))
    ]
    assert inline == []
