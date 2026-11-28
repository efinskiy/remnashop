from pydantic import BaseModel

from app.core.dto import ResponseModel
from app.core.enums import Locale


class TranslationEntryResponse(ResponseModel):
    locale: Locale
    message_id: str
    attribute_id: str
    value: str
    default_value: str


class UpdateTranslationRequest(BaseModel):
    value: str


class TranslationTextExportResponse(ResponseModel):
    locale: Locale
    message_id: str
    attribute_id: str
    value: str


class TranslationTextImportRequest(BaseModel):
    locale: Locale
    message_id: str
    attribute_id: str
    value: str


class TranslationsExportResponse(ResponseModel):
    version: int
    texts: list[TranslationTextExportResponse]


class TranslationsImportRequest(BaseModel):
    version: int
    texts: list[TranslationTextImportRequest]


class TranslationsImportResponse(ResponseModel):
    applied: int
    skipped: int


class TranslationEntryListResponse(ResponseModel):
    items: list[TranslationEntryResponse]
    total: int


class ActiveLocalesResponse(ResponseModel):
    active: list[Locale]
    available: list[Locale]
    default: Locale


class UpdateLocalesRequest(BaseModel):
    default: Locale
