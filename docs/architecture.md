# Architecture

## System overview

```
Browser (GitHub Pages)
        │
        │  HTTPS — REST JSON
        ▼
FastAPI backend (Render.com)
        │
        ├── PostgreSQL (Neon.tech) ── cache hit? → return immediately
        │      artist_cache  (7-day TTL)
        │      song_cache    (7-day TTL)
        │
        └── External APIs  (asyncio.gather — all in parallel)
               ├── Spotify       followers, popularity, top tracks, discography, related
               ├── Last.fm       playcount, listeners, similar artists / tracks
               ├── YouTube       official channel videos + view counts
               ├── Wikipedia     bio extract + 30-day pageviews
               ├── MusicBrainz   country, artist type, sample relationships
               ├── Setlist.fm    full tour history (paginated)
               ├── Deezer        30-second audio previews
               └── iTunes        Apple Music deep-link
```

**First search:** ~3–6 s (all APIs hit in parallel)  
**Repeat search (same query within 7 days):** ~200 ms (PostgreSQL cache)

---

## Repository layout

```
artist-radar/
├── backend/
│   ├── main.py                  # FastAPI app, endpoints, cache logic, scores
│   ├── models.py                # Pydantic response models
│   ├── requirements.txt
│   ├── runtime.txt              # Python 3.11
│   ├── render.yaml              # Render.com service config
│   ├── railway.toml             # Railway (alternative deploy)
│   ├── .env.example
│   ├── services/
│   │   ├── spotify.py           # OAuth2 client-credentials + artist data
│   │   ├── lastfm.py            # Artist info, similar artists, charts
│   │   ├── musicbrainz.py       # Country/type metadata + sample relationships
│   │   ├── youtube.py           # Channel lookup, video stats, trending
│   │   ├── wikipedia.py         # Bio extract + pageview metrics
│   │   ├── setlistfm.py         # Tour history + timeline builder
│   │   ├── deezer.py            # 30-sec preview URLs
│   │   ├── itunes.py            # Apple Music link
│   │   ├── song_search.py       # Song mode: Spotify + Last.fm + MusicBrainz
│   │   └── ticketmaster.py      # (deprecated — kept for reference)
│   └── scripts/
│       └── refresh_cache.py     # Batch pre-warm for top artists
├── frontend/
│   ├── index.html               # Single-page app shell
│   ├── app.js                   # All UI logic (Vanilla JS, ~1 600 lines)
│   └── style.css                # CSS variables + dark/light mode
├── .github/
│   └── workflows/
│       ├── deploy-pages.yml     # Auto-deploy frontend on push to master
│       └── refresh-cache.yml    # Scheduled cache pre-warm (weekly)
└── docs/                        # ← you are here
```

---

## Data flow — artist search

```
1. User types "Bad Bunny" → app.js calls GET /api/artist/bad+bunny
2. Backend normalises key: "bad bunny" (strip + lowercase)
3. Check artist_cache WHERE name_lower = 'bad bunny'
   └── Hit + age < 7 days → return JSONB directly (~200 ms)
   └── Miss or stale:
       4a. asyncio.gather(
             get_artist_info(),       # Last.fm
             get_setlists(),          # Setlist.fm
             get_artist_youtube_summary(), # YouTube (3 API calls internally)
             get_spotify_data(),      # Spotify (3 API calls internally)
             get_similar_artists(),   # Last.fm fallback
             get_top_tracks_with_preview() # Deezer
           )
       4b. get_artist_metadata()      # MusicBrainz (needs canonical name from Spotify)
       4c. asyncio.gather(
             get_artist_wikipedia(),  # Wikipedia + Pageviews API
             get_itunes_data()        # iTunes
           )
       5. compute_momentum()          # derived score, no API call
       6. compute_career_stats()      # derived stats, no API call
       7. UPSERT into artist_cache
       8. Return JSON response
```

---

## Data flow — song search

```
1. User types "Blinding Lights" → GET /api/song/blinding+lights
2. Check song_cache WHERE query_lower = 'blinding lights'
   └── Hit → return cached
   └── Miss:
       3. search_track_spotify(query)   # find track metadata
       4. asyncio.gather(
            get_lastfm_track_info(),    # playcount, listeners, tags
            get_lastfm_similar_tracks(),# similar songs
            get_musicbrainz_samples()   # sample DNA (2 sequential MB calls)
          )
       5. UPSERT into song_cache
       6. Return JSON
```

---

## Caching strategy

| Table | Primary key | TTL | Invalidation |
|-------|-------------|-----|--------------|
| `artist_cache` | `name_lower TEXT` | 7 days | `DELETE /api/cache/{artist}` |
| `song_cache` | `query_lower TEXT` | 7 days | manual SQL |

Both tables use `JSONB` for the payload — schema changes don't require migrations.  
The `cached_at TIMESTAMPTZ` column drives TTL checks at read time; no background job deletes rows.

---

## Momentum Score formula

```python
score = (
    min(spotify_followers / 50_000_000, 1.0) * 30   # 30 pts max
  + (spotify_popularity / 100)              * 30   # 30 pts max
  + min(youtube_top5_views / 500_000_000, 1.0) * 20 # 20 pts max
  + min(latest_tour_shows / 50, 1.0)        * 20   # 20 pts max
)

label = "Rising"   if score >= 60
        "Stable"   if score >= 35
        "Declining" otherwise
```

---

## Concurrency model

The backend is fully async (`asyncio` + `httpx.AsyncClient`).  
`asyncpg` provides non-blocking PostgreSQL access.  
Under Render's free tier (512 MB RAM, 1 shared CPU), the app handles 3–5 concurrent searches comfortably.
