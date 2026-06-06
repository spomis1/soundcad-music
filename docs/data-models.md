# Data Models

All models are defined in `backend/models.py` using **Pydantic v2**.  
The `ArtistResponse` model is used as the response type for `GET /api/artist/{name}`.  
Song responses are plain dicts (no Pydantic model — the schema is defined in `song_search.py`).

---

## `ArtistResponse`

Top-level response for the artist endpoint.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `name` | `str` | Spotify / Last.fm | Canonical artist name |
| `listeners` | `int` | Last.fm | Monthly unique listeners |
| `playcount` | `int` | Last.fm | All-time total plays |
| `bio` | `str` | Wikipedia | 2–3 sentence bio extract |
| `bio_summary` | `str` | Last.fm | HTML bio (not shown in UI) |
| `wiki_url` | `str` | Wikipedia | Link to the full article |
| `wiki_pageviews_30d` | `int` | Wikimedia Pageviews API | Last 30 days of page traffic |
| `tags` | `list[str]` | Spotify genres / Last.fm tags | Genre labels |
| `image_url` | `str \| None` | Spotify | Artist photo URL |
| `spotify_url` | `str \| None` | Spotify | `open.spotify.com/artist/...` |
| `itunes_url` | `str` | iTunes | Apple Music deep-link |
| `itunes_genre` | `str` | iTunes | Primary iTunes genre |
| `country_code` | `str \| None` | MusicBrainz | ISO 3166-1 alpha-2 (e.g. `"PR"`) |
| `country_name` | `str \| None` | MusicBrainz | Human-readable name |
| `country_flag` | `str \| None` | MusicBrainz | Emoji flag |
| `artist_type` | `str \| None` | MusicBrainz | `"Person"` or `"Group"` |
| `begin_year` | `str \| None` | MusicBrainz | Birth year (Person) or founding year (Group) |
| `origin_area` | `str \| None` | MusicBrainz | City / region of origin |
| `spotify_followers` | `int` | Spotify | Total follower count |
| `spotify_popularity` | `int` | Spotify | Score 0–100 |
| `spotify_market_count` | `int` | Spotify | Number of markets where tracks are available |
| `related_artists` | `list[RelatedArtist]` | Spotify (+ Last.fm fallback) | Up to 6 similar artists |
| `top_tracks` | `list[TopTrack]` | Spotify + Deezer | Top 5 tracks with previews |
| `albums` | `list[Album]` | Spotify | Full-length albums |
| `singles` | `list[Album]` | Spotify | Singles + EPs |
| `country_presence` | `list[CountryPresence]` | Spotify | Markets where tracks are available |
| `recent_concerts` | `list[Concert]` | Setlist.fm | Up to 50 most recent shows |
| `tour_timeline` | `list[TourEra]` | Setlist.fm | Grouped by tour/year |
| `upcoming_events` | `list[UpcomingEvent]` | — | Always empty (no reliable free source) |
| `top_videos` | `list[YoutubeVideo]` | YouTube | Top 5 videos from official channel |
| `total_views_top5` | `int` | YouTube | Sum of views for top-5 videos |
| `trending_regions` | `list[TrendingRegion]` | YouTube | Regional trending presence |
| `trending_region_count` | `int` | YouTube | Number of regions trending |
| `career_stats` | `CareerStats` | derived | Computed from existing data — no extra API call |
| `momentum` | `MomentumScore` | derived | Composite 0–100 industry score |
| `cached_at` | `str \| None` | internal | ISO 8601 timestamp of last cache write |

---

## `MomentumScore`

| Field | Type | Description |
|-------|------|-------------|
| `score` | `float` | 0–100 composite score |
| `label` | `str` | `"Rising"` (≥60) · `"Stable"` (35–59) · `"Declining"` (<35) |
| `factors` | `dict` | Breakdown: `followers_score`, `popularity_score`, `youtube_score`, `tour_score` |

---

## `CareerStats`

Derived metrics — computed from data already fetched, zero extra API calls.

| Field | Type | Description |
|-------|------|-------------|
| `total_shows` | `int` | Career concert count (Setlist.fm) |
| `toured_countries` | `int` | Distinct countries toured |
| `engagement_ratio` | `int` | `playcount / listeners` — measures audience depth |
| `engagement_label` | `str` | `"Cult following"` / `"Highly engaged"` / `"Solid fanbase"` / `"Casual listeners"` |
| `years_active` | `int \| None` | Only set for Groups (founding year to present) |

**Engagement ratio thresholds:**

| Ratio | Label |
|-------|-------|
| ≥ 300 | Cult following |
| ≥ 100 | Highly engaged |
| ≥ 40 | Solid fanbase |
| ≥ 10 | Casual listeners |
| < 10 | — |

---

## `TopTrack`

| Field | Type | Source |
|-------|------|--------|
| `name` | `str` | Spotify |
| `popularity` | `int` | Spotify |
| `preview_url` | `str \| None` | Deezer (Spotify deprecated previews in 2024) |
| `spotify_url` | `str \| None` | Spotify |
| `deezer_url` | `str \| None` | Deezer |
| `album_cover` | `str \| None` | Deezer |

---

## `Album`

Used for both albums and singles.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Album/single title |
| `year` | `str \| None` | 4-digit release year |
| `release_date` | `str \| None` | Full ISO date (`YYYY-MM-DD`) |
| `total_tracks` | `int \| None` | Track count |
| `image` | `str \| None` | Cover art URL |
| `album_type` | `str \| None` | `"album"`, `"single"`, `"compilation"` |
| `spotify_url` | `str \| None` | Spotify deep-link |

---

## `Concert`

| Field | Type |
|-------|------|
| `date` | `str` (ISO 8601) |
| `year` | `int \| None` |
| `venue_name` | `str \| None` |
| `city` | `str \| None` |
| `country` | `str \| None` |
| `country_code` | `str \| None` |
| `lat` / `lon` | `float` |
| `tour_name` | `str \| None` |
| `songs_count` | `int` |

---

## `TourEra`

| Field | Type | Description |
|-------|------|-------------|
| `tour` | `str` | Tour name or year (if unnamed) |
| `start_date` | `str` | ISO 8601 |
| `end_date` | `str` | ISO 8601 |
| `show_count` | `int` | Number of shows |
| `countries` | `list[str]` | Countries visited |

---

## Song response schema

Song searches return a plain dict (not a Pydantic model). Fields:

| Field | Type | Source |
|-------|------|--------|
| `name` | `str` | Spotify |
| `artist_name` | `str` | Spotify |
| `all_artists` | `list[str]` | Spotify (feat. artists) |
| `artist_spotify_url` | `str \| None` | Spotify |
| `album_name` | `str` | Spotify |
| `cover` | `str \| None` | Spotify |
| `year` | `str` | Spotify |
| `popularity` | `int` | Spotify (0–100) |
| `preview_url` | `str \| None` | Spotify |
| `spotify_url` | `str \| None` | Spotify |
| `lastfm_listeners` | `int` | Last.fm |
| `lastfm_playcount` | `int` | Last.fm |
| `tags` | `list[str]` | Last.fm |
| `similar_tracks` | `list[dict]` | Last.fm |
| `samples_used` | `list[dict]` | MusicBrainz |
| `sampled_by` | `list[dict]` | MusicBrainz |
| `interpolations` | `list[dict]` | MusicBrainz |
| `mb_url` | `str` | MusicBrainz |

Each sample entry: `{ "name": str, "artist": str, "year": str }`
