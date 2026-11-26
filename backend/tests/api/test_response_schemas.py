from typing import Any, Final

from fastapi import FastAPI

# answers whose shape is not ours: WebAuthn options are the library's own JSON,
# the webhooks answer what the panel and each gateway expect
_UNTYPED_JSON_OPERATIONS: Final[frozenset[str]] = frozenset(
    {
        "get_registration_options",
        "get_authentication_options",
        "receive_remnawave_webhook",
        "receive_payment_webhook",
    }
)


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


def test_every_json_response_has_a_model(api_app: FastAPI) -> None:
    # a route answering with a file or nothing sets response_class=Response,
    # so the schema doesn't promise JSON
    untyped = [
        operation["operationId"]
        for path_item in api_app.openapi()["paths"].values()
        for operation in path_item.values()
        for status, response in operation["responses"].items()
        if status.startswith("2")
        and response.get("content", {}).get("application/json", {}).get("schema", {}) == {}
        and "application/json" in response.get("content", {})
    ]
    assert sorted(untyped) == sorted(_UNTYPED_JSON_OPERATIONS)


def test_schema_names_are_unique(api_app: FastAPI) -> None:
    # two models of one name come out as module paths (app__modules__...),
    # unusable as the dashboard's type names
    names = api_app.openapi()["components"]["schemas"]
    assert [name for name in names if "__" in name] == []
