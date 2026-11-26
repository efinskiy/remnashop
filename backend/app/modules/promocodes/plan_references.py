from app.modules.promocodes.repository import PromocodeRepository


class PromocodePlanReferences:
    """Drops a deleted plan from every promocode's plan list."""

    def __init__(self, promocode_repository: PromocodeRepository) -> None:
        self._promocode_repository = promocode_repository

    async def forget_plan(self, plan_id: int) -> list[int]:
        # a list left empty would open the promocode to every plan, so it is switched off instead
        disabled = await self._promocode_repository.lock_limited_to_plan(plan_id)
        if disabled:
            await self._promocode_repository.deactivate(disabled)
        await self._promocode_repository.remove_plan_from_allowlists(plan_id)
        return disabled
