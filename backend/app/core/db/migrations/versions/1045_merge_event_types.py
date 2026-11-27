from typing import Final, Optional, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1045"
down_revision: Union[str, None] = "1044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES: Final[tuple[str, ...]] = ("event_log_entries", "event_outbox")

# old type -> (new type, action added to the payload)
_RENAMES: Final[dict[str, tuple[str, Optional[str]]]] = {
    "BroadcastScheduledEvent": ("BroadcastChangedEvent", "schedule"),
    "BroadcastCanceledEvent": ("BroadcastChangedEvent", "cancel"),
    "BroadcastRecalledEvent": ("BroadcastChangedEvent", "recall"),
    "LocaleActivatedEvent": ("LocaleChangedEvent", "activate"),
    "LocaleDeactivatedEvent": ("LocaleChangedEvent", "deactivate"),
    "DefaultLocaleChangedEvent": ("LocaleChangedEvent", "set_default"),
    "BlacklistEntryAddedEvent": ("BlacklistEntryChangedEvent", "create"),
    "BlacklistEntryRemovedEvent": ("BlacklistEntryChangedEvent", "delete"),
    "AdminCreatedEvent": ("AdminChangedEvent", "create"),
    "AdminPromotedEvent": ("AdminChangedEvent", "promote"),
    "AdminDemotedEvent": ("AdminChangedEvent", "demote"),
    "AdminDeletedEvent": ("AdminChangedEvent", "delete"),
    "AdminPermissionsUpdatedEvent": ("AdminChangedEvent", "permissions"),
    "UserBlockedEvent": ("UserBlockChangedEvent", "block"),
    "UserUnblockedEvent": ("UserBlockChangedEvent", "unblock"),
    "PasskeyRegisteredEvent": ("PasskeyChangedEvent", "create"),
    "PasskeyRemovedEvent": ("PasskeyChangedEvent", "delete"),
    "PasskeyRenamedEvent": ("PasskeyChangedEvent", "rename"),
    "ApiTokenCreatedEvent": ("ApiTokenChangedEvent", "create"),
    "ApiTokenRevokedEvent": ("ApiTokenChangedEvent", "delete"),
    "TelegramIdBoundEvent": ("TelegramIdChangedEvent", "link"),
    "TelegramIdUnboundEvent": ("TelegramIdChangedEvent", "unlink"),
    "OAuthIdentityConnectedEvent": ("OAuthIdentityLinkedEvent", None),
    "OAuthIdentityDisconnectedEvent": ("OAuthIdentityUnlinkedEvent", None),
}

# event type -> (old action, new action)
_ACTION_RENAMES: Final[tuple[tuple[str, str, str], ...]] = (
    ("BlacklistSourceChangedEvent", "add", "create"),
    ("BlacklistSourceChangedEvent", "remove", "delete"),
    ("BannerChangedEvent", "reset_default", "reset"),
)

# event type -> (old payload key, new payload key)
_KEY_RENAMES: Final[tuple[tuple[str, str, str], ...]] = (
    ("SubscriptionAddOnGrantedEvent", "user", "actor"),
    ("LegalDocumentChangedEvent", "changed", "changed_fields"),
)


def _rename(table: str, old: str, new: str, action: Optional[str]) -> None:
    if action is None:
        op.execute(
            sa.text(f"UPDATE {table} SET event_type = :new WHERE event_type = :old").bindparams(
                old=old, new=new
            )
        )
        return
    op.execute(
        sa.text(
            f"UPDATE {table} SET event_type = :new, "
            "payload = payload || jsonb_build_object('action', CAST(:action AS text)) "
            "WHERE event_type = :old"
        ).bindparams(old=old, new=new, action=action)
    )


def _unrename(table: str, old: str, new: str, action: Optional[str]) -> None:
    if action is None:
        _rename(table, new, old, None)
        return
    op.execute(
        sa.text(
            f"UPDATE {table} SET event_type = :old, payload = payload - 'action' "
            "WHERE event_type = :new AND payload ->> 'action' = :action"
        ).bindparams(old=old, new=new, action=action)
    )


def _set_action(table: str, event_type: str, old: str, new: str) -> None:
    op.execute(
        sa.text(
            f"UPDATE {table} "
            "SET payload = jsonb_set(payload, '{action}', to_jsonb(CAST(:new AS text))) "
            "WHERE event_type = :event_type AND payload ->> 'action' = :old"
        ).bindparams(event_type=event_type, old=old, new=new)
    )


def _move_key(table: str, event_type: str, old: str, new: str) -> None:
    op.execute(
        sa.text(
            f"UPDATE {table} "
            "SET payload = (payload - CAST(:old AS text)) "
            "|| jsonb_build_object(CAST(:new AS text), payload -> CAST(:old AS text)) "
            "WHERE event_type = :event_type AND payload ? CAST(:old AS text)"
        ).bindparams(event_type=event_type, old=old, new=new)
    )


def _set_category(table: str, event_type: str, category: str) -> None:
    op.execute(
        sa.text(
            f"UPDATE {table} SET category = '{category}' WHERE event_type = :event_type"
        ).bindparams(event_type=event_type)
    )


def upgrade() -> None:
    for table in _TABLES:
        for old, (new, action) in _RENAMES.items():
            _rename(table, old, new, action)
        for event_type, old_action, new_action in _ACTION_RENAMES:
            _set_action(table, event_type, old_action, new_action)
        for event_type, old_key, new_key in _KEY_RENAMES:
            _move_key(table, event_type, old_key, new_key)
        _set_category(table, "CabinetNewDeviceSignInEvent", "AUTH")


def downgrade() -> None:
    for table in _TABLES:
        _set_category(table, "CabinetNewDeviceSignInEvent", "USER")
        for event_type, old_key, new_key in _KEY_RENAMES:
            _move_key(table, event_type, new_key, old_key)
        for event_type, old_action, new_action in _ACTION_RENAMES:
            _set_action(table, event_type, new_action, old_action)
        for old, (new, action) in _RENAMES.items():
            _unrename(table, old, new, action)
