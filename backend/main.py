import asyncio
import json
import os
import unicodedata
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

from services.lastfm import get_artist_info, get_similar_artists
from services.musicbrainz import get_artist_metadata
from services.deezer import get_top_tracks_with_preview
from services.setlistfm import get_setlists, build_tour_timeline
from services.youtube import get_artist_youtube_summary
from services.spotify import get_artist_data as get_spotify_data
from services.wikipedia import get_artist_wikipedia
from services.itunes import get_itunes_data
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

app = FastAPI(title="SoundCard Music API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "DELETE"],
    allow_headers=["*"],
)

CACHE_TTL_DAYS = 7


# ---------------------------------------------------------------------------
# Momentum calculation (v2 — no longer needs upcoming shows)
# ---------------------------------------------------------------------------

def compute_momentum(
    spotify_followers: int,
    spotify_popularity: int,
    total_views_top5: int,
    tour_timeline: list[dict],
) -> MomentumScore:
    """
    Composite score 0-100:
    - Spotify followers   (50M = full, max 30 pts)
    - Spotify popularity  (0-100,      max 30 pts)
    - YouTube top-5 views (500M = full, max 20 pts)
    - Recent tour activity latest tour show count (50+ = full, max 20 pts)
    """
    followers_score  = min(spotify_followers / 50_000_000, 1.0) * 30
    popularity_score = (spotify_popularity / 100) * 30
    youtube_score    = min(total_views_top5 / 500_000_000, 1.0) * 20

    tour_score = 0.0
    if tour_timeline:
        latest = tour_timeline[-1]
        tour_score = min(latest.get("show_count", 0) / 50, 1.0) * 20

    total = followers_score + popularity_score + youtube_score + tour_score

    label = "Rising" if total >= 60 else "Stable" if total >= 35 else "Declining"

    return MomentumScore(
        score=round(total, 1),
        label=label,
        factors={
            "followers_score":  round(followers_score, 1),
            "popularity_score": round(popularity_score, 1),
            "youtube_score":    round(youtube_score, 1),
            "tour_score":       round(tour_score, 1),
        },
    )


# ---------------------------------------------------------------------------
# Career stats (derived, no extra API calls)
# ---------------------------------------------------------------------------

def compute_career_stats(
    tour_timeline: list[dict],
    listeners: int,
    playcount: int,
    begin_year: str | None,
    artist_type: str | None = None,
) -> dict:
    """
    Derived industry metrics — all computed from data we already have.
    """
    # Total career shows and countries from setlist.fm tour data
    total_shows = sum(t.get("show_count", 0) for t in tour_timeline)
    toured_countries = len({c for t in tour_timeline for c in t.get("countries", [])})

    # Engagement ratio: average plays per unique listener (Last.fm)
    # High ratio (200+) = cult following. Low (<30) = casual / radio audience.
    engagement = round(playcount / max(listeners, 1)) if playcount and listeners else 0

    if engagement >= 300:
        engagement_label = "Cult following"
    elif engagement >= 100:
        engagement_label = "Highly engaged"
    elif engagement >= 40:
        engagement_label = "Solid fanbase"
    elif engagement >= 10:
        engagement_label = "Casual listeners"
    else:
        engagement_label = "—"

    # Years active — only meaningful for groups (begin_year = founding year).
    # For solo artists, begin_year = birth year, so we skip it.
    years_active = None
    if begin_year and str(begin_year).isdigit() and artist_type == "Group":
        years_active = datetime.now().year - int(begin_year)

    return {
        "total_shows": total_shows,
        "toured_countries": toured_countries,
        "engagement_ratio": engagement,
        "engagement_label": engagement_label,
        "years_active": years_active,
    }


# ---------------------------------------------------------------------------
# Core data fetching
# ---------------------------------------------------------------------------

async def fetch_artist_data(artist_name: str) -> dict:
    # Run all independent API calls in parallel
    (
        info, setlists, yt, spotify, similar_lfm, deezer_tracks
    ) = await asyncio.gather(
        get_artist_info(artist_name),
        get_setlists(artist_name),
        get_artist_youtube_summary(artist_name),
        get_spotify_data(artist_name),
        get_similar_artists(artist_name),
        get_top_tracks_with_preview(artist_name),
    )

    # Use canonical name (with accents) for downstream lookups
    canonical = spotify.get("name") or artist_name
    popularity = spotify.get("popularity", 0)

    # MusicBrainz after Spotify so we can pass the canonical name
    mb = await get_artist_metadata(artist_name, canonical_name=canonical)

    # Wikipedia + iTunes can also use the canonical name
    wiki, itunes = await asyncio.gather(
        get_artist_wikipedia(artist_name, canonical_name=canonical),
        get_itunes_data(canonical),
    )

    tour_timeline = build_tour_timeline(setlists)

    # ── Merge data ────────────────────────────────────────────────────────────

    name        = spotify.get("name") or info.get("name", artist_name)
    image_url   = spotify.get("image_url") or info.get("image_url")
    tags        = spotify.get("genres") or info.get("tags", [])
    followers   = spotify.get("followers", 0)
    market_count = spotify.get("market_count", 0)

    # Related artists: Spotify → Last.fm fallback
    related_artists = spotify.get("related_artists") or similar_lfm

    # Top tracks: Spotify + Deezer preview enrichment
    sp_tracks  = spotify.get("top_tracks", [])
    dz_by_name = {t["name"].lower(): t for t in deezer_tracks}
    top_tracks = []
    for t in sp_tracks:
        dz = dz_by_name.get(t["name"].lower(), {})
        top_tracks.append({
            "name":        t["name"],
            "popularity":  t.get("popularity", 0),
            "preview_url": t.get("preview_url") or dz.get("preview_url"),
            "spotify_url": t.get("spotify_url"),
            "deezer_url":  dz.get("deezer_url"),
            "album_cover": dz.get("album_cover"),
        })
    if not top_tracks and deezer_tracks:
        top_tracks = deezer_tracks

    # YouTube
    total_views_top5 = yt.get("total_views_top5", 0)

    # Scores
    listeners  = info.get("listeners", 0)
    playcount  = info.get("playcount", 0)

    momentum = compute_momentum(
        spotify_followers=followers,
        spotify_popularity=popularity,
        total_views_top5=total_views_top5,
        tour_timeline=tour_timeline,
    )

    career_stats = compute_career_stats(
        tour_timeline=tour_timeline,
        listeners=listeners,
        playcount=playcount,
        begin_year=mb.get("begin_year"),
        artist_type=mb.get("artist_type"),
    )

    return {
        "name": name,
        "listeners": listeners,
        "playcount": playcount,
        "bio_summary": info.get("bio_summary", ""),
        "bio": wiki.get("bio", ""),
        "wiki_url": wiki.get("wiki_url", ""),
        "wiki_pageviews_30d": wiki.get("wiki_pageviews_30d", 0),
        "tags": tags,
        "image_url": image_url,
        "spotify_url": spotify.get("spotify_url"),
        "itunes_url": itunes.get("itunes_url", ""),
        "itunes_genre": itunes.get("itunes_genre", ""),
        # MusicBrainz
        "country_code":  mb.get("country_code"),
        "country_name":  mb.get("country_name"),
        "country_flag":  mb.get("country_flag"),
        "artist_type":   mb.get("artist_type"),
        "begin_year":    mb.get("begin_year"),
        "origin_area":   mb.get("origin_area"),
        # Spotify
        "spotify_followers":   followers,
        "spotify_popularity":  popularity,
        "spotify_market_count": market_count,
        "related_artists": related_artists,
        "top_tracks":  top_tracks,
        "albums":      spotify.get("albums", []),
        "singles":     spotify.get("singles", []),
        "country_presence": spotify.get("country_presence", []),
        # Tour / setlists
        "recent_concerts": setlists[:50],
        "tour_timeline":   tour_timeline,
        "upcoming_events": [],          # removed — no reliable free source
        # YouTube
        "top_videos":           yt.get("top_videos", []),
        "trending_regions":     yt.get("trending_regions", []),
        "trending_region_count": yt.get("trending_region_count", 0),
        "total_views_top5":     total_views_top5,
        # Career stats (derived)
        "career_stats": career_stats,
        # Momentum
        "momentum": momentum.model_dump(),
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/artist/{artist_name}", response_model=ArtistResponse)
async def get_artist(artist_name: str):
    pool = await get_pool()
    key = artist_name.strip().lower()

    row = await pool.fetchrow(
        "SELECT data, cached_at FROM artist_cache WHERE name_lower = $1", key
    )
    if row:
        age_days = (datetime.now(timezone.utc) - row["cached_at"]).days
        if age_days < CACHE_TTL_DAYS:
            cached = json.loads(row["data"])
            # If cached data is from old schema (missing new fields), force refresh
            if "career_stats" in cached and "bio" in cached:
                return cached
            # else fall through to re-fetch with new schema

    try:
        data = await fetch_artist_data(artist_name.strip())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")

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


@app.delete("/api/cache/{artist_name}")
async def clear_cache(artist_name: str):
    """Manually invalidate cache for an artist (useful during development)."""
    pool = await get_pool()
    key = artist_name.strip().lower()
    result = await pool.execute(
        "DELETE FROM artist_cache WHERE name_lower = $1", key
    )
    deleted = result.split()[-1] != "0"
    return {"deleted": deleted, "key": key}


@app.get("/api/top-artists")
async def top_artists():
    """Returns cached artist names for autocomplete."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT data->>'name' as name FROM artist_cache ORDER BY (data->>'listeners')::bigint DESC LIMIT 100"
    )
    return [r["name"] for r in rows]


@app.get("/api/song/{song_name}")
async def get_song(song_name: str):
    """Search for a song by name (and optionally artist, e.g. 'blinding lights the weeknd')."""
    from services.song_search import get_song_data
    try:
        data = await get_song_data(song_name.strip())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Song API error: {e}")
    if not data:
        raise HTTPException(status_code=404, detail="Song not found")
    return data


@app.get("/health")
async def health():
    return {"status": "ok"}
