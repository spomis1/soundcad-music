import os
import httpx
from datetime import datetime, timedelta, timezone

BASE_URL = "https://www.googleapis.com/youtube/v3"

# ISO 3166-1 alpha-2 codes for the regions we check
REGIONS = [
    "US", "GB", "DE", "BR", "FR", "MX", "AR", "ES", "AU", "CA",
    "JP", "KR", "IT", "NL", "PL", "SE", "RU", "TR", "IN", "ID",
]


async def search_artist_videos(artist_name: str, max_results: int = 10) -> list[dict]:
    """Search for the artist's most recent music videos on YouTube."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{BASE_URL}/search",
            params={
                "key": os.environ["YOUTUBE_API_KEY"],
                "q": f"{artist_name} official music video",
                "type": "video",
                "videoCategoryId": "10",  # Music category
                "order": "relevance",
                "maxResults": max_results,
                "part": "snippet",
            },
        )
        if r.status_code != 200:
            return []
        items = r.json().get("items", [])
        return [
            {
                "video_id": i["id"]["videoId"],
                "title": i["snippet"]["title"],
                "published_at": i["snippet"]["publishedAt"],
                "thumbnail": i["snippet"]["thumbnails"].get("medium", {}).get("url"),
                "channel": i["snippet"]["channelTitle"],
            }
            for i in items
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
