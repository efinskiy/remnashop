from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.core.dto import ResponseModel
from app.core.enums import Currency, PaymentGatewayType, PromocodeRewardType
from app.modules.analytics.aggregates import RevenueGranularity
from app.modules.analytics.sources import SourceKind
from app.modules.promocodes import PromocodeStatus


class AnalyticsPeriodInfoResponse(ResponseModel):
    start: datetime
    end: datetime
    previous_start: datetime
    previous_end: datetime


class PeriodKpiResponse(ResponseModel):
    revenue: Decimal
    payments: int
    paying_users: int
    arppu: Decimal
    new_payers: int
    conversion_cohort: int
    converted: int
    conversion_rate: float
    churn_base: int
    churned: int
    churn_rate: float


class SnapshotKpiResponse(ResponseModel):
    mrr: Decimal
    paid_subscriptions: int
    limited_subscriptions: int
    active_trials: int
    paying_customers: int
    never_connected: int
    expiring_soon_days: int
    expiring_soon: int
    expiring_soon_mrr: Decimal
    trials_ending_days: int
    trials_ending_soon: int
    points_owed: Decimal
    bonus_days_owed: int


class AnalyticsResponse(ResponseModel):
    period: AnalyticsPeriodInfoResponse
    report_currency: Currency
    revenue_by_currency: dict[Currency, Decimal]
    conversion_window_days: int
    current: PeriodKpiResponse
    previous: PeriodKpiResponse
    snapshot: SnapshotKpiResponse


class FunnelStepResponse(ResponseModel):
    key: str
    count: int
    pct_of_start: float
    pct_of_prev: float


class FunnelSourceRowResponse(ResponseModel):
    source: SourceKind
    ad_link_id: Optional[int]
    name: Optional[str]
    registered: int
    connected: int
    paid: int
    repeat_paid: int


class FunnelResponse(ResponseModel):
    period: AnalyticsPeriodInfoResponse
    steps: list[FunnelStepResponse]
    paid_via_trial: int
    previous_conversion: Optional[float]
    by_source: list[FunnelSourceRowResponse]


class CohortRowResponse(ResponseModel):
    cohort: str
    cohort_size: int
    retention_by_month: list[float]


class CohortsResponse(ResponseModel):
    items: list[CohortRowResponse]
    total: int


class LtvBucketResponse(ResponseModel):
    label: str
    lower_bound: Decimal
    upper_bound: Optional[Decimal]
    users: int


class LtvDistributionResponse(ResponseModel):
    report_currency: Currency
    buckets: list[LtvBucketResponse]
    payers: int
    mean: Decimal
    median: Decimal


class LtvGroupResponse(ResponseModel):
    key: str
    source: Optional[SourceKind]
    customers: int
    avg_ltv: Decimal


class TopPayerResponse(ResponseModel):
    user_id: int
    name: str
    username: Optional[str]
    current_plans: list[str]
    payments: int
    spent: Decimal
    last_paid_at: datetime


class LtvBreakdownResponse(ResponseModel):
    report_currency: Currency
    by_first_plan: list[LtvGroupResponse]
    by_source: list[LtvGroupResponse]
    top_payers: list[TopPayerResponse]


class RevenueTotalsResponse(ResponseModel):
    revenue: Decimal
    payments: int
    avg_check: Decimal
    median_check: Decimal
    refunds: int
    refunded: Decimal
    previous_revenue: Decimal
    previous_payments: int
    previous_refunds: int


class RevenueBucketResponse(ResponseModel):
    start: datetime
    new: Decimal
    renew: Decimal
    change: Decimal
    previous_total: Decimal


class RevenueGroupResponse(ResponseModel):
    key: str
    payments: int
    revenue: Decimal


class GatewayStatsResponse(ResponseModel):
    gateway_type: PaymentGatewayType
    paid: int
    canceled: int
    failed: int
    refunded: int
    revenue: Decimal


class RevenueResponse(ResponseModel):
    period: AnalyticsPeriodInfoResponse
    report_currency: Currency
    granularity: RevenueGranularity
    totals: RevenueTotalsResponse
    series: list[RevenueBucketResponse]
    by_plan: list[RevenueGroupResponse]
    by_duration: list[RevenueGroupResponse]
    by_channel: list[RevenueGroupResponse]
    gateways: list[GatewayStatsResponse]


class TrialDayBucketResponse(ResponseModel):
    key: str
    count: int


class TimeToPayBucketResponse(ResponseModel):
    key: str
    via_trial: int
    direct: int


class TrialStatsResponse(ResponseModel):
    period: AnalyticsPeriodInfoResponse
    report_currency: Currency
    trials: int
    converted: int
    conversion_rate: float
    previous_conversion_rate: Optional[float]
    previous_trials: int
    revenue_from_converted: Decimal
    previous_revenue_from_converted: Decimal
    median_days_to_pay: int
    trial_days: int
    by_trial_day: list[TrialDayBucketResponse]
    time_to_first_payment: list[TimeToPayBucketResponse]
    plans_after_trial: list[RevenueGroupResponse]


class RetentionPointResponse(ResponseModel):
    months: int
    rate: float
    eligible: int


class ExpiringWeekResponse(ResponseModel):
    key: str
    count: int
    mrr_at_risk: Decimal


class ExpiringCustomerResponse(ResponseModel):
    user_id: int
    name: str
    username: Optional[str]
    plan_names: list[str]
    expire_at: datetime
    spent: Decimal
    renewals: int


class ExpiringCustomerPageResponse(ResponseModel):
    items: list[ExpiringCustomerResponse]
    total: int


class PlanActiveResponse(ResponseModel):
    plan_name: str
    active: int
    limited: int


class MonthlyChurnResponse(ResponseModel):
    month: str
    base: int
    churned: int
    rate: float


class RetentionResponse(ResponseModel):
    report_currency: Currency
    points: list[RetentionPointResponse]
    avg_paid_months: float
    expiring_paid: int
    expiring_trials: int
    expiring_weeks: list[ExpiringWeekResponse]
    active_by_plan: list[PlanActiveResponse]
    monthly_churn: list[MonthlyChurnResponse]


class SourceRowResponse(ResponseModel):
    source: SourceKind
    ad_link_id: Optional[int]
    name: Optional[str]
    registrations: int
    payers: int
    conversion_rate: float
    revenue: Decimal
    revenue_per_payer: Decimal


class ReferralPaybackResponse(ResponseModel):
    referred_revenue: Decimal
    reward_days: int
    reward_points: int
    referrers: int
    deep_levels_revenue_share: float


class TopReferrerResponse(ResponseModel):
    user_id: int
    name: str
    invited: int
    paid: int
    revenue: Decimal
    reward_days: int


class ChannelRevenueResponse(ResponseModel):
    source: SourceKind
    revenue: Decimal


class SourcesResponse(ResponseModel):
    period: AnalyticsPeriodInfoResponse
    report_currency: Currency
    channels: list[SourceRowResponse]
    previous_channels: list[ChannelRevenueResponse]
    ad_links: list[SourceRowResponse]
    referral: ReferralPaybackResponse
    top_referrers: list[TopReferrerResponse]


class RewardTypeCountResponse(ResponseModel):
    reward_type: PromocodeRewardType
    activations: int


class PromocodeRowResponse(ResponseModel):
    promocode_id: int
    code: str
    reward_type: PromocodeRewardType
    reward: Optional[int]
    reward_duration_days: Optional[int]
    activations: int
    total_activations: int
    max_activations: Optional[int]
    revenue_after: Decimal
    conversion_rate: Optional[float]
    status: PromocodeStatus


class PromocodeStatsResponse(ResponseModel):
    period: AnalyticsPeriodInfoResponse
    report_currency: Currency
    activations: int
    codes_used: int
    discount_given: Decimal
    revenue_with_discount: Decimal
    revenue_share: float
    free_rewards: int
    free_reward_conversion: float
    previous_activations: int
    previous_discount_given: Decimal
    previous_revenue_with_discount: Decimal
    previous_free_reward_conversion: Optional[float]
    by_reward_type: list[RewardTypeCountResponse]
    codes: list[PromocodeRowResponse]
