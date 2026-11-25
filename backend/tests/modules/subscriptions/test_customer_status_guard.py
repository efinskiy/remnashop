import ast
from collections.abc import Iterator
from pathlib import Path
from typing import Final

_APP_DIR: Final[Path] = Path(__file__).parents[3] / "app"
# the rule's switch-off is DISABLED in the panel and EXPIRED to everyone else
_AMBIGUOUS: Final[frozenset[str]] = frozenset({"EXPIRED", "DISABLED"})
_MARKS: Final[tuple[str, ...]] = ("customer_status", "disabled_by_expiry", "expiry_disabled_at")
_SKIPPED: Final[tuple[str, ...]] = ("modules/subscriptions/", "cli/", "core/db/models/")
_ALLOWED: Final[dict[str, str]] = {
    "core/db/filters.py": "expired_subscription() itself",
    "modules/customer_notifications/usecases/notify_customer.py": (
        "the warning is dropped once the subscription is switched off"
    ),
}


def _is_ambiguous(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr in _AMBIGUOUS
        and isinstance(node.value, ast.Name)
        and node.value.id == "SubscriptionStatus"
    )


def _reads_status(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "status"


def _status_checks(tree: ast.AST) -> Iterator[ast.expr]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            if any(map(_reads_status, operands)) and any(map(_is_ambiguous, operands)):
                yield node
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("in_", "notin_")
            and _reads_status(node.func.value)
            and any(_is_ambiguous(sub) for arg in node.args for sub in ast.walk(arg))
        ):
            yield node


def _outermost_expression(node: ast.expr, parents: dict[ast.AST, ast.AST]) -> ast.expr:
    while isinstance(parents.get(node), ast.expr):
        node = parents[node]  # type: ignore[assignment]
    return node


def test_outside_subscriptions_expired_and_disabled_go_through_customer_status() -> None:
    offenders = []
    for path in sorted(_APP_DIR.rglob("*.py")):
        relative = path.relative_to(_APP_DIR).as_posix()
        if relative.startswith(_SKIPPED) or relative in _ALLOWED:
            continue
        source = path.read_text()
        tree = ast.parse(source)
        parents = {
            child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
        }
        for check in _status_checks(tree):
            segment = ast.get_source_segment(source, _outermost_expression(check, parents)) or ""
            if not any(mark in segment for mark in _MARKS):
                offenders.append(f"{relative}:{check.lineno}")
    assert offenders == [], (
        "a subscription switched off by the expiry rule is DISABLED here and EXPIRED to the "
        "customer: read customer_status, or filter with core.db.filters.expired_subscription()"
    )
