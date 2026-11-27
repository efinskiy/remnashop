from pathlib import Path

import pytest
from fluent.syntax import FluentParser
from fluent.syntax.ast import Message

from app.core.enums import Locale
from app.modules.notifications.dto import NOTIFICATION_GROUPS
from app.modules.notifications.render import (
    TEST_EVENT_TYPE,
    NotificationRenderer,
    message_id,
    notification_args,
    telegram_card,
)

_TRANSLATIONS_DIR = Path(__file__).parents[3] / "assets" / "translations"
SEEDED_LOCALES = (Locale.EN, Locale.RU)
FTL = "ntf-login-failed = Login { $login }\n    .title = Login failed\n"


def _messages(path: Path) -> dict[str, Message]:
    resource = FluentParser().parse(path.read_text())
    return {e.id.name: e for e in resource.body if isinstance(e, Message)}


@pytest.mark.parametrize("locale", SEEDED_LOCALES)
def test_every_notification_type_has_a_template_with_a_title(locale: Locale) -> None:
    messages = _messages(_TRANSLATIONS_DIR / locale.value / "notifications.ftl")
    event_types = [*frozenset().union(*NOTIFICATION_GROUPS.values()), TEST_EVENT_TYPE]
    for event_type in event_types:
        key = message_id(event_type)
        assert key in messages, f"{key} missing in {locale}"
        assert messages[key].value is not None
        assert any(a.id.name == "title" for a in messages[key].attributes)


def test_message_id_is_kebab_without_event_suffix() -> None:
    assert message_id("LoginFailedEvent") == "ntf-login-failed"
    assert message_id("OAuthLoginFailedEvent") == "ntf-oauth-login-failed"
    assert message_id(TEST_EVENT_TYPE) == "ntf-test"


def test_args_flatten_user_snapshots_and_keep_scalars() -> None:
    args = notification_args(
        {"user": {"login": None, "username": "bob", "name": "Bob"}, "amount": "500", "flag": True},
        "1.2.3.4",
        Locale.RU,
    )
    assert args == {"user": "@bob", "amount": "500", "flag": "yes", "ip": "1.2.3.4"}


def test_args_format_an_amount_with_its_currency() -> None:
    args = notification_args({"amount": "18450.00", "currency": "RUB"}, None, Locale.RU)
    assert args["money"] == "18\xa0450\xa0₽"


def test_an_id_is_printed_without_grouping_and_a_count_with_it() -> None:
    renderer = NotificationRenderer(
        {Locale.RU: (_TRANSLATIONS_DIR / "ru" / "notifications.ftl").read_text()},
        default_locale=Locale.RU,
    )
    payload = {"broadcast_id": 10293, "sent": 1240, "failed": 0, "blocked": 0}

    _, body = renderer.render(
        Locale.RU, "BroadcastCompletedEvent", notification_args(payload, None, Locale.RU)
    )

    assert body.startswith("Рассылка #10293 завершена: доставлено 1\xa0240,")


@pytest.mark.parametrize(
    ("event_type", "payload", "shown"),
    [
        (
            "SubscriptionPurchasedEvent",
            {"purchase_type": "RENEW", "user": "@ivan"},
            "Клиент: @ivan",
        ),
        ("BackupFailedEvent", {"kind": "DATABASE", "error": "x"}, "копия базы данных"),
        ("CabinetUserRegisteredEvent", {"method": "EMAIL"}, "вход через почту"),
        ("OAuthLoginFailedEvent", {"provider": "GITHUB"}, "Вход через GitHub"),
    ],
)
def test_an_enum_value_is_worded_not_printed(
    event_type: str, payload: dict[str, str], shown: str
) -> None:
    renderer = NotificationRenderer(
        {Locale.RU: (_TRANSLATIONS_DIR / "ru" / "notifications.ftl").read_text()},
        default_locale=Locale.RU,
    )

    _, body = renderer.render(
        Locale.RU, event_type, notification_args({"is_trial": False, **payload}, None, Locale.RU)
    )

    assert shown in body
    assert not [v for k, v in payload.items() if k not in ("error", "user") and v in body]


def test_render_falls_back_to_default_locale_then_to_event_type() -> None:
    renderer = NotificationRenderer({Locale.EN: FTL}, default_locale=Locale.EN)
    assert renderer.render(Locale.DE, "LoginFailedEvent", {"login": "x"}) == (
        "Login failed",
        "Login x",
    )
    assert renderer.render(Locale.EN, "BackupFailedEvent", {}) == ("BackupFailedEvent", "")


def test_render_survives_a_missing_variable() -> None:
    renderer = NotificationRenderer({Locale.EN: FTL}, default_locale=Locale.EN)
    title, body = renderer.render(Locale.EN, "LoginFailedEvent", {})
    assert title == "Login failed"
    assert body


def test_render_falls_through_a_message_without_title() -> None:
    renderer = NotificationRenderer(
        {Locale.RU: "ntf-login-failed = Вход { $login }\n", Locale.EN: FTL},
        default_locale=Locale.EN,
    )
    assert renderer.render(Locale.RU, "LoginFailedEvent", {"login": "x"}) == (
        "Login failed",
        "Login x",
    )
    body_only = NotificationRenderer({Locale.EN: "ntf-login-failed = x\n"}, Locale.EN)
    assert body_only.render(Locale.EN, "LoginFailedEvent", {}) == ("LoginFailedEvent", "")


def test_missing_ip_reads_as_a_dash() -> None:
    assert notification_args({}, None, Locale.RU) == {"ip": "—"}


def test_broadcast_completed_renders_counts() -> None:
    texts = {Locale.EN: (_TRANSLATIONS_DIR / "en" / "notifications.ftl").read_text()}
    renderer = NotificationRenderer(texts, default_locale=Locale.EN)
    title, body = renderer.render(
        Locale.EN,
        "BroadcastCompletedEvent",
        {"broadcast_id": 4, "sent": 10, "failed": 1, "blocked": 2, "ip": "—"},
    )
    assert title == "Broadcast finished!"
    assert "10" in body
    assert "#4" in body


def test_text_falls_back_to_the_default_locale_and_misses_cleanly() -> None:
    renderer = NotificationRenderer(
        {
            Locale.EN: "ntf-access =\n    .payments-restored = Back!\nplain = Hello\n",
            Locale.RU: "plain = Привет\n",
        },
        default_locale=Locale.EN,
    )

    assert renderer.text(Locale.RU, "plain") == "Привет"
    assert renderer.text(Locale.RU, "ntf-access.payments-restored") == "Back!"
    assert renderer.text(Locale.RU, "ntf-access.missing") is None


def test_telegram_card_escapes_values_and_drops_empty_rows() -> None:
    card = telegram_card(
        "Sign-in <x>",
        "From 1.2.3.4 (<script>)",
        emoji="🔐",
        hashtag="NewDevice-Event",
        blocks=[
            ("👤", "User", [("ID", "7", True), ("Name", "A&B", False), ("Email", "", False)]),
            ("ℹ️", "Empty", [("Email", "", False)]),
        ],
        quote="Check <it>",
        footer="2 more",
    )

    assert card == (
        "#NewDeviceEvent\n\n<b>🔐 Sign-in &lt;x&gt;</b>\n\n"
        "<blockquote>From 1.2.3.4 (&lt;script&gt;)</blockquote>\n\n"
        "👤 <b>User</b>:\n<blockquote>• <b>ID</b>: <code>7</code>\n"
        "• <b>Name</b>: A&amp;B</blockquote>"
        "\n\n<blockquote>Check &lt;it&gt;</blockquote>\n\n<i>2 more</i>"
    )


def test_telegram_card_renders_premium_emoji_markup() -> None:
    card = telegram_card("Expired", "Renew it", emoji="[🚫](emoji:5872829476143894491)")

    assert card == (
        '<b><tg-emoji emoji-id="5872829476143894491">🚫</tg-emoji> Expired</b>\n\n'
        "<blockquote>Renew it</blockquote>"
    )


@pytest.mark.parametrize("locale", SEEDED_LOCALES)
@pytest.mark.parametrize(
    "event_type",
    [
        "NodeConnectionLostEvent",
        "NodeTrafficReachedEvent",
        "RemnawaveUnavailableEvent",
        "SystemHealthDegradedEvent",
        "TelegramWebhookFailedEvent",
    ],
)
def test_an_outage_is_marked_as_a_warning(locale: Locale, event_type: str) -> None:
    text = (_TRANSLATIONS_DIR / locale.value / "notifications.ftl").read_text()
    renderer = NotificationRenderer({locale: text}, default_locale=locale)

    assert renderer.emoji(locale, event_type) == "⚠️"


def test_a_renewal_names_the_customer_and_the_term_without_a_gendered_verb() -> None:
    renderer = NotificationRenderer(
        {Locale.RU: (_TRANSLATIONS_DIR / "ru" / "notifications.ftl").read_text()},
        default_locale=Locale.RU,
    )
    args = notification_args({"user": "@ivan", "duration_days": 30}, None, Locale.RU)

    _, body = renderer.render(Locale.RU, "SubscriptionRenewedEvent", args)

    assert body == "Клиент: @ivan, на 30 дней"
