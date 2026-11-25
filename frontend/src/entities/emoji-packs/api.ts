import { apiDelete, apiGet, apiPost, BASE_URL } from "@shared/api/http";

import { LUCIDE_PACK_ICONS } from "@entities/emoji-packs/lucide-pack";
import type { ApiSchema } from "@shared/api/schemas";

export type EmojiPackItem = ApiSchema<"EmojiPackItemResponse">;

export type EmojiPack = ApiSchema<"EmojiPackResponse">;

export function listEmojiPacks(signal?: AbortSignal): Promise<EmojiPack[]> {
  return apiGet<ApiSchema<"EmojiPackListResponse">>("/emoji-packs", signal).then((response) => response.items);
}

export function importEmojiPack(link: string): Promise<EmojiPack> {
  return apiPost<EmojiPack, ApiSchema<"ImportEmojiPackRequest">>("/emoji-packs", { link });
}

export function deleteEmojiPack(setName: string): Promise<null> {
  return apiDelete<null>(`/emoji-packs/${encodeURIComponent(setName)}`);
}

/** The pack's real artwork, served as a static thumbnail: sessionless, so an
 * <img> can point straight at it. A lucide_dev emoji is its lucide icon instead. */
export function emojiThumbnailUrl(customEmojiId: string): string {
  const lucide = LUCIDE_PACK_ICONS[customEmojiId];
  if (lucide) return lucideDataUrl(lucide.node);
  return `${BASE_URL}/emoji-packs/thumbnails/${customEmojiId}`;
}

// white, as the pack's own artwork
function lucideDataUrl(node: (typeof LUCIDE_PACK_ICONS)[string]["node"]): string {
  const body = node
    .map(([tag, attrs]) => `<${tag} ${Object.entries(attrs).map(([k, v]) => `${k}="${v}"`).join(" ")}/>`)
    .join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

/** The animation itself: gzipped lottie JSON, or a .webm. */
export function emojiAnimationUrl(customEmojiId: string): string {
  return `${BASE_URL}/emoji-packs/animations/${customEmojiId}`;
}
