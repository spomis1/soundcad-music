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
from services.setlistfm import get_setlists, build_tour_timeline
from services.ticketmaster import get_upcoming_events as get_upcoming_ticketmaster
from services.bandsintown import get_upcoming_events as get_upcoming_bandsintown
from services.youtube import get_artist_youtube_summary
from services.spotify import get_artist_data as get_spotify_data
from models import ArtistResponse, MomentumScore

# ---------------------------------------------------------------------------
# Event quality filter
# ---------------------------------------------------------------------------

def _ascii(s: str) -> str:
    """Lowercase + strip accents for fuzzy comparison."""
    return unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode().strip()


# Keywords that indicate a themed night / tribute / club event (not real concert)
_TRIBUTE_KW = frozenset([
    "night", "tribute", "party", "fiesta", "bash", "takeover",
    "vs.", " vs ", "dance party", "latin night", "reggaeton night",
    "dj set", "dj night", "open bar", "brunch", "day party",
    "halloween", "christmas", "new year", "nye", "pride",
])

# Minimum estimated venue capacity expected by Spotify popularity tier
_POP_MIN_CAPACITY = [
    (90, 8_000),   # popularity ≥ 90 → stadium/arena (8k+)
    (75, 2_000),   # popularity ≥ 75 → theater/large club (2k+)
    (60, 500),     # popularity ≥ 60 → mid-size venue (500+)
]


def _is_real_event(ev: dict, artist_name: str, popularity: int) -> bool:
    """
    Heuristic filter to remove tribute nights / themed club events.
    Returns True if the event is likely a real artist performance.
    """
    title = ev.get("name", "")
    norm_title = _ascii(title)
    norm_artist = _ascii(artist_name)

    # 1. Reject tribute/themed nights by title keywords
    if norm_title.startswith(norm_artist):
        suffix = norm_title[len(norm_artist):].strip(" -:")
        if any(kw in suffix for kw in _TRIBUTE_KW):
            return False
    elif any(kw in norm_title for kw in _TRIBUTE_KW):
        return False

    # 2. Capacity sanity check — always runs regardless of title match.
    #    Popular artists simply don't play tiny venues.
    cap = ev.get("estimated_capacity", 1_000)
    for min_pop, min_cap in _POP_MIN_CAPACITY:
        if popularity >= min_pop and cap < min_cap:
            return False

    return True


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
    spotify_followers: int,
    spotify_popularity: int,
    upcoming_count: int,
    tour_timeline: list[dict],
) -> MomentumScore:
    """
    Composite score 0-100 based on:
    - Spotify followers (50M = full score, max 30 pts)
    - Spotify popularity 0-100 (max 30 pts)
    - Upcoming shows scheduled (5+ = full score, max 20 pts)
    - Recent tour activity: show count in latest tour (50+ = full score, max 20 pts)
    """
    followers_score = min(spotify_followers / 50_000_000, 1.0) * 30   # max 30 pts
    popularity_score = (spotify_popularity / 100) * 30                  # max 30 pts
    upcoming_score = min(upcoming_count / 5, 1.0) * 20                  # max 20 pts

    tour_score = 0.0
    if tour_timeline:
        latest = tour_timeline[-1]
        show_count = latest.get("show_count", 0)
        tour_score = min(show_count / 50, 1.0) * 20                    # max 20 pts

    total = followers_score + popularity_score + upcoming_score + tour_score

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
            "followers_score": round(followers_score, 1),
            "popularity_score": round(popularity_score, 1),
            "upcoming_score": round(upcoming_score, 1),
            "tour_score": round(tour_score, 1),
        },
    )


# ---------------------------------------------------------------------------
# Core data fetching
# ---------------------------------------------------------------------------

async def fetch_artist_data(artist_name: str) -> dict:
    info, setlists, tm_events, bit_events, yt, spotify, similar_lfm = await asyncio.gather(
        get_artist_info(artist_name),
        get_setlists(artist_name),
        get_upcoming_ticketmaster(artist_name),
        get_upcoming_bandsintown(artist_name),
        get_artist_youtube_summary(artist_name),
        get_spotify_data(artist_name),
        get_similar_artists(artist_name),
    )

    # MusicBrainz after Spotify so we can pass the canonical name (handles accents)
    canonical = spotify.get("name") or artist_name
    popularity = spotify.get("popularity", 0)   # needed for event quality filter
    mb = await get_artist_metadata(artist_name, canonical_name=canonical)

    # Merge events: Bandsintown first (global) + Ticketmaster (US pricing/links)
    # When same date+city appears in both, BIT wins (more global), but we patch
    # the ticket_url and pricing from TM if BIT doesn't have them.
    def _event_key(e: dict) -> str:
        return f"{e['date']}|{(e['city'] or '').lower()}"

    # Index TM events for enrichment lookup
    tm_by_key: dict[str, dict] = {}
    for ev in tm_events:
        tm_by_key[_event_key(ev)] = ev

    seen_keys: set[str] = set()
    upcoming = []
    for ev in sorted(bit_events + tm_events, key=lambda e: e["date"]):
        k = _event_key(ev)
        if k in seen_keys:
            continue
        seen_keys.add(k)
        # Enrich BIT event with TM pricing/ticket_url if available
        if k in tm_by_key and not ev.get("ticket_url"):
            tm_ev = tm_by_key[k]
            ev["ticket_url"] = tm_ev.get("ticket_url") or ev.get("ticket_url")
            ev["min_price"] = tm_ev.get("min_price") or ev.get("min_price")
            ev["max_price"] = tm_ev.get("max_price") or ev.get("max_price")
            ev["currency"] = tm_ev.get("currency") or ev.get("currency", "USD")
        # Filter out tribute nights and themed club events
        if _is_real_event(ev, canonical, popularity):
            upcoming.append(ev)
    upcoming = upcoming[:20]
    tour_timeline = build_tour_timeline(setlists)

    # Spotify is primary source; Last.fm fills gaps
    name = spotify.get("name") or info.get("name", artist_name)
    image_url = spotify.get("image_url") or info.get("image_url")
    tags = spotify.get("genres") or info.get("tags", [])
    country_presence = spotify.get("country_presence", [])
    followers = spotify.get("followers", 0)
    popularity = spotify.get("popularity", 0)
    market_count = spotify.get("market_count", 0)

    # Related artists: Spotify (deprecated in 2024) → Last.fm fallback
    related_artists = spotify.get("related_artists") or similar_lfm

    momentum = compute_momentum(
        spotify_followers=followers,
        spotify_popularity=popularity,
        upcoming_count=len(upcoming),
        tour_timeline=tour_timeline,
    )
    return {
        "name": name,
        "listeners": info.get("listeners", 0),
        "playcount": info.get("playcount", 0),
        "bio_summary": info.get("bio_summary", ""),
        "tags": tags,
        "image_url": image_url,
        # MusicBrainz
        "country_code": mb.get("country_code"),
        "country_name": mb.get("country_name"),
        "country_flag": mb.get("country_flag"),
        "artist_type": mb.get("artist_type"),
        "begin_year": mb.get("begin_year"),
        "origin_area": mb.get("origin_area"),
        # Spotify
        "spotify_followers": followers,
        "spotify_popularity": popularity,
        "spotify_market_count": market_count,
        "related_artists": related_artists,
        "top_tracks": spotify.get("top_tracks", []),
        "albums": spotify.get("albums", []),
        "singles": spotify.get("singles", []),
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
