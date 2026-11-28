from loguru import logger

from app.core.event_bus import EventBus
from app.core.events import StoredEvent
from app.modules.oauth.events import (
    OAuthIdentityLinkedEvent,
    OAuthIdentityUnlinkedEvent,
    OAuthLoginFailedEvent,
    OAuthLoginSucceededEvent,
)


async def _log_oauth_login_succeeded(event: OAuthLoginSucceededEvent, entry: StoredEvent) -> None:
    logger.info(f"Successful OAuth login via {event.provider} for login='{event.user.login}'")


async def _log_oauth_login_failed(event: OAuthLoginFailedEvent, entry: StoredEvent) -> None:
    logger.warning(f"Failed OAuth login attempt via {event.provider}")


async def _log_oauth_identity_linked(event: OAuthIdentityLinkedEvent, entry: StoredEvent) -> None:
    logger.info(f"OAuth identity linked: {event.provider} for login='{event.user.login}'")


async def _log_oauth_identity_unlinked(
    event: OAuthIdentityUnlinkedEvent, entry: StoredEvent
) -> None:
    logger.info(f"OAuth identity unlinked: {event.provider} for login='{event.user.login}'")


def register_subscribers(bus: EventBus) -> None:
    bus.subscribe(OAuthLoginSucceededEvent, _log_oauth_login_succeeded)
    bus.subscribe(OAuthLoginFailedEvent, _log_oauth_login_failed)
    bus.subscribe(OAuthIdentityLinkedEvent, _log_oauth_identity_linked)
    bus.subscribe(OAuthIdentityUnlinkedEvent, _log_oauth_identity_unlinked)
