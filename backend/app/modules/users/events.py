from dataclasses import dataclass, field
from typing import ClassVar, Literal, Optional

from app.core.events import ActorEvent, ActorTargetEvent, EventCategory, SystemEvent, UserEvent
from app.modules.users.dto import CabinetSignInMethod


@dataclass(frozen=True, kw_only=True)
class TelegramUserRegisteredEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    # passed through: advertising and referrals resolve these in their subscribers
    ad_link_code: Optional[str] = None
    referral_code: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class CabinetUserRegisteredEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    method: CabinetSignInMethod
    ad_link_code: Optional[str] = None
    referral_code: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class AdminChangedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.ADMIN_MANAGEMENT
    action: Literal["create", "delete", "demote", "permissions", "promote"]
    # set on "permissions"
    permission_grants: Optional[list[str]] = None
    permission_revokes: Optional[list[str]] = None


@dataclass(frozen=True, kw_only=True)
class UserDeletedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER


@dataclass(frozen=True, kw_only=True)
class TelegramIdChangedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    action: Literal["link", "unlink"]
    previous_telegram_id: Optional[int] = None


@dataclass(frozen=True, kw_only=True)
class UserBlockChangedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    action: Literal["block", "unblock"]


@dataclass(frozen=True, kw_only=True)
class UserEmailUndeliverableClearedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER


@dataclass(frozen=True, kw_only=True)
class UserBotMenuResetEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER


@dataclass(frozen=True, kw_only=True)
class UserTrialAvailabilityChangedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    is_trial_available: bool


@dataclass(frozen=True, kw_only=True)
class TelegramRegistrationBlockedEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.USER


@dataclass(frozen=True, kw_only=True)
class CabinetRegistrationBlockedEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.USER


@dataclass(frozen=True, kw_only=True)
class UsersBulkUnblockedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    count: int


@dataclass(frozen=True, kw_only=True)
class UserPersonalDiscountChangedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    old_percent: int
    new_percent: int


@dataclass(frozen=True, kw_only=True)
class UserMarkupChangedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    old_percent: int
    new_percent: int


@dataclass(frozen=True, kw_only=True)
class UserPurchaseDiscountChangedEvent(ActorTargetEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    old_percent: int
    new_percent: int


@dataclass(frozen=True, kw_only=True)
class PasswordChangedEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH


@dataclass(frozen=True, kw_only=True)
class SecuritySettingsChangedEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH
    changed_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class BotBlockedByUserEvent(SystemEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    user_id: int


@dataclass(frozen=True, kw_only=True)
class MarketingOptOutChangedEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    opted_out: bool
    source: Literal["account", "link"]
