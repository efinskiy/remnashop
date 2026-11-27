import pytest

from app.core.actor import SYSTEM_ACTOR, Actor, SyntheticActor
from app.core.enums import Locale, Role
from app.core.exceptions import ValidationError
from app.core.security.permissions import (
    GRANTABLE_PERMISSIONS,
    PERMISSION_METADATA,
    ROLE_PERMISSIONS,
    TOKEN_GRANTABLE_PERMISSIONS,
    Permission,
    PermissionPolicy,
    assert_grantable,
    expand_token_scopes,
)
from app.modules.users.dto import UserDto

OWNER = UserDto(id=1, login="owner", name="owner", role=Role.OWNER, language=Locale.EN)
ADMIN = UserDto(id=2, login="admin", name="admin", role=Role.ADMIN, language=Locale.EN)
REGULAR_USER = UserDto(id=3, name="Bob", role=Role.USER, language=Locale.EN)


def test_owner_has_manage_admins_by_default() -> None:
    assert PermissionPolicy.has_permission(OWNER, Permission.ADMINS_MANAGE)


def test_admin_does_not_have_manage_admins_by_default() -> None:
    assert not PermissionPolicy.has_permission(ADMIN, Permission.ADMINS_MANAGE)


def test_admin_gains_permission_via_grant() -> None:
    granted_admin = ADMIN.model_copy(update={"permission_grants": ["ADMINS_MANAGE"]})
    assert PermissionPolicy.has_permission(granted_admin, Permission.ADMINS_MANAGE)


def test_admin_loses_default_permission_via_revoke() -> None:
    revoked_admin = ADMIN.model_copy(update={"permission_revokes": ["BOT_SETTINGS_MANAGE"]})
    assert not PermissionPolicy.has_permission(revoked_admin, Permission.BOT_SETTINGS_MANAGE)


def test_manage_admins_is_not_grantable() -> None:
    assert Permission.ADMINS_MANAGE not in GRANTABLE_PERMISSIONS


def test_assert_grantable_rejects_manage_admins() -> None:
    with pytest.raises(ValidationError):
        assert_grantable([Permission.ADMINS_MANAGE])


def test_assert_grantable_allows_ordinary_permissions() -> None:
    assert_grantable([Permission.BOT_SETTINGS_MANAGE])  # does not raise


def test_regular_user_has_no_permissions_by_default() -> None:
    assert not PermissionPolicy.has_permission(REGULAR_USER, Permission.OWN_ACCOUNT_MANAGE)


def test_effective_permissions_drops_stale_grant_string() -> None:
    stale_admin = ADMIN.model_copy(update={"permission_grants": ["SOME_REMOVED_PERMISSION"]})
    effective = PermissionPolicy.effective_permissions(stale_admin)
    assert effective == ROLE_PERMISSIONS[Role.ADMIN]


def test_effective_permissions_drops_stale_revoke_string() -> None:
    stale_admin = ADMIN.model_copy(update={"permission_revokes": ["SOME_REMOVED_PERMISSION"]})
    effective = PermissionPolicy.effective_permissions(stale_admin)
    assert effective == ROLE_PERMISSIONS[Role.ADMIN]


def test_view_event_log_is_grantable() -> None:
    assert Permission.EVENT_LOG_VIEW in GRANTABLE_PERMISSIONS


def test_owner_has_view_event_log_by_default() -> None:
    assert PermissionPolicy.has_permission(OWNER, Permission.EVENT_LOG_VIEW)


def test_admin_does_not_have_view_event_log_by_default() -> None:
    assert not PermissionPolicy.has_permission(ADMIN, Permission.EVENT_LOG_VIEW)


def test_admin_gains_view_event_log_via_grant() -> None:
    granted_admin = ADMIN.model_copy(update={"permission_grants": ["EVENT_LOG_VIEW"]})
    assert PermissionPolicy.has_permission(granted_admin, Permission.EVENT_LOG_VIEW)


def test_view_users_is_grantable() -> None:
    assert Permission.USERS_VIEW in GRANTABLE_PERMISSIONS


def test_owner_has_view_users_by_default() -> None:
    assert PermissionPolicy.has_permission(OWNER, Permission.USERS_VIEW)


def test_admin_has_view_users_by_default() -> None:
    assert PermissionPolicy.has_permission(ADMIN, Permission.USERS_VIEW)


def test_delete_user_is_grantable() -> None:
    assert Permission.USERS_DELETE in GRANTABLE_PERMISSIONS


def test_owner_has_delete_user_by_default() -> None:
    assert PermissionPolicy.has_permission(OWNER, Permission.USERS_DELETE)


def test_admin_does_not_have_delete_user_by_default() -> None:
    assert not PermissionPolicy.has_permission(ADMIN, Permission.USERS_DELETE)


def test_admin_gains_delete_user_via_grant() -> None:
    granted_admin = ADMIN.model_copy(update={"permission_grants": ["USERS_DELETE"]})
    assert PermissionPolicy.has_permission(granted_admin, Permission.USERS_DELETE)


def test_manage_api_tokens_is_not_grantable() -> None:
    assert Permission.API_TOKENS_MANAGE not in GRANTABLE_PERMISSIONS


def test_assert_grantable_rejects_manage_api_tokens() -> None:
    with pytest.raises(ValidationError):
        assert_grantable([Permission.API_TOKENS_MANAGE])


def test_owner_has_manage_api_tokens_by_default() -> None:
    assert PermissionPolicy.has_permission(OWNER, Permission.API_TOKENS_MANAGE)


def test_admin_does_not_have_manage_api_tokens_by_default() -> None:
    assert not PermissionPolicy.has_permission(ADMIN, Permission.API_TOKENS_MANAGE)


def test_manage_own_account_is_not_grantable() -> None:
    # every privileged role has it by default, and revoking it breaks GET /users/me
    assert Permission.OWN_ACCOUNT_MANAGE not in TOKEN_GRANTABLE_PERMISSIONS
    assert Permission.OWN_ACCOUNT_MANAGE not in GRANTABLE_PERMISSIONS


def test_every_catalog_permission_has_metadata() -> None:
    non_catalog = {
        Permission.PUBLIC,
        Permission.OWN_ACCOUNT_MANAGE,
        Permission.ADMINS_MANAGE,
        Permission.API_TOKENS_MANAGE,
        Permission.PRICING_RATES_MANAGE,
        Permission.PRICING_ANCHOR_MANAGE,
        Permission.TRANSACTIONS_UNRATED_RATE,
        Permission.USERS_UNBLOCK_BLACKLIST_MATCHES,
        Permission.BACKUPS_RUN_DOWNLOAD,
        Permission.NOTIFICATION_VAPID_KEYS_GENERATE,
        Permission.OVERVIEW_RECAP_VIEW,
    }
    assert set(Permission) - PERMISSION_METADATA.keys() == non_catalog


def test_admin_default_is_the_catalog_minus_the_owner_defaults() -> None:
    admin = ROLE_PERMISSIONS[Role.ADMIN]
    assert admin - PERMISSION_METADATA.keys() == {Permission.OWN_ACCOUNT_MANAGE}
    assert PERMISSION_METADATA.keys() - admin == {
        Permission.OAUTH_SETTINGS_MANAGE,
        Permission.EMAIL_SETTINGS_MANAGE,
        Permission.EMAIL_SETTINGS_BULK_RESET,
        Permission.EMAIL_SETTINGS_RESET,
        Permission.EVENT_LOG_VIEW,
        Permission.EVENT_LOG_DETAIL_VIEW,
        Permission.NOTIFICATION_SETTINGS_VIEW,
        Permission.NOTIFICATION_SETTINGS_MANAGE,
        Permission.USERS_DELETE,
        Permission.STAFF_SELF_MANAGE,
        Permission.USER_SESSIONS_VIEW,
        Permission.USER_SESSIONS_REVOKE,
        Permission.APPEARANCE_SETTINGS_MANAGE,
        Permission.APPEARANCE_SETTINGS_RESET,
        Permission.APPEARANCE_LOGO_UPLOAD,
        Permission.APPEARANCE_LOGO_DELETE,
        Permission.APPEARANCE_FAVICON_UPLOAD,
        Permission.APPEARANCE_FAVICON_DELETE,
        Permission.APPEARANCE_APP_ICON_UPLOAD,
        Permission.APPEARANCE_APP_ICON_DELETE,
        Permission.GATEWAYS_VIEW,
        Permission.GATEWAYS_UPDATE,
        Permission.GATEWAYS_ACTIVE_SET,
        Permission.GATEWAYS_CHANNELS_UPDATE,
        Permission.GATEWAYS_REORDER,
        Permission.GATEWAYS_TEST,
        Permission.GATEWAYS_TEST_VIEW,
        Permission.TRANSACTIONS_REFUND,
        Permission.TRANSACTIONS_REFUND_PREVIEW,
        Permission.BACKUPS_VIEW,
        Permission.BACKUPS_SETTINGS_VIEW,
        Permission.BACKUPS_SETTINGS_MANAGE,
        Permission.BACKUPS_SETTINGS_RESET,
        Permission.BACKUPS_RUN_VIEW,
        Permission.BACKUPS_RUN_CREATE,
        Permission.BACKUPS_RUN_DELETE,
        Permission.BACKUPS_RUN_CANCEL,
        Permission.BACKUPS_STATS_VIEW,
        Permission.BLACKLIST_VIEW,
        Permission.BLACKLIST_SOURCES_VIEW,
        Permission.BLACKLIST_SOURCE_DETAIL_VIEW,
        Permission.BLACKLIST_ENTRY_ADD,
        Permission.BLACKLIST_ENTRY_REMOVE,
        Permission.BLACKLIST_SOURCE_ADD,
        Permission.BLACKLIST_SOURCE_REMOVE,
        Permission.BLACKLIST_SOURCE_UPDATE,
        Permission.BLACKLIST_SYNC,
        Permission.BLACKLIST_MATCHES_VIEW,
        Permission.USERS_BLOCK,
        Permission.USERS_UNBLOCK,
        Permission.USERS_MERGE_PREVIEW,
        Permission.USERS_MERGE,
        Permission.USERS_TELEGRAM_BIND,
        Permission.USERS_TELEGRAM_UNBIND,
    }


def test_user_sessions_revoke_is_distinct_from_view() -> None:
    assert Permission.USER_SESSIONS_REVOKE != Permission.USER_SESSIONS_VIEW
    granted_view_only = ADMIN.model_copy(
        update={"permission_grants": [Permission.USER_SESSIONS_VIEW.value]}
    )
    assert not PermissionPolicy.has_permission(granted_view_only, Permission.USER_SESSIONS_REVOKE)


def test_banner_permissions_are_independently_gateable() -> None:
    # ADMIN has every banner permission by default; revoke two, BANNERS_UPLOAD stays
    upload_only = ADMIN.model_copy(
        update={
            "permission_revokes": [
                Permission.BANNERS_IMAGE_VIEW.value,
                Permission.BANNERS_DELETE.value,
            ]
        }
    )
    assert PermissionPolicy.has_permission(upload_only, Permission.BANNERS_UPLOAD)
    assert not PermissionPolicy.has_permission(upload_only, Permission.BANNERS_DELETE)
    assert not PermissionPolicy.has_permission(upload_only, Permission.BANNERS_IMAGE_VIEW)


def test_gateways_permissions_are_grantable() -> None:
    assert Permission.GATEWAYS_VIEW in GRANTABLE_PERMISSIONS
    assert Permission.GATEWAYS_UPDATE in GRANTABLE_PERMISSIONS
    assert Permission.GATEWAYS_ACTIVE_SET in GRANTABLE_PERMISSIONS
    assert Permission.GATEWAYS_REORDER in GRANTABLE_PERMISSIONS


def test_owner_has_gateways_permissions_by_default() -> None:
    assert PermissionPolicy.has_permission(OWNER, Permission.GATEWAYS_VIEW)
    assert PermissionPolicy.has_permission(OWNER, Permission.GATEWAYS_UPDATE)


def test_admin_does_not_have_gateways_permissions_by_default() -> None:
    assert not PermissionPolicy.has_permission(ADMIN, Permission.GATEWAYS_VIEW)
    assert not PermissionPolicy.has_permission(ADMIN, Permission.GATEWAYS_UPDATE)
    assert not PermissionPolicy.has_permission(ADMIN, Permission.GATEWAYS_ACTIVE_SET)
    assert not PermissionPolicy.has_permission(ADMIN, Permission.GATEWAYS_REORDER)


def test_admin_gains_gateways_view_via_grant() -> None:
    granted_admin = ADMIN.model_copy(update={"permission_grants": ["GATEWAYS_VIEW"]})
    assert PermissionPolicy.has_permission(granted_admin, Permission.GATEWAYS_VIEW)


def test_gateways_permissions_are_independently_gateable() -> None:
    view_only = OWNER.model_copy(
        update={
            "permission_revokes": [
                Permission.GATEWAYS_UPDATE.value,
                Permission.GATEWAYS_ACTIVE_SET.value,
                Permission.GATEWAYS_REORDER.value,
            ]
        }
    )
    assert PermissionPolicy.has_permission(view_only, Permission.GATEWAYS_VIEW)
    assert not PermissionPolicy.has_permission(view_only, Permission.GATEWAYS_UPDATE)


def test_plans_permissions_granted_to_admin_by_default() -> None:
    admin_default = ROLE_PERMISSIONS[Role.ADMIN]
    for permission in (
        Permission.PLANS_VIEW,
        Permission.PLANS_DETAIL_VIEW,
        Permission.PLANS_SHARE_VIEW,
        Permission.PLANS_CREATE,
        Permission.PLANS_UPDATE,
        Permission.PLANS_DELETE,
        Permission.PLANS_DURATIONS_MANAGE,
        Permission.PLANS_PRICE_OVERRIDE_MANAGE,
        Permission.PLANS_DURATION_BASE_PRICE_MANAGE,
        Permission.PLANS_ACCESS_MANAGE,
        Permission.PLANS_SQUADS_MANAGE,
        Permission.PLANS_DISCOUNT_MANAGE,
        Permission.PLANS_ORDER_MANAGE,
    ):
        assert permission in admin_default
        assert permission in PERMISSION_METADATA


def test_subscriptions_permissions_granted_to_admin_by_default() -> None:
    admin_default = ROLE_PERMISSIONS[Role.ADMIN]
    for permission in (
        Permission.SUBSCRIPTIONS_VIEW,
        Permission.SUBSCRIPTIONS_DETAIL_VIEW,
        Permission.SUBSCRIPTIONS_UPDATE,
        Permission.SUBSCRIPTIONS_SQUADS_MANAGE,
        Permission.SUBSCRIPTIONS_DELETE,
        Permission.ADDONS_VIEW,
        Permission.ADDONS_DETAIL_VIEW,
        Permission.ADDONS_CREATE,
        Permission.ADDONS_UPDATE,
        Permission.ADDONS_DELETE,
        Permission.ADDONS_PRICES_MANAGE,
        Permission.ADDONS_PRICE_OVERRIDE_MANAGE,
    ):
        assert permission in admin_default
        assert permission in PERMISSION_METADATA


def test_admin_role_has_all_referrals_permissions() -> None:
    admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.REFERRALS_VIEW in admin_perms
    assert Permission.REFERRALS_INVITED_VIEW in admin_perms
    assert Permission.REFERRALS_REVENUE_VIEW in admin_perms
    assert Permission.REFERRALS_LIST in admin_perms
    assert Permission.REFERRALS_SUMMARY_VIEW in admin_perms
    assert Permission.REFERRALS_SETTINGS_VIEW in admin_perms
    assert Permission.REFERRALS_SETTINGS_MANAGE in admin_perms
    assert Permission.REFERRALS_SETTINGS_RESET in admin_perms
    assert Permission.REFERRALS_POINTS_MANAGE in admin_perms
    assert Permission.REFERRALS_BONUS_DAYS_MANAGE in admin_perms
    assert Permission.REFERRALS_CODE_RESET in admin_perms


def test_backups_permissions_are_grantable_but_not_default_admin() -> None:
    backups_permissions = (
        Permission.BACKUPS_VIEW,
        Permission.BACKUPS_SETTINGS_VIEW,
        Permission.BACKUPS_SETTINGS_MANAGE,
        Permission.BACKUPS_RUN_VIEW,
        Permission.BACKUPS_RUN_CREATE,
        Permission.BACKUPS_RUN_DELETE,
        Permission.BACKUPS_RUN_CANCEL,
        Permission.BACKUPS_STATS_VIEW,
    )
    admin_default = ROLE_PERMISSIONS[Role.ADMIN]
    owner_default = ROLE_PERMISSIONS[Role.OWNER]
    for permission in backups_permissions:
        assert permission in GRANTABLE_PERMISSIONS
        assert permission not in admin_default
        assert permission in owner_default


def test_token_cannot_take_over_login_bot_or_payments() -> None:
    # still delegable to an admin, never to a bearer string in a script
    for permission in (
        Permission.OAUTH_SETTINGS_MANAGE,
        Permission.EMAIL_SETTINGS_MANAGE,
        Permission.BOT_SETTINGS_MANAGE,
        Permission.BOT_PROXY_SET,
        Permission.GATEWAYS_UPDATE,
        Permission.GATEWAYS_ACTIVE_SET,
        Permission.USERS_DELETE,
        Permission.BACKUPS_RUN_DELETE,
    ):
        assert permission in GRANTABLE_PERMISSIONS
        assert permission not in TOKEN_GRANTABLE_PERMISSIONS


def test_token_scope_wildcard_expands_to_every_token_grantable_permission() -> None:
    assert expand_token_scopes(["*"]) == set(TOKEN_GRANTABLE_PERMISSIONS)


def test_token_resource_scopes_follow_resource_and_kind() -> None:
    reads = expand_token_scopes(["users:read"])
    assert Permission.USERS_VIEW in reads
    assert Permission.USERS_BLOCK not in reads
    everything = expand_token_scopes(["users:*"])
    assert {Permission.USERS_VIEW, Permission.USERS_BLOCK} <= everything
    # excluded permissions never come back through a broader scope
    assert Permission.USERS_DELETE not in everything
    assert Permission.OAUTH_SETTINGS_MANAGE not in expand_token_scopes(["*"])


def test_token_leaf_scope_is_a_single_permission() -> None:
    assert expand_token_scopes(["PLANS_VIEW"]) == {Permission.PLANS_VIEW}
    assert expand_token_scopes(["USERS_DELETE", "bogus", "users:delete"]) == set()


def test_token_grantable_is_a_subset_of_grantable() -> None:
    assert TOKEN_GRANTABLE_PERMISSIONS < GRANTABLE_PERMISSIONS


def test_backup_download_is_owner_only() -> None:
    # a DATABASE dump holds every table, password hashes included, so it
    # subsumes every read permission and can't be delegated
    assert Permission.BACKUPS_RUN_DOWNLOAD not in GRANTABLE_PERMISSIONS
    assert Permission.BACKUPS_RUN_DOWNLOAD not in TOKEN_GRANTABLE_PERMISSIONS
    assert Permission.BACKUPS_RUN_DOWNLOAD not in ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.BACKUPS_RUN_DOWNLOAD in ROLE_PERMISSIONS[Role.OWNER]


def test_blacklist_permissions_are_owner_only_by_default() -> None:
    for perm in (
        Permission.BLACKLIST_VIEW,
        Permission.BLACKLIST_SOURCES_VIEW,
        Permission.BLACKLIST_ENTRY_ADD,
        Permission.BLACKLIST_ENTRY_REMOVE,
        Permission.BLACKLIST_SOURCE_ADD,
        Permission.BLACKLIST_SOURCE_REMOVE,
        Permission.BLACKLIST_SOURCE_UPDATE,
        Permission.BLACKLIST_SYNC,
        Permission.BLACKLIST_MATCHES_VIEW,
        Permission.USERS_BLOCK,
        Permission.USERS_UNBLOCK,
        Permission.USERS_UNBLOCK_BLACKLIST_MATCHES,
    ):
        assert perm in ROLE_PERMISSIONS[Role.OWNER]
        assert perm not in ROLE_PERMISSIONS[Role.ADMIN]


def test_unblock_blacklist_matches_is_not_grantable() -> None:
    assert Permission.USERS_UNBLOCK_BLACKLIST_MATCHES not in GRANTABLE_PERMISSIONS
    assert Permission.BLACKLIST_ENTRY_ADD in GRANTABLE_PERMISSIONS


def test_admin_role_has_ad_links_permissions() -> None:
    assert Permission.AD_LINKS_VIEW in ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.AD_LINKS_CREATE in ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.AD_LINKS_UPDATE in ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.AD_LINKS_DELETE in ROLE_PERMISSIONS[Role.ADMIN]


def test_ad_links_permissions_are_grantable() -> None:
    assert Permission.AD_LINKS_VIEW in GRANTABLE_PERMISSIONS
    assert Permission.AD_LINKS_CREATE in GRANTABLE_PERMISSIONS


def test_admin_can_open_a_user_card_by_default() -> None:
    assert PermissionPolicy.has_permission(ADMIN, Permission.USERS_DETAIL_VIEW)


_TOKEN = SyntheticActor(
    id=0, role=Role.USER, name="API Token: ci", is_privileged=True, log="[api_token:ci]"
)


@pytest.mark.parametrize(
    ("actor", "target", "allowed"),
    [
        (ADMIN, REGULAR_USER, True),
        (ADMIN, ADMIN, False),
        (ADMIN, OWNER, False),
        (OWNER, REGULAR_USER, True),
        (OWNER, ADMIN, True),
        (OWNER, OWNER, False),
        (_TOKEN, REGULAR_USER, True),
        (_TOKEN, ADMIN, False),
        (_TOKEN, OWNER, False),
        (SYSTEM_ACTOR, ADMIN, True),
        (SYSTEM_ACTOR, OWNER, True),
    ],
)
def test_can_manage_reaches_customers_and_only_lower_staff(
    actor: Actor, target: UserDto, allowed: bool
) -> None:
    assert PermissionPolicy.can_manage(actor, target) is allowed


_ADMIN_SUBSCRIPTION_PERMISSIONS = (
    Permission.SUBSCRIPTIONS_GRANT,
    Permission.SUBSCRIPTIONS_PLAN_CHANGE,
    Permission.SUBSCRIPTIONS_STATUS_MANAGE,
    Permission.SUBSCRIPTIONS_TRAFFIC_RESET,
    Permission.SUBSCRIPTIONS_LINK_REISSUE,
    Permission.SUBSCRIPTIONS_DEVICES_VIEW,
    Permission.SUBSCRIPTIONS_DEVICES_DELETE,
    Permission.SUBSCRIPTIONS_DEVICES_DELETE_ALL,
)


def test_admin_subscription_permissions_are_admin_default_and_grantable() -> None:
    for permission in _ADMIN_SUBSCRIPTION_PERMISSIONS:
        assert permission in ROLE_PERMISSIONS[Role.ADMIN]
        assert permission in GRANTABLE_PERMISSIONS
        assert PERMISSION_METADATA[permission].resource == "subscriptions"


def test_irreversible_subscription_actions_are_not_token_grantable() -> None:
    assert Permission.SUBSCRIPTIONS_LINK_REISSUE not in TOKEN_GRANTABLE_PERMISSIONS
    assert Permission.SUBSCRIPTIONS_DEVICES_DELETE not in TOKEN_GRANTABLE_PERMISSIONS
    assert Permission.SUBSCRIPTIONS_DEVICES_DELETE_ALL not in TOKEN_GRANTABLE_PERMISSIONS
    assert Permission.SUBSCRIPTIONS_DELETE_ALL not in TOKEN_GRANTABLE_PERMISSIONS
    assert Permission.SUBSCRIPTIONS_GRANT in TOKEN_GRANTABLE_PERMISSIONS


def test_backups_write_token_cannot_rotate_or_reset_history() -> None:
    granted = expand_token_scopes(["backups:write"])
    assert Permission.BACKUPS_SETTINGS_RESET not in granted
    assert Permission.BACKUPS_RUN_CREATE not in granted


def test_oauth_settings_manage_is_owner_only_by_default() -> None:
    assert Permission.OAUTH_SETTINGS_MANAGE not in ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.EMAIL_SETTINGS_MANAGE not in ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.EMAIL_SETTINGS_MANAGE in ROLE_PERMISSIONS[Role.OWNER]
    assert Permission.EMAIL_SETTINGS_MANAGE in GRANTABLE_PERMISSIONS
    assert Permission.OAUTH_SETTINGS_MANAGE in ROLE_PERMISSIONS[Role.OWNER]
    assert Permission.OAUTH_SETTINGS_MANAGE in GRANTABLE_PERMISSIONS


@pytest.mark.parametrize(
    "permission", [Permission.TRANSACTIONS_REFUND, Permission.TRANSACTIONS_REFUND_PREVIEW]
)
def test_refund_permissions_are_owner_only_and_not_for_tokens(permission: Permission) -> None:
    assert permission in GRANTABLE_PERMISSIONS
    assert permission not in ROLE_PERMISSIONS[Role.ADMIN]
    assert permission in ROLE_PERMISSIONS[Role.OWNER]
    assert permission not in TOKEN_GRANTABLE_PERMISSIONS
