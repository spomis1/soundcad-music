# SoundCard Music — Documentation

Music Intelligence App · Beta · [Live demo](https://spomis1.github.io/soundcad-music/)

---

## Contents

| Document | What's inside |
|----------|---------------|
| [Architecture](./architecture.md) | System diagram, data flow, caching strategy, Momentum Score formula |
| [API Reference](./api-reference.md) | All endpoints, request/response examples, rate limits |
| [Services](./services.md) | Each external API integration documented (Spotify, Last.fm, YouTube, MusicBrainz, Setlist.fm, Wikipedia, Deezer, iTunes) |
| [Data Models](./data-models.md) | All Pydantic models with field-level docs and data sources |
| [Setup](./setup.md) | Local development — Python env, database, API keys |
| [Deployment](./deployment.md) | GitHub Pages (frontend), Render.com (backend), Neon.tech (PostgreSQL) |

---

## Quick reference

```
GET  /api/artist/{name}   → full artist profile (cached 7 days)
GET  /api/song/{query}    → track info + Sample DNA (cached 7 days)
GET  /api/top-artists     → cached artists for autocomplete
GET  /api/top-songs       → cached songs for autocomplete
DEL  /api/cache/{artist}  → invalidate artist cache
GET  /health              → server status
```

```
Stack:
  Backend   Python 3.11 · FastAPI · asyncpg · httpx · Pydantic v2
  Database  PostgreSQL (Neon.tech free tier)
  Frontend  Vanilla JS · CSS variables · no frameworks
  Deploy    Render.com (backend) · GitHub Pages (frontend)
  CI/CD     GitHub Actions
```
