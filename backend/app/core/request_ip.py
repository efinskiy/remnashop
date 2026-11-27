from contextvars import ContextVar
from typing import Final, Optional

# set by the api for each request; read when an actor's event names no address
REQUEST_CLIENT_IP: Final[ContextVar[Optional[str]]] = ContextVar("request_client_ip", default=None)
