from typing import get_args

from app.core.enums import Role
from app.modules.users.schemas import RoleName


def test_role_name_lists_every_role() -> None:
    assert set(get_args(RoleName)) == {role.name for role in Role}
