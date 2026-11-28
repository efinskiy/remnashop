from typing import Annotated, get_args, get_origin, get_type_hints

from fastapi.routing import APIRoute

from app.api.dependencies.admin import require_admin_user
from app.core.security.permissions import TOKEN_GRANTABLE_PERMISSIONS, Permission
from app.core.usecase import UseCase
from app.modules.users import UserDto
from tests.api.test_admin_router_enforcement import _discover_admin_routers
from tests.core.security.test_permission_uniqueness import _discover_use_case_classes


def _takes_user_only(cls: type[UseCase]) -> bool:
    for klass in cls.__mro__:
        for base in getattr(klass, "__orig_bases__", ()):
            if get_origin(base) is UseCase:
                args = get_args(base)
                return len(args) == 3 and args[2] is UserDto
    return False


def _needs_admin_user(route: APIRoute) -> bool:
    pending = list(route.dependant.dependencies)
    while pending:
        dep = pending.pop()
        if dep.call is require_admin_user:
            return True
        pending.extend(dep.dependencies)
    return False


def _route_use_cases(route: APIRoute) -> list[type[UseCase]]:
    # dishka's @inject hides FromDishka parameters from the endpoint it returns
    endpoint = getattr(route.endpoint, "__dishka_orig_func__", route.endpoint)
    hints = get_type_hints(endpoint, include_extras=True)
    return [
        get_args(hint)[0]
        for hint in hints.values()
        if get_origin(hint) is Annotated
        and isinstance(get_args(hint)[0], type)
        and issubclass(get_args(hint)[0], UseCase)
    ]


def _unreachable_by_token() -> set[Permission]:
    # a token has no account: a usecase typed for UserDto or a route behind
    # require_admin_user answers it 403
    unreachable: set[Permission] = {
        cls.required_permission
        for cls in _discover_use_case_classes()
        if cls.required_permission is not None and _takes_user_only(cls)
    }
    for _, router in _discover_admin_routers():
        for route in router.routes:
            if isinstance(route, APIRoute) and _needs_admin_user(route):
                unreachable |= {
                    cls.required_permission
                    for cls in _route_use_cases(route)
                    if cls.required_permission is not None
                }
    return unreachable


def test_every_token_grantable_permission_is_callable_by_a_token() -> None:
    assert sorted(_unreachable_by_token() & TOKEN_GRANTABLE_PERMISSIONS) == []


def test_reachability_check_finds_both_kinds() -> None:
    unreachable = _unreachable_by_token()
    assert Permission.EMAIL_SETTINGS_TEST in unreachable  # UserDto usecase
    assert Permission.REMNAWAVE_NODES_VIEW in unreachable  # require_admin_user route
    assert Permission.USERS_VIEW not in unreachable
