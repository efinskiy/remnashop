from datetime import datetime, timedelta
from typing import Final

from app.core.enums import SubscriptionStatus
from app.modules.settings import GraceSettingsDto
from app.modules.subscriptions.dto import SubscriptionDto

# a run that claimed and never finished (a crash, a panel that didn't answer): taken again
CLAIM_STALE_AFTER: Final[timedelta] = timedelta(minutes=10)


def lapsed_at(subscription: SubscriptionDto) -> datetime:
    """When access really ended: the grace end where grace followed the expiry."""
    if subscription.grace_ended_at is None:
        return subscription.expire_at
    return max(subscription.expire_at, subscription.grace_ended_at)


def handled(subscription: SubscriptionDto, now: datetime) -> bool:
    """The rule already acted on this expiry: switched it off, gave up on a panel refusal,
    or an admin turned it back on. A claim left half done long enough is taken again."""
    marked = subscription.expiry_disable_handled_at
    if marked is None or marked < lapsed_at(subscription):
        return False
    stale_claim = subscription.expiry_disabled_at is not None and marked < now - CLAIM_STALE_AFTER
    return not stale_claim


def disable_at(subscription: SubscriptionDto, settings: GraceSettingsDto) -> datetime:
    return lapsed_at(subscription) + timedelta(days=settings.expiry_disable_after_days)


def disable_due(subscription: SubscriptionDto, settings: GraceSettingsDto, now: datetime) -> bool:
    return (
        settings.expiry_disable_enabled
        and subscription.status is SubscriptionStatus.EXPIRED
        and subscription.grace_until is None
        and not handled(subscription, now)
        and disable_at(subscription, settings) <= now
    )


def warning_due(subscription: SubscriptionDto, settings: GraceSettingsDto, now: datetime) -> bool:
    """Only while the switch-off is still ahead: a subscription that lapsed long before the
    rule was switched on is switched off without one."""
    if not settings.expiry_disable_warn_days:
        return False
    switch_off = disable_at(subscription, settings)
    return (
        settings.expiry_disable_enabled
        and subscription.status is SubscriptionStatus.EXPIRED
        and subscription.grace_until is None
        and switch_off - timedelta(days=settings.expiry_disable_warn_days) <= now < switch_off
        and (
            subscription.expiry_disable_warned_at is None
            or subscription.expiry_disable_warned_at < lapsed_at(subscription)
        )
    )
