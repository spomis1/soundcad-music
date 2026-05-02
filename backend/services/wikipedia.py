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
    # Build list of names to try
    names: list[str] = []
    if canonical_name and canonical_name.lower() != artist_name.lower():
        names.append(canonical_name)
    names.append(artist_name)
    ascii_name = unicodedata.normalize("NFD", artist_name).encode("ascii", "ignore").decode().strip()
    if ascii_name and ascii_name not in names:
        names.append(ascii_name)

    async with httpx.AsyncClient(timeout=8, headers=_HEADERS) as client:
        article_data = None
        wiki_title: str = ""

        for name in names:
            title = _norm_title(name)
            try:
                r = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
                )
                if r.status_code != 200:
                    continue
                d = r.json()
                if d.get("type") in ("disambiguation", "no-extract"):
                    continue
                # Sanity check: description should mention music/singer/band
                desc = (d.get("description") or "").lower()
                extract = (d.get("extract") or "").lower()
                music_kw = ("singer", "musician", "rapper", "band", "artist", "songwriter",
                            "producer", "dj", "group", "duo", "trio", "vocalist", "musical")
                if not any(k in desc or k in extract[:200] for k in music_kw):
                    # Accept it only if name matches exactly and there's nothing else to try
                    if name != names[-1]:
                        continue
                article_data = d
                wiki_title = d.get("title", title)
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
