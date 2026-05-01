"""
Weekly cache refresh job — run by GitHub Actions.
Fetches top 100 global artists from Last.fm and pre-warms the DB cache.
"""
import asyncio
import json
import os
import sys

# Make sure backend/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncpg
from services.lastfm import get_top_artists_global, get_artist_info, get_artist_top_countries
from services.setlistfm import get_setlists, build_tour_timeline
from services.ticketmaster import get_upcoming_events
from services.youtube import get_artist_youtube_summary


async def compute_momentum(listeners, country_count, tour_timeline, trending_count):
    listener_score = min(listeners / 5_000_000, 1.0) * 30
    country_score  = min(country_count / 20, 1.0) * 20
    youtube_score  = min(trending_count / 10, 1.0) * 25
    tour_score = 0.0
    if tour_timeline:
        tour_score = min(tour_timeline[-1].get("show_count", 0) / 50, 1.0) * 25
    total = listener_score + country_score + youtube_score + tour_score
    label = "Rising" if total >= 60 else ("Stable" if total >= 35 else "Declining")
    return {"score": round(total, 1), "label": label,
            "factors": {"listener_score": round(listener_score, 1),
                        "country_score": round(country_score, 1),
                        "youtube_score": round(youtube_score, 1),
                        "tour_score": round(tour_score, 1)}}


async def refresh_artist(pool: asyncpg.Pool, artist_name: str) -> None:
    print(f"  → {artist_name}...", end=" ", flush=True)
    try:
        info, setlists, upcoming, yt = await asyncio.gather(
            get_artist_info(artist_name),
            get_setlists(artist_name, max_pages=3),
            get_upcoming_events(artist_name),
            get_artist_youtube_summary(artist_name),
        )
        country_presence = await get_artist_top_countries(artist_name)
        tour_timeline    = build_tour_timeline(setlists)
        momentum         = await compute_momentum(
            info.get("listeners", 0),
            len(country_presence),
            tour_timeline,
            yt.get("trending_region_count", 0),
        )
        from datetime import datetime, timezone
        data = {
            "name": info.get("name", artist_name),
            "listeners": info.get("listeners", 0),
            "playcount": info.get("playcount", 0),
            "bio_summary": info.get("bio_summary", ""),
            "tags": info.get("tags", []),
            "image_url": info.get("image_url"),
            "country_presence": country_presence,
            "recent_concerts": setlists[:50],
            "tour_timeline": tour_timeline,
            "upcoming_events": upcoming,
            "top_videos": yt.get("top_videos", []),
            "trending_regions": yt.get("trending_regions", []),
            "trending_region_count": yt.get("trending_region_count", 0),
            "total_views_top5": yt.get("total_views_top5", 0),
            "momentum": momentum,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        await pool.execute(
            """
            INSERT INTO artist_cache (name_lower, data, cached_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (name_lower) DO UPDATE
                SET data = EXCLUDED.data, cached_at = EXCLUDED.cached_at
            """,
            artist_name.lower(),
            json.dumps(data),
        )
        print("✓")
    except Exception as e:
        print(f"✗ {e}")


async def main():
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS artist_cache (
            name_lower TEXT PRIMARY KEY,
            data       JSONB NOT NULL,
            cached_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    print("Fetching top artists from Last.fm...")
    artists = await get_top_artists_global(limit=100)
    print(f"Found {len(artists)} artists. Starting refresh...\n")

    # Process in batches of 5 to avoid hammering APIs
    for i in range(0, len(artists), 5):
        batch = artists[i : i + 5]
        await asyncio.gather(*(refresh_artist(pool, a) for a in batch))
        await asyncio.sleep(2)  # be polite to rate limits

    await pool.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
