import asyncio
import json
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

from services.lastfm import get_artist_info
from services.setlistfm import get_setlists, build_tour_timeline
from services.ticketmaster import get_upcoming_events
from services.youtube import get_artist_youtube_summary
from services.spotify import get_artist_data as get_spotify_data
from models import ArtistResponse, MomentumScore

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    return _pool


async def init_db(pool: asyncpg.Pool) -> None:
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS artist_cache (
            name_lower TEXT PRIMARY KEY,
            data       JSONB NOT NULL,
            cached_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await get_pool()
    await init_db(pool)
    yield
    await pool.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="ArtistRadar API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

CACHE_TTL_DAYS = 7


# ---------------------------------------------------------------------------
# Momentum calculation
# ---------------------------------------------------------------------------

def compute_momentum(
    listeners: int,
    country_count: int,
    tour_timeline: list[dict],
    trending_region_count: int,
) -> MomentumScore:
    """
    Simple composite score 0-100 based on:
    - Global listener count (normalized)
    - Number of countries with presence
    - Venue size trend across tours (growing = better)
    - YouTube trending regions
    """
    listener_score = min(listeners / 5_000_000, 1.0) * 30      # max 30 pts
    country_score = min(country_count / 20, 1.0) * 20           # max 20 pts
    youtube_score = min(trending_region_count / 10, 1.0) * 25   # max 25 pts

    # Tour activity: recent tours score higher
    tour_score = 0.0
    if tour_timeline:
        latest = tour_timeline[-1]
        show_count = latest.get("show_count", 0)
        tour_score = min(show_count / 50, 1.0) * 25             # max 25 pts

    total = listener_score + country_score + youtube_score + tour_score

    if total >= 60:
        label = "Rising"
    elif total >= 35:
        label = "Stable"
    else:
        label = "Declining"

    return MomentumScore(
        score=round(total, 1),
        label=label,
        factors={
            "listener_score": round(listener_score, 1),
            "country_score": round(country_score, 1),
            "youtube_score": round(youtube_score, 1),
            "tour_score": round(tour_score, 1),
        },
    )


# ---------------------------------------------------------------------------
# Core data fetching
# ---------------------------------------------------------------------------

async def fetch_artist_data(artist_name: str) -> dict:
    info, setlists, upcoming, yt, spotify = await asyncio.gather(
        get_artist_info(artist_name),
        get_setlists(artist_name),
        get_upcoming_events(artist_name),
        get_artist_youtube_summary(artist_name),
        get_spotify_data(artist_name),
    )
    tour_timeline = build_tour_timeline(setlists)

    # Spotify is primary source; Last.fm fills gaps
    name = spotify.get("name") or info.get("name", artist_name)
    image_url = spotify.get("image_url") or info.get("image_url")
    tags = spotify.get("genres") or info.get("tags", [])
    country_presence = spotify.get("country_presence", [])
    followers = spotify.get("followers", 0)
    popularity = spotify.get("popularity", 0)
    market_count = spotify.get("market_count", 0)

    momentum = compute_momentum(
        listeners=info.get("listeners", 0),
        country_count=market_count,
        tour_timeline=tour_timeline,
        trending_region_count=yt.get("trending_region_count", 0),
    )
    return {
        "name": name,
        "listeners": info.get("listeners", 0),
        "playcount": info.get("playcount", 0),
        "bio_summary": info.get("bio_summary", ""),
        "tags": tags,
        "image_url": image_url,
        "spotify_followers": followers,
        "spotify_popularity": popularity,
        "spotify_market_count": market_count,
        "related_artists": spotify.get("related_artists", []),
        "top_tracks": spotify.get("top_tracks", []),
        "country_presence": country_presence,
        "recent_concerts": setlists[:50],
        "tour_timeline": tour_timeline,
        "upcoming_events": upcoming,
        "top_videos": yt.get("top_videos", []),
        "trending_regions": yt.get("trending_regions", []),
        "trending_region_count": yt.get("trending_region_count", 0),
        "total_views_top5": yt.get("total_views_top5", 0),
        "momentum": momentum.model_dump(),
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/debug/env")
async def debug_env():
    return {
        "SPOTIFY_CLIENT_ID": bool(os.getenv("SPOTIFY_CLIENT_ID")),
        "SPOTIFY_CLIENT_SECRET": bool(os.getenv("SPOTIFY_CLIENT_SECRET")),
        "LASTFM_API_KEY": bool(os.getenv("LASTFM_API_KEY")),
    }


@app.get("/api/artist/{artist_name}", response_model=ArtistResponse)
async def get_artist(artist_name: str):
    pool = await get_pool()
    key = artist_name.strip().lower()

    # Try cache first
    row = await pool.fetchrow(
        "SELECT data, cached_at FROM artist_cache WHERE name_lower = $1", key
    )
    if row:
        age_days = (datetime.now(timezone.utc) - row["cached_at"]).days
        if age_days < CACHE_TTL_DAYS:
            return json.loads(row["data"])

    # Fetch fresh
    try:
        data = await fetch_artist_data(artist_name.strip())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")

    # Upsert cache
    await pool.execute(
        """
        INSERT INTO artist_cache (name_lower, data, cached_at)
        VALUES ($1, $2, NOW())
        ON CONFLICT (name_lower) DO UPDATE
            SET data = EXCLUDED.data, cached_at = EXCLUDED.cached_at
        """,
        key,
        json.dumps(data),
    )
    return data


@app.get("/api/top-artists")
async def top_artists():
    """Returns cached artist names for autocomplete."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT data->>'name' as name FROM artist_cache ORDER BY (data->>'listeners')::int DESC LIMIT 100"
    )
    return [r["name"] for r in rows]


@app.get("/health")
async def health():
    return {"status": "ok"}
