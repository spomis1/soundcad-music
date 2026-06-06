# Services

Each file in `backend/services/` wraps a single external API. All functions are `async` and use `httpx.AsyncClient`.

---

## `spotify.py`

**Auth:** OAuth2 client credentials (`SPOTIFY_CLIENT_ID` + `SPOTIFY_CLIENT_SECRET`).  
Token is cached in module-level globals and refreshed ~60 s before expiry.

| Function | Description |
|----------|-------------|
| `_get_token()` | Returns a valid bearer token; refreshes automatically |
| `search_artist(name)` | Finds an artist on Spotify; returns the raw artist object or `None` |
| `get_artist_data(name)` | Full artist data: followers, popularity, genres, image, top tracks, related artists, albums, singles, country presence |

**Country presence** is derived from the `available_markets` field of the artist's top tracks — not a direct API field. The 50+ country codes are mapped to human-readable names locally.

**Album split logic:**  
- Full album = `album_type == "album"` AND `total_tracks > 1`  
- Everything else (singles, EPs, `total_tracks == 1`) goes into the `singles` list

---

## `lastfm.py`

**Auth:** `LASTFM_API_KEY` passed as a query parameter on every request.

| Function | Description |
|----------|-------------|
| `get_artist_info(artist_name)` | Listener count, total playcount, bio summary, tags |
| `get_similar_artists(artist_name)` | Up to 6 related artists (used as Spotify fallback) |
| `get_top_artists_global(limit)` | Top-N global artists — used by the cache refresh script |
| `get_artist_top_countries(artist_name)` | Checks top-50 charts for 20 countries (slow — not used in main flow) |

---

## `musicbrainz.py`

**Auth:** None. MusicBrainz is a free, open API.  
**Rate limit:** 1 request / second. The app adds a `User-Agent` header as required by MusicBrainz policy.

| Function | Description |
|----------|-------------|
| `get_artist_metadata(artist_name, canonical_name)` | Returns `country_code`, `country_name`, `country_flag`, `artist_type`, `begin_year`, `origin_area` |

**Matching logic** (3-pass):
1. Normalised exact name match + score ≥ 85
2. Normalised exact name match (any score)
3. Highest-score result only if score ≥ 90

This avoids false matches for artists with short or common names.

---

## `song_search.py` — MusicBrainz sample lookup

`get_musicbrainz_samples(title, artist)` performs **two sequential** MusicBrainz calls (rate-limited):

```
Step 1: GET /ws/2/recording?query=recording:"title" AND artist:"artist"
        → get the recording MBID (highest-scored result)
Step 2: GET /ws/2/recording/{mbid}?inc=recording-rels+artist-credits
        → get all recording relationships
```

Relationship types handled:

| MB type | Direction | Maps to |
|---------|-----------|---------|
| `samples material` | forward | `samples_used` (this song samples another) |
| `samples material` | backward | `sampled_by` (another song sampled this) |
| `has samples` | backward | `samples_used` |
| `has samples` | forward | `sampled_by` |
| `interpolates` | any | `interpolations` |

---

## `youtube.py`

**Auth:** `YOUTUBE_API_KEY` passed as a query param.  
**Quota cost:** ~50–60 units per artist search (channel lookup + video search + stats).

| Function | Description |
|----------|-------------|
| `_find_artist_channel(artist_name, client)` | Searches for the official channel by name, handles VEVO / Oficial / Official suffixes |
| `search_artist_videos(artist_name, max_results)` | Returns top videos by view count from the official channel; falls back to keyword search |
| `get_video_stats(video_ids)` | Batch-fetches view/like counts for up to 50 video IDs |
| `get_trending_presence(artist_name)` | Checks 20 regional trending charts; counts how many regions the artist appears in |
| `get_artist_youtube_summary(artist_name)` | Combines all of the above into a single dict |

**Channel matching** strips common suffixes (`vevo`, `oficial`, `official`, `music`, `records`) and uses normalised substring comparison.

---

## `wikipedia.py`

**Auth:** None. Uses the Wikipedia REST API and Wikimedia pageviews API.

`get_artist_wikipedia(artist_name, canonical_name)` tries titles in order:
1. Canonical name (with accents, from Spotify)
2. Original query
3. `"Name (musician)"`, `"Name (singer)"`, `"Name (rapper)"`, `"Name (band)"`, `"Name (artist)"`
4. ASCII-stripped fallback
5. Spanish Wikipedia fallback

A "music sanity check" verifies the article description/extract contains at least one music keyword before accepting a match — avoids returning a Wikipedia page for a politician named "Drake".

Bio is truncated to 3 sentences or 420 characters.

---

## `setlistfm.py`

**Auth:** `SETLISTFM_API_KEY` passed as `x-api-key` header.

| Function | Description |
|----------|-------------|
| `search_artist(artist_name)` | Returns the MusicBrainz ID for the artist on Setlist.fm |
| `get_setlists(artist_name, max_pages=5)` | Fetches up to 5 pages of setlists (~100 shows), returns sorted by date |
| `build_tour_timeline(setlists)` | Groups shows by tour name and year; returns a sorted list of `TourEra` objects |

Dates from Setlist.fm are in `DD-MM-YYYY` format and converted to ISO 8601 (`YYYY-MM-DD`).

---

## `deezer.py`

**Auth:** None. Deezer's public search API is open.

Searches for the artist by name, then fetches their top tracks with 30-second preview URLs. Used as an enrichment layer on top of Spotify tracks (which deprecated preview URLs in 2024).

---

## `itunes.py`

**Auth:** None. iTunes Search API is open.

Searches for the artist in the iTunes catalog and returns the Apple Music deep-link URL and primary genre. Simple lookup, no complex parsing needed.
