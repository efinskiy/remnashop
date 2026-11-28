import ast
from collections.abc import Iterator
from pathlib import Path
from typing import Final

_APP_DIR: Final[Path] = Path(__file__).parents[1] / "app"

# a refusal is the caller's decision; a repository only maps a database error to one
_DECISION_ERRORS: Final[frozenset[str]] = frozenset(
    {
        "ValidationError",
        "PermissionDeniedError",
        "CooldownError",
        "AuthenticationError",
        "SupersededError",
        "OrderNotPaidError",
    }
)
# the modules that hold a domain's rules; a repository applying them decides for its caller
_RULE_MODULES: Final[tuple[str, ...]] = (".rules", ".availability")
_ALLOWED: Final[frozenset[str]] = frozenset(
    {
        # a CHECK constraint violation turned into its error, called from an except block
        "advertising/repository.py:_raise_if_no_channel",
        # one of the 50 dialog states the bot declares, a storage capacity like a unique index
        "dialogs/repository.py:_claim_free_slot",
        # the rate rows are seeded for every currency; a missing one is broken data
        "pricing/repository.py:update_rate",
        "pricing/repository.py:set_anchor",
        # every purchase path claims and links through here, so none can skip it
        "subscriptions/idempotency_repository.py:_assert_order_paid",
        # the floor and cap sit in the UPDATE's own WHERE; the error names which one failed
        "users/repository.py:credit_points",
        "users/repository.py:credit_bonus_days",
    }
)


def _repositories() -> Iterator[Path]:
    return iter(sorted(_APP_DIR.rglob("*repository*.py")))


def _key(path: Path, function: str) -> str:
    return f"{path.relative_to(_APP_DIR / 'modules')}:{function}"


def _raised_decisions(tree: ast.AST) -> Iterator[tuple[str, int]]:
    in_handler = {
        id(node)
        for handler in ast.walk(tree)
        if isinstance(handler, ast.ExceptHandler)
        for node in ast.walk(handler)
    }
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Raise)
                and id(node) not in in_handler
                and isinstance(node.exc, ast.Call)
                and isinstance(node.exc.func, ast.Name)
                and node.exc.func.id in _DECISION_ERRORS
            ):
                yield function.name, node.lineno


def test_repositories_leave_refusals_to_their_callers() -> None:
    offenders = sorted(
        f"{_key(path, function)} (line {line})"
        for path in _repositories()
        for function, line in _raised_decisions(ast.parse(path.read_text()))
        if _key(path, function) not in _ALLOWED
    )
    assert offenders == [], "a repository returns what it found; the usecase refuses"


def test_repositories_do_not_apply_domain_rules() -> None:
    offenders = sorted(
        f"{path.relative_to(_APP_DIR)}: {node.module}"
        for path in _repositories()
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.endswith(_RULE_MODULES)
    )
    assert offenders == [], "rules are applied by the usecase, not the repository"


def test_every_allowed_refusal_still_exists() -> None:
    found = {
        _key(path, function)
        for path in _repositories()
        for function, _ in _raised_decisions(ast.parse(path.read_text()))
    }
    assert _ALLOWED <= found, "drop the allowlist entry of a refusal that is gone"
