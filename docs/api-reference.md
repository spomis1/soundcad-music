# API Reference

Base URL (production): `https://soundcad-music.onrender.com`  
Base URL (local): `http://localhost:8000`

Interactive docs (Swagger UI): `{base_url}/docs`

---

## Endpoints

### `GET /api/artist/{artist_name}`

Returns a full artist profile. Results are cached for 7 days.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `artist_name` | string | Artist name (URL-encoded). Case-insensitive. |

**Example**

```
GET /api/artist/bad%20bunny
GET /api/artist/the%20beatles
```

**Response** — `200 OK`

```jsonc
{
  "name": "Bad Bunny",
  "listeners": 8431200,
  "playcount": 680000000,
  "bio": "Bad Bunny is a Puerto Rican singer, rapper, and actor...",
  "wiki_url": "https://en.wikipedia.org/wiki/Bad_Bunny",
  "wiki_pageviews_30d": 412000,
  "tags": ["reggaeton", "latin trap", "urban"],
  "image_url": "https://i.scdn.co/image/...",
  "spotify_url": "https://open.spotify.com/artist/...",
  "itunes_url": "https://music.apple.com/artist/...",
  "country_code": "PR",
  "country_name": "Puerto Rico",
  "country_flag": "🇵🇷",
  "artist_type": "Person",
  "begin_year": "1994",
  "origin_area": "Vega Baja",
  "spotify_followers": 45000000,
  "spotify_popularity": 97,
  "related_artists": [
    { "name": "J Balvin", "popularity": 88 }
  ],
  "top_tracks": [
    {
      "name": "Tití Me Preguntó",
      "popularity": 95,
      "preview_url": "https://cdns-preview-....dzcdn.net/stream/...",
      "spotify_url": "https://open.spotify.com/track/...",
      "album_cover": "https://e-cdns-images.dzcdn.net/images/..."
    }
  ],
  "albums": [
    {
      "name": "Un Verano Sin Ti",
      "year": "2022",
      "total_tracks": 23,
      "image": "https://i.scdn.co/image/...",
      "album_type": "album",
      "spotify_url": "https://open.spotify.com/album/..."
    }
  ],
  "singles": [ ... ],
  "top_videos": [
    {
      "video_id": "GX3iAMmkAkk",
      "title": "Bad Bunny - Tití Me Preguntó",
      "published_at": "2022-06-10T12:00:00Z",
      "thumbnail": "https://i.ytimg.com/vi/.../mqdefault.jpg",
      "views": 890000000,
      "likes": 3200000
    }
  ],
  "total_views_top5": 2400000000,
  "tour_timeline": [
    {
      "tour": "El Último Tour del Mundo",
      "start_date": "2022-02-05",
      "end_date": "2022-06-19",
      "show_count": 48,
      "countries": ["United States", "Puerto Rico", "Mexico"]
    }
  ],
  "career_stats": {
    "total_shows": 180,
    "toured_countries": 12,
    "engagement_ratio": 80,
    "engagement_label": "Solid fanbase",
    "years_active": null
  },
  "momentum": {
    "score": 88.4,
    "label": "Rising",
    "factors": {
      "followers_score": 27.0,
      "popularity_score": 29.1,
      "youtube_score": 9.6,
      "tour_score": 19.2
    }
  },
  "cached_at": "2024-11-20T14:32:00+00:00"
}
```

**Error responses**

| Status | Condition |
|--------|-----------|
| `502 Bad Gateway` | One or more upstream APIs returned an error |

---

### `GET /api/song/{song_name}`

Returns track info, stats, and Sample DNA. Results are cached for 7 days.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `song_name` | string | Song title, optionally including artist name. |

**Example**

```
GET /api/song/titi%20me%20pregunto
GET /api/song/blinding%20lights%20the%20weeknd
```

**Response** — `200 OK`

```jsonc
{
  "name": "Blinding Lights",
  "artist_name": "The Weeknd",
  "all_artists": ["The Weeknd"],
  "artist_spotify_url": "https://open.spotify.com/artist/...",
  "album_name": "After Hours",
  "cover": "https://i.scdn.co/image/...",
  "year": "2019",
  "popularity": 88,
  "preview_url": "https://p.scdn.co/mp3-preview/...",
  "spotify_url": "https://open.spotify.com/track/...",
  "lastfm_listeners": 3200000,
  "lastfm_playcount": 180000000,
  "tags": ["synthwave", "80s", "pop"],
  "similar_tracks": [
    { "name": "Save Your Tears", "artist": "The Weeknd", "playcount": 80000000 }
  ],
  "samples_used": [
    { "name": "Take On Me", "artist": "a-ha", "year": "1985" }
  ],
  "sampled_by": [],
  "interpolations": [],
  "mb_url": "https://musicbrainz.org/recording/..."
}
```

**Error responses**

| Status | Condition |
|--------|-----------|
| `404 Not Found` | Song not found on Spotify |
| `502 Bad Gateway` | Upstream API error |

---

### `GET /api/top-artists`

Returns a list of artist names from the cache, sorted by Last.fm listeners descending. Used for autocomplete suggestions.

**Response** — `200 OK`

```json
["Bad Bunny", "Taylor Swift", "Drake", "The Weeknd"]
```

---

### `GET /api/top-songs`

Returns recently cached song names and their artist. Used for autocomplete suggestions in Song mode.

**Response** — `200 OK`

```json
[
  { "name": "Blinding Lights", "artist": "The Weeknd" },
  { "name": "Tití Me Preguntó", "artist": "Bad Bunny" }
]
```

---

### `DELETE /api/cache/{artist_name}`

Manually invalidates the cache for an artist. Useful during development or when data looks stale.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `artist_name` | string | Artist name (case-insensitive). |

**Example**

```
DELETE /api/cache/bad%20bunny
```

**Response** — `200 OK`

```json
{ "deleted": true, "key": "bad bunny" }
```

---

### `GET /health`

Health check endpoint used by Render.com's monitoring.

**Response** — `200 OK`

```json
{ "status": "ok" }
```

---

## Rate limits

SoundCard does not enforce its own rate limits. The bottleneck is upstream APIs:

| API | Free tier limit |
|-----|----------------|
| YouTube Data API v3 | 10 000 units / day (~400 new artist searches) |
| MusicBrainz | 1 request / second (enforced via `asyncio.sleep(1.1)`) |
| Setlist.fm | ~2 req/sec (soft limit) |
| Spotify | No strict limit under normal usage |
| Last.fm | No strict limit under normal usage |

---

## CORS

The API allows all origins (`*`) with `GET` and `DELETE` methods only. This is intentional — the app is publicly accessible and read-only.
