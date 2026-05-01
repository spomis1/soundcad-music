# ArtistRadar 🌍

**Music Industry Intelligence Dashboard** — search any artist and instantly see how they're performing in the real world: where their fans are, their complete touring history, upcoming shows, YouTube trending presence, and a composite Momentum Score.

> Built as a portfolio project by Sebastian Pomi. Data powered by Last.fm, Setlist.fm, Ticketmaster Discovery API, and YouTube Data API v3.

---

## What it shows

| Feature | Data Source |
|---|---|
| Fan concentration map (by country) | Last.fm |
| Full touring history + tour eras timeline | Setlist.fm |
| Upcoming shows with ticket links | Ticketmaster |
| YouTube trending presence by region | YouTube Data API v3 |
| Momentum Score (0–100) | Composite |

---

## Architecture

```
Frontend (GitHub Pages)
  └── Vanilla HTML + Chart.js + Leaflet.js

Backend (Railway ~$5/month)
  └── Python + FastAPI
  └── PostgreSQL (cache layer, TTL 7 days)

Automation (GitHub Actions — free)
  └── Weekly job refreshes top 100 artists in DB
```

---

## Getting started locally

### 1. Get API keys (all free)

| Service | URL | Notes |
|---|---|---|
| Last.fm | https://www.last.fm/api/account/create | Instant, no review |
| Setlist.fm | https://api.setlist.fm/docs/1.0/ | Same-day approval |
| Ticketmaster | https://developer.ticketmaster.com | Instant |
| YouTube | https://console.cloud.google.com → YouTube Data API v3 | Needs Google account |

### 2. Backend setup

```bash
cd backend
cp .env.example .env
# Fill in your keys in .env

pip install -r requirements.txt
uvicorn main:app --reload
# API running at http://localhost:8000
```

### 3. Frontend

Just open `frontend/index.html` in your browser.  
It auto-detects localhost and points to `http://localhost:8000`.

---

## Deploy

### Backend → Railway

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Select the `backend/` folder as root
4. Add PostgreSQL plugin
5. Set environment variables (same as `.env`)
6. Railway auto-detects FastAPI and deploys

### Frontend → GitHub Pages

1. Push repo to GitHub
2. Settings → Pages → Source: `/ (root)` or `frontend/` folder
3. Update `API_BASE` in `frontend/app.js` with your Railway URL
4. Done — live at `https://yourusername.github.io/artist-radar`

### GitHub Actions secrets

Add these in repo Settings → Secrets → Actions:

```
LASTFM_API_KEY
SETLISTFM_API_KEY
TICKETMASTER_API_KEY
YOUTUBE_API_KEY
DATABASE_URL
```

---

## Momentum Score

Composite 0–100 score:

| Factor | Max points |
|---|---|
| Global listener count | 30 |
| Countries with chart presence | 20 |
| YouTube trending regions | 25 |
| Tour activity (recent show count) | 25 |

**Rising** ≥ 60 · **Stable** 35–59 · **Declining** < 35

---

## Scalability roadmap

- **v2**: User login → analyze your own Spotify listening history and compare it to global trends
- **v3**: Artist "watchlists" + email alerts when an artist announces a show in a region
- **v4**: White-label API for promoters and A&R scouts
- **v5**: Freemium — basic data free, historical data + alerts on paid plan ($9/month)

---

## Tech stack

- Python 3.11, FastAPI, asyncpg, httpx, Pydantic v2
- Vanilla JS, Chart.js 4, Leaflet.js 1.9
- PostgreSQL on Railway
- GitHub Pages + GitHub Actions
