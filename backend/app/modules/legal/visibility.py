from typing import Optional

from app.core.enums import LegalDocumentKind, Locale, PurchaseChannel
from app.modules.legal.dto import LegalDocumentDto, LegalRevisionDto
from app.modules.legal.repository import LegalRepository


async def resolve_revision(
    repo: LegalRepository,
    kind: LegalDocumentKind,
    channel: PurchaseChannel,
    locale: Locale,
    default_locale: Locale,
) -> Optional[LegalRevisionDto]:
    """The text a customer reads: their language before a channel override, the
    default language last; an empty revision removes its text."""
    chain: list[tuple[Locale, Optional[PurchaseChannel]]] = [
        (locale, channel),
        (locale, None),
        (default_locale, channel),
        (default_locale, None),
    ]
    for chain_locale, chain_channel in dict.fromkeys(chain):
        revision = await repo.find_current(kind, chain_locale, chain_channel)
        if revision is not None and revision.body.strip():
            return revision
    return None


async def visible_documents(
    repo: LegalRepository,
    documents: list[LegalDocumentDto],
    channel: PurchaseChannel,
    locale: Optional[Locale],
    default_locale: Locale,
    active_locales: list[Locale],
    kinds: frozenset[LegalDocumentKind] = frozenset(LegalDocumentKind),
) -> list[LegalRevisionDto]:
    if locale not in active_locales:
        locale = default_locale
    by_kind = {document.kind: document for document in documents}
    visible: list[LegalRevisionDto] = []
    for kind in LegalDocumentKind:
        if kind not in kinds:
            continue
        document = by_kind.get(kind)
        if document is None:
            continue
        shown = document.show_in_bot if channel == PurchaseChannel.BOT else document.show_in_cabinet
        if not shown:
            continue
        revision = await resolve_revision(repo, kind, channel, locale, default_locale)
        if revision is not None:
            visible.append(revision)
    return visible
