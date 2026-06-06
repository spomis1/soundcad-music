# Local Setup

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (local instance or [Neon.tech](https://neon.tech) free tier)
- API keys for: Spotify, Last.fm, YouTube, Setlist.fm

---

## 1. Clone the repo

```bash
git clone https://github.com/spomis1/soundcad-music.git
cd soundcad-music
```

---

## 2. Set up the Python environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt
```

---

## 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
LASTFM_API_KEY=...
YOUTUBE_API_KEY=...
SETLISTFM_API_KEY=...
DATABASE_URL=postgresql://user:password@localhost:5432/soundcard

# Optional (not strictly needed for local dev)
TICKETMASTER_API_KEY=...
```

### Where to get each key

| Key | Where to register | Auth type |
|-----|-------------------|-----------|
| Spotify | [developer.spotify.com](https://developer.spotify.com/dashboard) → Create App | OAuth2 client credentials |
| Last.fm | [last.fm/api/account/create](https://www.last.fm/api/account/create) | API key in query params |
| YouTube | [console.cloud.google.com](https://console.cloud.google.com) → YouTube Data API v3 | API key in query params |
| Setlist.fm | [setlist.fm/settings/api](https://www.setlist.fm/settings/api) | API key in header |

MusicBrainz, Wikipedia, Deezer, and iTunes do **not** require keys.

---

## 4. Create the database

The app auto-creates its tables on startup via `init_db()`. All you need is an empty database:

```sql
-- PostgreSQL
CREATE DATABASE soundcard;
```

Or use the Neon.tech web console to create a new project and copy the connection string.

---

## 5. Start the backend

```bash
# From the backend/ directory
uvicorn main:app --reload
```

The API will be available at:
- `http://localhost:8000` — API
- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/health` — Health check

---

## 6. Open the frontend

Open `frontend/index.html` directly in your browser. The frontend auto-detects `localhost` and points to `http://localhost:8000`.

> No build step needed — it's plain HTML, CSS, and Vanilla JS.

---

## Verifying the setup

```bash
# Test the health endpoint
curl http://localhost:8000/health
# → {"status":"ok"}

# Test an artist search
curl "http://localhost:8000/api/artist/bad%20bunny" | python -m json.tool | head -20
```

---

## Common issues

**`KeyError: 'SPOTIFY_CLIENT_ID'`**  
The `.env` file wasn't loaded. Make sure you're running `uvicorn` from the `backend/` directory.

**`asyncpg: could not connect to server`**  
PostgreSQL isn't running, or the `DATABASE_URL` is wrong. Check with `psql $DATABASE_URL`.

**Empty results for some fields**  
MusicBrainz, Wikipedia, and Deezer don't require keys but occasionally time out or return no data for less-known artists. This is expected.

**YouTube quota exhausted**  
The free tier allows ~10 000 units/day (~400 new artist searches). If you hit the limit, the top videos section will be empty until midnight PST when the quota resets.
