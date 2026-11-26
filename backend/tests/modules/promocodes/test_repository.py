from datetime import timedelta

import pytest

import app.modules.promocodes.repository as promocode_repository_module
from app.core.enums import PromocodeAvailability, PromocodeRewardType
from app.core.exceptions import ConflictError, NotFoundError
from app.core.utils.time import datetime_now
from app.modules.promocodes.dto import (
    CreatePromocodeDto,
    ListPromocodesDto,
    PromocodeStatus,
    UpdatePromocodeDto,
)
from app.modules.promocodes.repository import PromocodeRepository
from app.modules.promocodes.rules import is_promocode_live
from app.modules.users.dto import CreateUserDto
from app.modules.users.repository import UserRepository


def _create_dto(code: str = "WELCOME10", **overrides: object) -> CreatePromocodeDto:
    defaults: dict = {"code": code, "reward_type": PromocodeRewardType.DURATION, "reward": 30}
    defaults.update(overrides)
    return CreatePromocodeDto(**defaults)


async def _create_user(user_repository: UserRepository, telegram_id: int) -> int:
    user = await user_repository.create(CreateUserDto(name="buyer", telegram_id=telegram_id))
    return user.id


async def test_create_then_get_by_code_returns_promocode(
    promocode_repository: PromocodeRepository,
) -> None:
    created = await promocode_repository.create(_create_dto())

    found = await promocode_repository.find_by_code("WELCOME10")

    assert found is not None
    assert found.id == created.id
    assert found.is_active is True
    assert found.reward == 30


async def test_get_by_code_unknown_returns_none(promocode_repository: PromocodeRepository) -> None:
    assert await promocode_repository.find_by_code("NOPE") is None


async def test_create_duplicate_code_raises_conflict(
    promocode_repository: PromocodeRepository,
) -> None:
    await promocode_repository.create(_create_dto("DUP"))

    with pytest.raises(ConflictError):
        await promocode_repository.create(_create_dto("DUP"))


async def test_a_used_up_promocode_is_exhausted_not_active(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    full = await promocode_repository.create(_create_dto("EXH-FULL", max_activations=1))
    await promocode_repository.create(_create_dto("EXH-OPEN", max_activations=2))
    await promocode_repository.add_activation(
        full.id, await _create_user(user_repository, 1201), None
    )

    async def codes(status: PromocodeStatus) -> list[str]:
        items, _ = await promocode_repository.list_paginated(
            ListPromocodesDto(search="exh-", status=status)
        )
        return [item.code for item in items]

    assert await codes(PromocodeStatus.EXHAUSTED) == ["EXH-FULL"]
    assert await codes(PromocodeStatus.ACTIVE) == ["EXH-OPEN"]

    items, _ = await promocode_repository.list_paginated(ListPromocodesDto(search="exh-"))
    counted = await promocode_repository.with_activations_count(items)
    assert {p.code: p.activations_count for p in counted} == {"EXH-FULL": 1, "EXH-OPEN": 0}


async def test_get_by_id_unknown_raises_not_found(
    promocode_repository: PromocodeRepository,
) -> None:
    with pytest.raises(NotFoundError):
        await promocode_repository.get_by_id(999_999)


async def test_list_all_returns_created_promocodes(
    promocode_repository: PromocodeRepository,
) -> None:
    await promocode_repository.create(_create_dto("A"))
    await promocode_repository.create(_create_dto("B"))

    codes = {promo.code for promo in await promocode_repository.list_all()}

    assert codes == {"A", "B"}


async def test_list_paginated_filters_by_derived_status_and_puts_live_first(
    promocode_repository: PromocodeRepository,
) -> None:
    off = await promocode_repository.create(_create_dto("PGX-OFF"))
    await promocode_repository.update(UpdatePromocodeDto(promocode_id=off.id, is_active=False))
    await promocode_repository.create(
        _create_dto("PGX-OLD", expires_at=datetime_now() - timedelta(days=1))
    )
    await promocode_repository.create(
        _create_dto("PGX-LIVE", reward_type=PromocodeRewardType.TRAFFIC)
    )

    async def codes(**filters: object) -> list[str]:
        items, _ = await promocode_repository.list_paginated(
            ListPromocodesDto(search="pgx-", **filters)  # type: ignore[arg-type]
        )
        return [item.code for item in items]

    assert (await codes())[0] == "PGX-LIVE"
    assert await codes(status=PromocodeStatus.ACTIVE) == ["PGX-LIVE"]
    assert await codes(status=PromocodeStatus.INACTIVE) == ["PGX-OFF"]
    assert await codes(status=PromocodeStatus.EXPIRED) == ["PGX-OLD"]
    assert await codes(reward_type=PromocodeRewardType.TRAFFIC) == ["PGX-LIVE"]

    page, total = await promocode_repository.list_paginated(
        ListPromocodesDto(search="PGX-", page=2, page_size=2)
    )
    assert total == 3
    assert len(page) == 1


async def test_update_partial_leaves_other_fields_untouched(
    promocode_repository: PromocodeRepository,
) -> None:
    created = await promocode_repository.create(_create_dto("PARTIAL", max_activations=5))

    updated = await promocode_repository.update(
        UpdatePromocodeDto(promocode_id=created.id, is_active=False)
    )

    assert updated.is_active is False
    assert updated.max_activations == 5  # untouched


async def test_delete_removes_promocode(promocode_repository: PromocodeRepository) -> None:
    created = await promocode_repository.create(_create_dto("GONE"))

    await promocode_repository.delete(created.id)

    assert await promocode_repository.find_by_code("GONE") is None


async def test_delete_unknown_raises_not_found(promocode_repository: PromocodeRepository) -> None:
    with pytest.raises(NotFoundError):
        await promocode_repository.delete(999_999)


async def test_update_allowed_availability(promocode_repository: PromocodeRepository) -> None:
    created = await promocode_repository.create(_create_dto("ALLOWLIST"))

    updated = await promocode_repository.update(
        UpdatePromocodeDto(
            promocode_id=created.id,
            availability=PromocodeAvailability.ALLOWED,
            allowed_user_ids=[7, 8],
        )
    )

    assert updated.availability == PromocodeAvailability.ALLOWED
    assert updated.allowed_user_ids == [7, 8]


async def test_get_activations_count(
    promocode_repository: PromocodeRepository,
    user_repository: UserRepository,
) -> None:
    promo = await promocode_repository.create(
        CreatePromocodeDto(
            code="COUNT1", reward_type=PromocodeRewardType.PERSONAL_DISCOUNT, reward=10
        )
    )
    user = await user_repository.create(CreateUserDto(name="counter"))
    assert await promocode_repository.get_activations_count(promo.id) == 0

    await promocode_repository.add_activation(
        promocode_id=promo.id, user_id=user.id, subscription_id=None
    )

    assert await promocode_repository.get_activations_count(promo.id) == 1


async def test_get_activation_by_user(
    promocode_repository: PromocodeRepository,
    user_repository: UserRepository,
) -> None:
    promo = await promocode_repository.create(
        CreatePromocodeDto(
            code="BYUSER1", reward_type=PromocodeRewardType.PERSONAL_DISCOUNT, reward=10
        )
    )
    user = await user_repository.create(CreateUserDto(name="by-user"))

    assert await promocode_repository.find_activation_by_user(promo.id, user.id) is None

    await promocode_repository.add_activation(
        promocode_id=promo.id, user_id=user.id, subscription_id=None
    )

    activation = await promocode_repository.find_activation_by_user(promo.id, user.id)
    assert activation is not None
    assert activation.user_id == user.id


async def test_list_activations_by_user_returns_only_that_users_codes(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    first = await promocode_repository.create(_create_dto("MINE1"))
    second = await promocode_repository.create(_create_dto("MINE2"))
    user_id = await _create_user(user_repository, 1101)
    other_id = await _create_user(user_repository, 1102)
    for promo in (first, second):
        await promocode_repository.add_activation(
            promocode_id=promo.id, user_id=user_id, subscription_id=None
        )
    await promocode_repository.add_activation(
        promocode_id=first.id, user_id=other_id, subscription_id=None
    )

    activations, total = await promocode_repository.list_activations_by_user(user_id)
    page, _ = await promocode_repository.list_activations_by_user(user_id, page=2, page_size=1)

    assert {a.code for a in activations} == {"MINE1", "MINE2"}
    assert total == 2
    assert len(page) == 1


async def test_sql_statuses_agree_with_the_liveness_rule(
    promocode_repository: PromocodeRepository,
    user_repository: UserRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # the list filters and the summary count repeat is_promocode_live in SQL
    now = datetime_now()
    monkeypatch.setattr(promocode_repository_module, "datetime_now", lambda: now)
    expiries = [None, now - timedelta(days=1), now, now + timedelta(days=1)]
    user_id = await _create_user(user_repository, 1301)
    created = []
    for index, expires_at in enumerate(expiries):
        for active in (True, False):
            for capped in (False, True):
                promo = await promocode_repository.create(
                    _create_dto(
                        f"PARITY{index}{int(active)}{int(capped)}",
                        expires_at=expires_at,
                        max_activations=1 if capped else None,
                    )
                )
                if capped:
                    await promocode_repository.add_activation(promo.id, user_id, None)
                if not active:
                    promo = await promocode_repository.update(
                        UpdatePromocodeDto(promocode_id=promo.id, is_active=False)
                    )
                created.append((promo, capped))

    async def codes(status: PromocodeStatus) -> set[str]:
        items, _ = await promocode_repository.list_paginated(
            ListPromocodesDto(search="parity", status=status, page_size=100)
        )
        return {item.code for item in items}

    live = {promo.code for promo, _ in created if is_promocode_live(promo, now)}
    redeemable = {promo.code for promo, capped in created if promo.code in live and not capped}
    total, active_count = await promocode_repository.count_total_and_active(now)

    assert live  # not vacuous
    assert await codes(PromocodeStatus.ACTIVE) | await codes(PromocodeStatus.EXHAUSTED) == live
    assert await codes(PromocodeStatus.ACTIVE) == redeemable
    assert active_count == len(redeemable)
    assert total == len(created)
