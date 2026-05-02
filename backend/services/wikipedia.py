import unicodedata
import httpx
from datetime import datetime, timedelta

_HEADERS = {"User-Agent": "SoundCardMusic/1.0 (music-intelligence-dashboard; contact@soundcard.music)"}


def _norm_title(name: str) -> str:
    return name.replace(" ", "_")


async def get_artist_wikipedia(artist_name: str, canonical_name: str | None = None) -> dict:
    """
    Fetch Wikipedia bio extract + monthly pageviews for an artist.

    Tries names in order: canonical (accented), original, ASCII-stripped.
    Skips disambiguation pages. Returns {} if no article found.
    """
    # Build list of Wikipedia titles to try, ordered by likelihood
    base = canonical_name or artist_name
    ascii_base = unicodedata.normalize("NFD", base).encode("ascii", "ignore").decode().strip()

    titles_to_try: list[str] = []
    # 1. Canonical name (with accents)
    if canonical_name and canonical_name.lower() != artist_name.lower():
        titles_to_try.append(canonical_name)
    # 2. Original name
    titles_to_try.append(artist_name)
    # 3. Disambiguations for short/generic names (e.g. "Prince" → "Prince (musician)")
    for suffix in ("musician", "singer", "rapper", "band", "artist"):
        titles_to_try.append(f"{base} ({suffix})")
        if ascii_base and ascii_base != base:
            titles_to_try.append(f"{ascii_base} ({suffix})")
    # 4. ASCII fallback
    if ascii_base and ascii_base not in titles_to_try:
        titles_to_try.append(ascii_base)

    MUSIC_KW = ("singer", "musician", "rapper", "band", "artist", "songwriter",
                "producer", "dj", "group", "duo", "trio", "vocalist", "musical",
                "record", "album", "song", "pop", "rock", "hip-hop", "reggae",
                "cumbia", "salsa", "indie", "punk", "metal")

    async with httpx.AsyncClient(timeout=10, headers=_HEADERS) as client:
        article_data = None
        wiki_title: str = ""

        for title_name in titles_to_try:
            title = _norm_title(title_name)
            try:
                r = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
                )
                if r.status_code != 200:
                    continue
                d = r.json()
                if d.get("type") in ("disambiguation", "no-extract"):
                    continue
                # Sanity: description or start of extract should mention music
                desc = (d.get("description") or "").lower()
                extract_start = (d.get("extract") or "").lower()[:300]
                if not any(k in desc or k in extract_start for k in MUSIC_KW):
                    continue
                article_data = d
                wiki_title = d.get("title", title)
                break
            except Exception:
                continue

        # Fallback: try Spanish Wikipedia if nothing found in English
        if not article_data:
            for title_name in [base, ascii_base]:
                if not title_name:
                    continue
                try:
                    r = await client.get(
                        f"https://es.wikipedia.org/api/rest_v1/page/summary/{_norm_title(title_name)}"
                    )
                    if r.status_code == 200:
                        d = r.json()
                        if d.get("type") not in ("disambiguation", "no-extract"):
                            desc = (d.get("description") or "").lower()
                            extract_start = (d.get("extract") or "").lower()[:300]
                            if any(k in desc or k in extract_start for k in MUSIC_KW):
                                article_data = d
                                wiki_title = d.get("title", title_name)
                                break
                except Exception:
                    continue

        if not article_data:
            return {}

        # Build short bio (max 3 sentences, max 420 chars)
        extract: str = article_data.get("extract", "")
        if extract:
            sentences = extract.replace("\n", " ").split(". ")
            bio = ". ".join(sentences[:3]).strip()
            if bio and not bio.endswith("."):
                bio += "."
            if len(bio) > 420:
                bio = bio[:417] + "…"
        else:
            bio = ""

        wiki_url: str = article_data.get("content_urls", {}).get("desktop", {}).get("page", "")

        # Monthly pageviews (last 30 days)
        pageviews_30d = 0
        if wiki_title:
            try:
                end = datetime.now()
                start = end - timedelta(days=30)
                pv_r = await client.get(
                    f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
                    f"/en.wikipedia/all-access/all-agents/{_norm_title(wiki_title)}"
                    f"/daily/{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
                )
                if pv_r.status_code == 200:
                    items = pv_r.json().get("items", [])
                    pageviews_30d = sum(item.get("views", 0) for item in items)
            except Exception:
                pass

        return {
            "bio": bio,
            "wiki_url": wiki_url,
            "wiki_pageviews_30d": pageviews_30d,
        }
