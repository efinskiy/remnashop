from datetime import datetime, timedelta

from app.core.enums import SubscriptionStatus
from app.modules.settings import GraceSettingsDto
from app.modules.subscriptions.dto import SubscriptionDto


def lapsed_at(subscription: SubscriptionDto) -> datetime:
    """When access really ended: the grace end where grace followed the expiry."""
    if subscription.grace_ended_at is None:
        return subscription.expire_at
    return max(subscription.expire_at, subscription.grace_ended_at)


def disable_at(subscription: SubscriptionDto, settings: GraceSettingsDto) -> datetime:
    return lapsed_at(subscription) + timedelta(days=settings.expiry_disable_after_days)


def disable_due(subscription: SubscriptionDto, settings: GraceSettingsDto, now: datetime) -> bool:
    return (
        settings.expiry_disable_enabled
        and subscription.status is SubscriptionStatus.EXPIRED
        and subscription.grace_until is None
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
