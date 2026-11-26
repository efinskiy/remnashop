from app.core.dto import ResponseModel
from app.core.enums import Locale


class BannerMetaResponse(ResponseModel):
    name: str
    locale: Locale
    content_type: str
    size_bytes: int
