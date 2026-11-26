from datetime import datetime
from typing import Optional

from sqlalchemy import ColumnElement, and_, case, func, not_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.errors import constraint_name
from app.core.db.filters import in_ids, visible_rows
from app.core.db.models.promocode import Promocode, PromocodeActivation
from app.core.db.partial_update import apply_partial_update
from app.core.enums import PromocodeRewardType, PromocodeStatus
from app.core.error_codes import ErrorCode
from app.core.exceptions import ConflictError, NotFoundError
from app.core.utils.time import datetime_now
from app.modules.promocodes.dto import (
    CreatePromocodeDto,
    ListPromocodesDto,
    PromocodeActivationDto,
    PromocodeDto,
    PromocodeRewardTotalsDto,
    UpdatePromocodeDto,
    UserPromocodeActivationDto,
)


def _exhausted() -> ColumnElement[bool]:
    # the activation cap is used up; a cap lowered below the count counts too
    used = (
        select(func.count())
        .select_from(PromocodeActivation)
        .where(PromocodeActivation.promocode_id == Promocode.id)
        .correlate(Promocode)
        .scalar_subquery()
    )
    return and_(Promocode.max_activations.is_not(None), used >= Promocode.max_activations)


class PromocodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_dto(self, row: Promocode) -> PromocodeDto:
        return PromocodeDto(
            id=row.id,
            code=row.code,
            is_active=row.is_active,
            reward_type=row.reward_type,
            reward=row.reward,
            reward_addon_id=row.reward_addon_id,
            reward_plan_id=row.reward_plan_id,
            reward_duration_days=row.reward_duration_days,
            availability=row.availability,
            allowed_user_ids=list(row.allowed_user_ids or []),
            prior_customers_only=row.prior_customers_only,
            allowed_plan_ids=list(row.allowed_plan_ids or []),
            expires_at=row.expires_at,
            max_activations=row.max_activations,
            is_reusable=row.is_reusable,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_activation_dto(self, row: PromocodeActivation) -> PromocodeActivationDto:
        return PromocodeActivationDto.model_validate(row, from_attributes=True)

    async def _get_or_raise(self, promocode_id: int) -> Promocode:
        row = await self.session.get(Promocode, promocode_id)
        if row is None:
            raise NotFoundError(
                f"Promocode '{promocode_id}' not found", code=ErrorCode.PROMOCODE_NOT_FOUND
            )
        return row

    async def get_by_id(self, promocode_id: int) -> PromocodeDto:
        return self._to_dto(await self._get_or_raise(promocode_id))

    async def find_by_id(self, promocode_id: int) -> Optional[PromocodeDto]:
        row = await self.session.get(Promocode, promocode_id)
        return self._to_dto(row) if row is not None else None

    async def find_by_code(self, code: str) -> Optional[PromocodeDto]:
        row = await self.session.scalar(select(Promocode).where(Promocode.code == code))
        return self._to_dto(row) if row is not None else None

    async def list_all(self) -> list[PromocodeDto]:
        result = await self.session.execute(select(Promocode).order_by(Promocode.id))
        return [self._to_dto(row) for row in result.scalars()]

    async def count_total_and_active(self, now: datetime) -> tuple[int, int]:
        active = and_(
            Promocode.is_active.is_(True),
            # usable through the expiry instant itself, as rules.is_promocode_live
            or_(Promocode.expires_at.is_(None), Promocode.expires_at >= now),
            not_(_exhausted()),
        )
        total, active_count = (
            await self.session.execute(select(func.count(), func.count().filter(active)))
        ).one()
        return int(total), int(active_count)

    async def list_activations(
        self, start: Optional[datetime], end: datetime
    ) -> list[tuple[int, int, datetime]]:
        stmt = select(
            PromocodeActivation.promocode_id,
            PromocodeActivation.user_id,
            PromocodeActivation.activated_at,
        ).where(PromocodeActivation.activated_at < end)
        if start is not None:
            stmt = stmt.where(PromocodeActivation.activated_at >= start)
        return list((await self.session.execute(stmt)).tuples().all())

    async def list_paginated(self, data: ListPromocodesDto) -> tuple[list[PromocodeDto], int]:
        expired = and_(Promocode.expires_at.is_not(None), Promocode.expires_at < datetime_now())
        live = and_(not_(expired), Promocode.is_active)
        redeemable = and_(live, not_(_exhausted()))
        conditions: list[ColumnElement[bool]] = []
        if data.status is PromocodeStatus.ACTIVE:
            conditions.append(redeemable)
        elif data.status is PromocodeStatus.EXHAUSTED:
            conditions.append(and_(live, _exhausted()))
        elif data.status is PromocodeStatus.EXPIRED:
            conditions.append(expired)
        elif data.status is PromocodeStatus.INACTIVE:
            conditions.append(and_(not_(expired), Promocode.is_active.is_(False)))
        if data.reward_type is not None:
            conditions.append(Promocode.reward_type == data.reward_type)
        if data.search:
            conditions.append(Promocode.code.icontains(data.search, autoescape=True))

        total = await self.session.scalar(
            select(func.count()).select_from(Promocode).where(*conditions)
        )
        rows = await self.session.scalars(
            select(Promocode)
            .where(*conditions)
            .order_by(
                case((redeemable, 0), else_=1), Promocode.created_at.desc(), Promocode.id.desc()
            )
            .offset((data.page - 1) * data.page_size)
            .limit(data.page_size)
        )
        return [self._to_dto(row) for row in rows], total or 0

    async def create(self, data: CreatePromocodeDto) -> PromocodeDto:
        row = Promocode(
            code=data.code,
            is_active=True,
            reward_type=data.reward_type,
            reward=data.reward,
            reward_addon_id=data.reward_addon_id,
            reward_plan_id=data.reward_plan_id,
            reward_duration_days=data.reward_duration_days,
            availability=data.availability,
            allowed_user_ids=data.allowed_user_ids,
            prior_customers_only=data.prior_customers_only,
            allowed_plan_ids=data.allowed_plan_ids,
            expires_at=data.expires_at,
            max_activations=data.max_activations,
            is_reusable=data.is_reusable,
        )
        self.session.add(row)

        try:
            await self.session.flush()
        except IntegrityError as error:
            constraint = constraint_name(error)
            if constraint == "ix_promocodes_code":
                raise ConflictError(
                    f"Promocode with code '{data.code}' already exists",
                    code=ErrorCode.PROMOCODE_CODE_TAKEN,
                ) from error
            raise

        await self.session.refresh(row)
        return self._to_dto(row)

    async def update(self, data: UpdatePromocodeDto) -> PromocodeDto:
        row = await self._get_or_raise(data.promocode_id)

        apply_partial_update(row, data, skip=frozenset({"promocode_id", "cleared", "client_ip"}))
        for name in data.cleared:
            setattr(row, name, None)

        await self.session.flush()
        await self.session.refresh(row)
        return self._to_dto(row)

    async def lock_limited_to_plan(self, plan_id: int) -> list[int]:
        """Active promocodes valid for this plan and no other one."""
        ids = await self.session.scalars(
            select(Promocode.id)
            .where(
                Promocode.allowed_plan_ids.contained_by([plan_id]),
                Promocode.allowed_plan_ids != [],
                Promocode.is_active.is_(True),
            )
            .order_by(Promocode.id)
            .with_for_update()
        )
        return list(ids)

    async def deactivate(self, promocode_ids: list[int]) -> None:
        await self.session.execute(
            update(Promocode).where(in_ids(Promocode.id, promocode_ids)).values(is_active=False)
        )

    async def remove_plan_from_allowlists(self, plan_id: int) -> None:
        await self.session.execute(
            update(Promocode)
            .where(Promocode.allowed_plan_ids.contains([plan_id]))
            .values(allowed_plan_ids=func.array_remove(Promocode.allowed_plan_ids, plan_id))
        )
        await self.session.flush()

    async def list_expiring(self, now: datetime, until: datetime) -> list[PromocodeDto]:
        rows = await self.session.scalars(
            select(Promocode).where(
                Promocode.is_active.is_(True),
                Promocode.expires_at >= now,
                Promocode.expires_at < until,
            )
        )
        return [self._to_dto(row) for row in rows]

    async def delete(self, promocode_id: int) -> None:
        row = await self._get_or_raise(promocode_id)
        await self.session.delete(row)
        await self.session.flush()

    async def get_by_id_for_update(self, promocode_id: int) -> PromocodeDto:
        # concurrent activations of one code serialize on this lock
        result = await self.session.execute(
            select(Promocode)
            .where(Promocode.id == promocode_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundError(
                f"Promocode '{promocode_id}' not found", code=ErrorCode.PROMOCODE_NOT_FOUND
            )
        return self._to_dto(row)

    async def add_activation(
        self, promocode_id: int, user_id: int, subscription_id: Optional[int]
    ) -> PromocodeActivationDto:
        row = PromocodeActivation(
            promocode_id=promocode_id, user_id=user_id, subscription_id=subscription_id
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._to_activation_dto(row)

    async def get_activations_count(self, promocode_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(PromocodeActivation)
            .where(PromocodeActivation.promocode_id == promocode_id)
        )
        return result.scalar_one()

    async def count_activations_by_promocode(
        self, promocode_ids: Optional[list[int]] = None
    ) -> dict[int, int]:
        stmt = select(PromocodeActivation.promocode_id, func.count()).group_by(
            PromocodeActivation.promocode_id
        )
        if promocode_ids is not None:
            stmt = stmt.where(in_ids(PromocodeActivation.promocode_id, promocode_ids))
        return dict((await self.session.execute(stmt)).tuples().all())

    async def with_activations_count(self, promocodes: list[PromocodeDto]) -> list[PromocodeDto]:
        counts = await self.count_activations_by_promocode([p.id for p in promocodes])
        return [p.model_copy(update={"activations_count": counts.get(p.id, 0)}) for p in promocodes]

    async def count_activations(self) -> tuple[int, int]:
        # (activations, distinct users)
        stmt = select(func.count(), func.count(func.distinct(PromocodeActivation.user_id)))
        activations, users = (await self.session.execute(stmt)).tuples().one()
        return activations, users

    async def reward_totals_by_type(self) -> dict[PromocodeRewardType, PromocodeRewardTotalsDto]:
        stmt = (
            select(
                Promocode.reward_type,
                func.count(),
                func.sum(Promocode.reward),
                func.sum(Promocode.reward_duration_days),
            )
            .select_from(PromocodeActivation)
            .join(Promocode, Promocode.id == PromocodeActivation.promocode_id)
            .group_by(Promocode.reward_type)
        )
        return {
            reward_type: PromocodeRewardTotalsDto(
                count=count, reward_sum=reward_sum or 0, duration_days_sum=duration_days_sum or 0
            )
            for reward_type, count, reward_sum, duration_days_sum in (
                await self.session.execute(stmt)
            ).tuples()
        }

    async def list_activations_paginated(
        self,
        promocode_id: int,
        *,
        page: int = 1,
        page_size: int = 50,
        hide_staff_from: Optional[int] = None,
    ) -> tuple[list[PromocodeActivationDto], int]:
        condition = PromocodeActivation.promocode_id == promocode_id
        if hide_staff_from is not None:
            condition = and_(
                condition,
                visible_rows(PromocodeActivation.user_id, hide_staff_from),
            )
        total = await self.session.scalar(
            select(func.count()).select_from(PromocodeActivation).where(condition)
        )
        rows = await self.session.scalars(
            select(PromocodeActivation)
            .where(condition)
            .order_by(PromocodeActivation.activated_at.desc(), PromocodeActivation.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [self._to_activation_dto(row) for row in rows], total or 0

    async def find_activation_by_user(
        self, promocode_id: int, user_id: int
    ) -> Optional[PromocodeActivationDto]:
        result = await self.session.execute(
            select(PromocodeActivation)
            .where(
                PromocodeActivation.promocode_id == promocode_id,
                PromocodeActivation.user_id == user_id,
            )
            .order_by(PromocodeActivation.activated_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return self._to_activation_dto(row) if row is not None else None

    async def list_activations_by_user(
        self, user_id: int, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[UserPromocodeActivationDto], int]:
        condition = PromocodeActivation.user_id == user_id
        total = await self.session.scalar(
            select(func.count()).select_from(PromocodeActivation).where(condition)
        )
        rows = await self.session.execute(
            select(PromocodeActivation, Promocode)
            .join(Promocode, Promocode.id == PromocodeActivation.promocode_id)
            .where(condition)
            .order_by(PromocodeActivation.activated_at.desc(), PromocodeActivation.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [
            UserPromocodeActivationDto(
                activation_id=activation.id,
                promocode_id=promo.id,
                code=promo.code,
                reward_type=promo.reward_type,
                reward=promo.reward,
                reward_duration_days=promo.reward_duration_days,
                activated_at=activation.activated_at,
            )
            for activation, promo in rows.tuples()
        ], total or 0
