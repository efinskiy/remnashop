from app.core.actor import Actor
from app.core.db.uow import UnitOfWork
from app.core.security.permissions import Permission
from app.core.usecase import UseCase
from app.core.utils.time import range_end_utc, range_start_utc
from app.modules.advertising.dto import AdLinkPayoutDto, GetAdLinkPayoutDto
from app.modules.advertising.repository import AdLinkRepository
from app.modules.pricing import PricingRepository, convert_for_report
from app.modules.settings import SettingsRepository
from app.modules.transactions import TransactionRepository


class GetAdLinkPayoutUseCase(UseCase[GetAdLinkPayoutDto, AdLinkPayoutDto]):
    required_permission = Permission.AD_LINKS_PAYOUT_VIEW

    def __init__(
        self,
        ad_link_repository: AdLinkRepository,
        transaction_repository: TransactionRepository,
        pricing_repository: PricingRepository,
        uow: UnitOfWork,
        settings_repository: SettingsRepository,
    ) -> None:
        self._settings_repository = settings_repository
        self._ad_link_repository = ad_link_repository
        self._transaction_repository = transaction_repository
        self._pricing_repository = pricing_repository
        self._uow = uow

    async def _execute(self, actor: Actor, data: GetAdLinkPayoutDto) -> AdLinkPayoutDto:
        async with self._uow:
            # bare dates are the shop's days
            zone = (await self._settings_repository.get_shop_settings()).zone
            ad_link = await self._ad_link_repository.get_by_id(data.ad_link_id)
            user_ids = await self._ad_link_repository.list_attributed_user_ids(data.ad_link_id)
            (
                payments_count,
                revenue_anchor,
            ) = await self._transaction_repository.count_and_sum_paid_anchor_amount(
                user_ids,
                paid_from=range_start_utc(data.paid_from, zone),
                paid_to=range_end_utc(data.paid_to, zone),
            )
            rate_table = await self._pricing_repository.get_rate_table()

        report_currency = rate_table.anchor
        revenue = convert_for_report(revenue_anchor, rate_table.anchor, report_currency, rate_table)
        return AdLinkPayoutDto(
            report_currency=report_currency,
            payments_count=payments_count,
            revenue=revenue,
            revenue_share_percent=ad_link.revenue_share_percent,
            payout=ad_link.revenue_share(revenue),
        )
