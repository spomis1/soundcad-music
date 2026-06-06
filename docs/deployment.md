# Deployment

SoundCard uses a split deployment: frontend on **GitHub Pages** (free), backend on **Render.com** (free or paid tier).

---

## Frontend — GitHub Pages

Deployment is **automatic** via GitHub Actions whenever you push changes to `frontend/**` on the `master` branch.

Workflow file: `.github/workflows/deploy-pages.yml`

```
push to master (frontend/** changed)
      │
      ▼
GitHub Actions: actions/upload-pages-artifact
      │         (uploads the /frontend folder)
      ▼
GitHub Pages CDN
      │
      ▼
https://spomis1.github.io/soundcad-music/
```

**Manual trigger:** Go to Actions → "Deploy Frontend to GitHub Pages" → "Run workflow".

### First-time setup

1. Go to your repo → Settings → Pages
2. Source: **GitHub Actions**
3. Push any change to `frontend/` to trigger the first deploy

---

## Backend — Render.com

Config file: `backend/render.yaml`

### First-time deploy

```bash
# 1. Create an account at render.com
# 2. New → Web Service → connect your GitHub repo
# 3. Set the following:
#    Root directory: backend
#    Build command:  pip install -r requirements.txt
#    Start command:  uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Environment variables (set in Render dashboard)

```
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
LASTFM_API_KEY
YOUTUBE_API_KEY
SETLISTFM_API_KEY
DATABASE_URL          # from Neon.tech (see Database section below)
```

### Tiers

| Tier | Cost | Cold start | RAM |
|------|------|-----------|-----|
| Free | $0 | ~30 s after 15 min idle | 512 MB |
| Starter | $7/mo | None (always on) | 512 MB |
| Standard | $25/mo | None | 2 GB |

> The free tier sleeps after 15 minutes of inactivity. The first request of the day wakes it up (~30 s). Upgrading to Starter eliminates this.

---

## Database — Neon.tech

Neon provides a serverless PostgreSQL on a free tier (500 MB).

1. Create an account at [neon.tech](https://neon.tech)
2. New project → copy the connection string
3. Paste into `DATABASE_URL` in Render's environment variables

The tables (`artist_cache`, `song_cache`) are created automatically on first startup — no manual migrations needed.

---

## Alternative backend deploy — Railway

Config file: `backend/railway.toml`

```bash
npm install -g @railway/cli
railway login
cd backend
railway up
```

Railway's free tier includes 500 hours/month of runtime and doesn't sleep.

---

## Cache pre-warm — GitHub Actions (weekly)

Workflow: `.github/workflows/refresh-cache.yml`

Runs weekly to pre-populate the cache with the global top-100 artists from Last.fm. This ensures users searching for popular artists always get sub-200ms responses.

The script (`backend/scripts/refresh_cache.py`) hits the backend's own `/api/artist/{name}` endpoint sequentially, which populates the PostgreSQL cache.

---

## Connecting frontend to backend

In `frontend/app.js`, the `API_BASE` constant is set automatically:

```js
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://soundcad-music.onrender.com';
```

If you deploy the backend to a different URL (Railway, etc.), update the production URL in this line and push to trigger a frontend redeploy.

---

## Monitoring

- **Backend health:** `https://soundcad-music.onrender.com/health`
- **Render logs:** Render dashboard → your service → Logs tab
- **GitHub Actions:** repository → Actions tab
- **Database usage:** Neon.tech dashboard → Storage metric
