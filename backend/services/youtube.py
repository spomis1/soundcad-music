import os
import re
import unicodedata
import httpx
from datetime import datetime, timedelta, timezone

BASE_URL = "https://www.googleapis.com/youtube/v3"


def _normalize(s: str) -> str:
    return unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode()


def _channel_matches_artist(channel_title: str, artist_name: str) -> bool:
    """
    Check if a YouTube channel belongs to the artist.
    Handles: "BadBunnyVEVO", "Bad Bunny Oficial", "Bad Bunny", "badbunnypr"
    """
    suffixes = r"(vevo|oficial|official|music|records|entertainment|tv|hd|channel|topic)$"
    clean_ch = re.sub(suffixes, "", _normalize(channel_title).replace(" ", ""))
    clean_ar = _normalize(artist_name).replace(" ", "")
    return clean_ar in clean_ch or clean_ch in clean_ar

# ISO 3166-1 alpha-2 codes for the regions we check
REGIONS = [
    "US", "GB", "DE", "BR", "FR", "MX", "AR", "ES", "AU", "CA",
    "JP", "KR", "IT", "NL", "PL", "SE", "RU", "TR", "IN", "ID",
]


async def _find_artist_channel(artist_name: str, client: httpx.AsyncClient) -> str | None:
    """Find the official YouTube channel ID for an artist. Returns None if not found."""
    r = await client.get(
        f"{BASE_URL}/search",
        params={
            "key": os.environ["YOUTUBE_API_KEY"],
            "q": artist_name,
            "type": "channel",
            "maxResults": 5,
            "part": "snippet",
        },
    )
    if r.status_code != 200:
        return None
    for item in r.json().get("items", []):
        ch_title = item["snippet"]["title"]
        if _channel_matches_artist(ch_title, artist_name):
            return item["id"]["channelId"]
    return None


async def search_artist_videos(artist_name: str, max_results: int = 10) -> list[dict]:
    """
    Search for the artist's top videos on YouTube.
    Strategy:
      1. Find the artist's official channel and get their most viewed videos.
      2. If no channel found, fall back to keyword search filtered by channel name.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        channel_id = await _find_artist_channel(artist_name, client)

        if channel_id:
            # Get most viewed videos from the official channel
            r = await client.get(
                f"{BASE_URL}/search",
                params={
                    "key": os.environ["YOUTUBE_API_KEY"],
                    "channelId": channel_id,
                    "type": "video",
                    "videoCategoryId": "10",
                    "order": "viewCount",
                    "maxResults": max_results,
                    "part": "snippet",
                },
            )
        else:
            # Fallback: keyword search, filter by channel name
            r = await client.get(
                f"{BASE_URL}/search",
                params={
                    "key": os.environ["YOUTUBE_API_KEY"],
                    "q": f"{artist_name} official music video",
                    "type": "video",
                    "videoCategoryId": "10",
                    "order": "relevance",
                    "maxResults": max_results * 2,  # fetch more to have room to filter
                    "part": "snippet",
                },
            )

        if r.status_code != 200:
            return []

        items = r.json().get("items", [])

        # If fallback search, filter to videos from the artist's channel
        if not channel_id:
            items = [
                i for i in items
                if _channel_matches_artist(i["snippet"]["channelTitle"], artist_name)
            ]

        return [
            {
                "video_id": i["id"]["videoId"],
                "title": i["snippet"]["title"],
                "published_at": i["snippet"]["publishedAt"],
                "thumbnail": i["snippet"]["thumbnails"].get("medium", {}).get("url"),
                "channel": i["snippet"]["channelTitle"],
            }
            for i in items[:max_results]
        ]


async def get_video_stats(video_ids: list[str]) -> dict[str, dict]:
    """Fetch view counts and likes for a list of video IDs."""
    if not video_ids:
        return {}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{BASE_URL}/videos",
            params={
                "key": os.environ["YOUTUBE_API_KEY"],
                "id": ",".join(video_ids),
                "part": "statistics",
            },
        )
        if r.status_code != 200:
            return {}
        stats = {}
        for item in r.json().get("items", []):
            s = item.get("statistics", {})
            stats[item["id"]] = {
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
            }
        return stats


async def get_trending_presence(artist_name: str) -> list[dict]:
    """
    Check in how many regions the artist appears in the music trending list.
    Uses YouTube trending (videoCategoryId=10 = Music).
    Cost: 1 quota unit per region (reads only), so ~20 units total.
    """
    presence = []
    artist_lower = artist_name.lower()
    async with httpx.AsyncClient(timeout=20) as client:
        for region in REGIONS:
            try:
                r = await client.get(
                    f"{BASE_URL}/videos",
                    params={
                        "key": os.environ["YOUTUBE_API_KEY"],
                        "chart": "mostPopular",
                        "videoCategoryId": "10",
                        "regionCode": region,
                        "maxResults": 50,
                        "part": "snippet",
                    },
                )
                if r.status_code != 200:
                    continue
                items = r.json().get("items", [])
                for rank, item in enumerate(items, 1):
                    snippet = item.get("snippet", {})
                    title = snippet.get("title", "").lower()
                    channel = snippet.get("channelTitle", "").lower()
                    if artist_lower in title or artist_lower in channel:
                        presence.append({
                            "region": region,
                            "rank": rank,
                            "video_title": snippet.get("title"),
                            "video_id": item["id"],
                        })
                        break
            except Exception:
                continue
    return presence


async def get_artist_youtube_summary(artist_name: str) -> dict:
    """Aggregate YouTube data for an artist: videos + stats + trending presence."""
    videos = await search_artist_videos(artist_name, max_results=5)
    video_ids = [v["video_id"] for v in videos]
    stats = await get_video_stats(video_ids)
    trending = await get_trending_presence(artist_name)

    for v in videos:
        v.update(stats.get(v["video_id"], {}))

    total_views = sum(s.get("views", 0) for s in stats.values())

    return {
        "top_videos": videos,
        "total_views_top5": total_views,
        "trending_regions": trending,
        "trending_region_count": len(trending),
    }
