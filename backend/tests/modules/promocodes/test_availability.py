import asyncio
from datetime import timedelta
from typing import Final

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

import app.modules.promocodes.availability as availability_module
from app.core.db.models.promocode import Promocode
from app.core.enums import PromocodeRewardType
from app.core.exceptions import NotFoundError, ValidationError
from app.core.utils.time import datetime_now
from app.modules.promocodes.availability import PromocodeLivenessCheck, claim_activation
from app.modules.promocodes.dto import CreatePromocodeDto, UpdatePromocodeDto
from app.modules.promocodes.repository import PromocodeRepository
from app.modules.users.dto import CreateUserDto
from app.modules.users.repository import UserRepository

# far longer than a round trip, so both sides of the race test overlap there
_RACE_WINDOW_DELAY_SECONDS: Final[float] = 0.05


def _create_dto(code: str = "WELCOME10", **overrides: object) -> CreatePromocodeDto:
    defaults: dict = {"code": code, "reward_type": PromocodeRewardType.DURATION, "reward": 30}
    defaults.update(overrides)
    return CreatePromocodeDto(**defaults)


async def _create_user(user_repository: UserRepository, telegram_id: int) -> int:
    user = await user_repository.create(CreateUserDto(name="buyer", telegram_id=telegram_id))
    return user.id


async def test_claim_activation_records_activation(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    created = await promocode_repository.create(_create_dto("CLAIM"))
    user_id = await _create_user(user_repository, 1001)

    activation = await claim_activation(
        promocode_repository, promocode_id=created.id, user_id=user_id, subscription_id=None
    )

    assert activation.promocode_id == created.id
    assert activation.user_id == user_id


async def test_claim_activation_second_time_by_same_user_raises_when_not_reusable(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    created = await promocode_repository.create(_create_dto("ONCE", is_reusable=False))
    user_id = await _create_user(user_repository, 1002)
    await claim_activation(
        promocode_repository, promocode_id=created.id, user_id=user_id, subscription_id=None
    )

    with pytest.raises(ValidationError):
        await claim_activation(
            promocode_repository, promocode_id=created.id, user_id=user_id, subscription_id=None
        )


async def test_claim_activation_second_time_by_same_user_allowed_when_reusable(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    created = await promocode_repository.create(_create_dto("REUSE", is_reusable=True))
    user_id = await _create_user(user_repository, 1003)
    await claim_activation(
        promocode_repository, promocode_id=created.id, user_id=user_id, subscription_id=None
    )

    second = await claim_activation(
        promocode_repository, promocode_id=created.id, user_id=user_id, subscription_id=None
    )
    assert second.user_id == user_id


async def test_claim_activation_raises_once_max_activations_reached(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    created = await promocode_repository.create(_create_dto("CAPPED", max_activations=1))
    first_user_id = await _create_user(user_repository, 1004)
    second_user_id = await _create_user(user_repository, 1005)
    await claim_activation(
        promocode_repository, promocode_id=created.id, user_id=first_user_id, subscription_id=None
    )

    with pytest.raises(ValidationError):
        await claim_activation(
            promocode_repository,
            promocode_id=created.id,
            user_id=second_user_id,
            subscription_id=None,
        )


def _widen_locking_select_race_window(session: AsyncSession) -> None:
    # Pauses between claim_activation's locking SELECT and the max_activations
    # count. On a local Postgres one side otherwise finishes before the other
    # starts and the race never happens. With the lock, the loser blocks in
    # its SELECT, so the pause only widens an unlocked race.
    original_execute = session.execute

    async def _delayed_execute(statement: object, *args: object, **kwargs: object) -> object:
        result = await original_execute(statement, *args, **kwargs)
        sql = str(statement).lower()
        if "from promocodes" in sql and "count(" not in sql:
            await asyncio.sleep(_RACE_WINDOW_DELAY_SECONDS)
        return result

    session.execute = _delayed_execute  # type: ignore[assignment]


async def test_claim_activation_concurrent_calls_against_cap_only_one_succeeds(
    engine: AsyncEngine,
) -> None:
    # two real connections (`session` is a single one); both commit, so the
    # cleanup is a try/finally
    session_a = AsyncSession(bind=engine, expire_on_commit=False)
    session_b = AsyncSession(bind=engine, expire_on_commit=False)
    promocode_id = None
    first_user_id = None
    second_user_id = None
    try:
        created = await PromocodeRepository(session_a).create(
            _create_dto("RACE1", max_activations=1)
        )
        promocode_id = created.id
        first_user_id = await _create_user(UserRepository(session_a), 9101)
        second_user_id = await _create_user(UserRepository(session_a), 9102)
        await session_a.commit()

        # warm both connections with claim_activation's query: a cold first
        # query is slow enough to hide the race too
        locking_select = select(Promocode).where(Promocode.id == promocode_id)
        await session_a.execute(locking_select)
        await session_b.execute(locking_select)
        _widen_locking_select_race_window(session_a)
        _widen_locking_select_race_window(session_b)

        async def _claim(session: AsyncSession, user_id: int) -> object:
            # ends its transaction here, not after gather: the loser's FOR UPDATE
            # waits for the winner's transaction to end
            repo = PromocodeRepository(session)
            try:
                result = await claim_activation(
                    repo, promocode_id=promocode_id, user_id=user_id, subscription_id=None
                )
            except Exception:
                await session.rollback()
                raise
            await session.commit()
            return result

        results = await asyncio.gather(
            _claim(session_a, first_user_id),
            _claim(session_b, second_user_id),
            return_exceptions=True,
        )

        successes = [result for result in results if not isinstance(result, BaseException)]
        failures = [result for result in results if isinstance(result, BaseException)]
        assert len(successes) == 1
        assert len(failures) == 1
        assert isinstance(failures[0], ValidationError)
    finally:
        await session_a.close()
        await session_b.close()
        async with engine.begin() as connection:
            if promocode_id is not None:
                await connection.execute(
                    text("DELETE FROM promocode_activations WHERE promocode_id = :id"),
                    {"id": promocode_id},
                )
                await connection.execute(
                    text("DELETE FROM promocodes WHERE id = :id"), {"id": promocode_id}
                )
            for user_id in (first_user_id, second_user_id):
                if user_id is not None:
                    await connection.execute(
                        text("DELETE FROM users WHERE id = :id"), {"id": user_id}
                    )


async def test_claim_activation_refuses_a_repeat_after_reusable_was_turned_off(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    promo = await promocode_repository.create(
        CreatePromocodeDto(
            code="WASREUSABLE",
            reward_type=PromocodeRewardType.PERSONAL_DISCOUNT,
            reward=10,
            is_reusable=True,
        )
    )
    user_id = await _create_user(user_repository, 1099)
    await claim_activation(
        promocode_repository, promocode_id=promo.id, user_id=user_id, subscription_id=None
    )
    await claim_activation(
        promocode_repository, promocode_id=promo.id, user_id=user_id, subscription_id=None
    )
    await promocode_repository.update(UpdatePromocodeDto(promocode_id=promo.id, is_reusable=False))

    # two activations on record: a scalar_one() lookup would raise
    # MultipleResultsFound instead of refusing the claim
    with pytest.raises(ValidationError):
        await claim_activation(
            promocode_repository, promocode_id=promo.id, user_id=user_id, subscription_id=None
        )

    assert await promocode_repository.find_activation_by_user(promo.id, user_id) is not None


async def test_is_live_follows_activity_and_expiry(
    promocode_repository: PromocodeRepository,
) -> None:
    fresh = await promocode_repository.create(
        CreatePromocodeDto(
            code="LIVE1", reward_type=PromocodeRewardType.PURCHASE_DISCOUNT, reward=5
        )
    )
    off = await promocode_repository.create(
        CreatePromocodeDto(code="OFF1", reward_type=PromocodeRewardType.PURCHASE_DISCOUNT, reward=5)
    )
    await promocode_repository.update(UpdatePromocodeDto(promocode_id=off.id, is_active=False))
    lapsed = await promocode_repository.create(
        CreatePromocodeDto(
            code="LAPSED1",
            reward_type=PromocodeRewardType.PURCHASE_DISCOUNT,
            reward=5,
            expires_at=datetime_now() - timedelta(days=1),
        )
    )

    assert await PromocodeLivenessCheck(promocode_repository).is_live(fresh.id) is True
    assert await PromocodeLivenessCheck(promocode_repository).is_live(off.id) is False
    assert await PromocodeLivenessCheck(promocode_repository).is_live(lapsed.id) is False
    assert await PromocodeLivenessCheck(promocode_repository).is_live(999_999_999) is False


async def test_is_live_at_the_exact_expiry_instant(
    promocode_repository: PromocodeRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    edge = datetime_now() + timedelta(days=1)
    promo = await promocode_repository.create(
        CreatePromocodeDto(
            code="EDGE1",
            reward_type=PromocodeRewardType.PURCHASE_DISCOUNT,
            reward=5,
            expires_at=edge,
        )
    )
    monkeypatch.setattr(availability_module, "datetime_now", lambda: edge)

    assert await PromocodeLivenessCheck(promocode_repository).is_live(promo.id) is True


async def test_claim_refuses_a_code_deactivated_after_it_was_read(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    created = await promocode_repository.create(_create_dto("LEAKED"))
    user_id = await _create_user(user_repository, 1003)
    # the admin switches it off between the activation's first read and its claim
    await promocode_repository.update(UpdatePromocodeDto(promocode_id=created.id, is_active=False))

    with pytest.raises(NotFoundError):
        await claim_activation(
            promocode_repository, promocode_id=created.id, user_id=user_id, subscription_id=None
        )


async def test_claim_refuses_a_code_expired_after_it_was_read(
    promocode_repository: PromocodeRepository, user_repository: UserRepository
) -> None:
    created = await promocode_repository.create(
        _create_dto("LASTSEC", expires_at=datetime_now() - timedelta(seconds=1))
    )
    user_id = await _create_user(user_repository, 1004)

    with pytest.raises(ValidationError):
        await claim_activation(
            promocode_repository, promocode_id=created.id, user_id=user_id, subscription_id=None
        )
