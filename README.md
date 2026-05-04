# SoundCard Music 🎵

> **Beta pública gratuita** — Music Intelligence Dashboard para artistas y canciones.

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-soundcard--music-7c3aed?style=for-the-badge)](https://spomis1.github.io/soundcad-music/)
[![Status](https://img.shields.io/badge/status-beta-f59e0b?style=for-the-badge)](https://spomis1.github.io/soundcad-music/)
[![Backend](https://img.shields.io/badge/backend-render.com-22c55e?style=for-the-badge)](https://soundcad-music.onrender.com/health)
[![Built by](https://img.shields.io/badge/built_by-Sebastian_Pomi-6d28d9?style=for-the-badge)](https://github.com/spomis1)

---

## 🔗 Demo en vivo

**[https://spomis1.github.io/soundcad-music/](https://spomis1.github.io/soundcad-music/)**

> ⚠️ El servidor corre en el **free tier de Render.com**, que entra en modo sleep después de 15 minutos de inactividad. El primer request del día puede tardar ~30 segundos en despertar. A partir de ahí responde instantáneamente.

---

## ¿Qué es SoundCard?

SoundCard es un dashboard de inteligencia musical que agrega datos de **8 APIs en tiempo real** para dar un perfil completo de cualquier artista o canción. Está pensado como alternativa open source y accesible a herramientas de industria como Chartmetric (~$150/mes) o Soundcharts (~$80/mes).

Dos modos de búsqueda:

- **🎤 Artist** — perfil completo del artista
- **🎵 Song** — info de la canción + Sample DNA

---

## 🎤 Dashboard de Artistas

### Header del artista
- Foto, nombre, géneros
- Origen: país 🇵🇷, tipo (solista / grupo), año de fundación o nacimiento
- Links directos a Spotify y Apple Music

### Stats principales
| Stat | Fuente |
|------|--------|
| Spotify Followers | Spotify |
| Total Plays | Last.fm |
| Wikipedia / mes | Wikipedia Pageviews API |
| Álbumes | Spotify |

### Industry Presence — Momentum Score
Score compuesto 0–100 que mide la relevancia global actual del artista:

| Factor | Peso |
|--------|------|
| Spotify Followers (escala hasta 50M) | 30 pts |
| Spotify Popularity (0–100) | 30 pts |
| YouTube top-5 views (escala hasta 500M) | 20 pts |
| Historial de giras — shows en última gira | 20 pts |

**Rising** ≥ 60 · **Stable** 35–59 · **Declining** < 35

### Career Stats
Métricas de industria derivadas de los datos existentes — sin llamadas extra a APIs:
- Plays por fan (ratio Last.fm: engagement cult vs. casual)
- Países girados (Setlist.fm)
- Shows totales en carrera (Setlist.fm)
- Años activos (MusicBrainz, solo para grupos)
- YouTube top-5 views acumulados

### Secciones del dashboard
- **Biografía** — Wikipedia, con link al artículo
- **Top Tracks** — 5 canciones más populares (Spotify) con preview de 30s (Deezer) y link a Spotify
- **Top Videos en YouTube** — del canal oficial verificado, con views
- **Discografía** — álbumes completos separados de singles, links a Spotify, expand/collapse
- **Singles & EPs** — ordenados por fecha, links individuales a Spotify
- **Similar Artists** — Spotify relacionados + fallback de Last.fm, clickeables

---

## 🎵 Dashboard de Canciones

### Header de la canción
- Portada del álbum, título, artistas, nombre del álbum, año
- Preview de 30 segundos (Spotify)
- Link a Spotify

### Stats
- Popularidad en Spotify (0–100)
- Reproducciones totales en Last.fm
- Oyentes únicos en Last.fm

### 🎛 Sample DNA
Relaciones de samples extraídas de **MusicBrainz**:
- **⬇ Esta canción samplea** — de dónde vienen los samples usados
- **🎼 Interpolaciones** — melodías tomadas de otras canciones
- **⬆ Ha sido sampleada por** — quién usó esta canción después

> Cobertura especialmente buena en hip-hop clásico (Kanye, Jay-Z, Dilla, ATCQ). Para reggaeton y pop reciente la base de datos de MusicBrainz tiene menos datos porque depende de contribuciones comunitarias.

### Canciones similares
Lista de tracks relacionados desde Last.fm, clickeables para explorar en cadena.

---

## ⚙️ Cómo funciona

```
Usuario
  │
  ▼
Frontend (GitHub Pages)
  │  Vanilla JS — sin frameworks
  │  Dark / Light mode
  │  URL params: ?artist=bad+bunny | ?song=blinding+lights
  │
  ▼
Backend (Render.com — Python + FastAPI)
  │
  ├─► Cache PostgreSQL (Neon.tech) ── ¿Está en caché? → respuesta inmediata
  │     TTL: 7 días por artista / canción
  │
  └─► APIs externas (en paralelo con asyncio.gather)
        ├── Spotify       → followers, popularidad, tracks, discografía
        ├── Last.fm       → plays, oyentes, tags, similares
        ├── YouTube       → videos del canal oficial, views
        ├── Wikipedia     → bio, pageviews mensuales
        ├── MusicBrainz   → país, tipo de artista, samples
        ├── Setlist.fm    → historial completo de giras
        ├── Deezer        → previews de 30s
        └── Apple Music   → link al artista en iTunes
```

**Primera búsqueda:** ~3–6 segundos (todas las APIs en paralelo)  
**Segunda búsqueda del mismo artista:** ~200ms (caché PostgreSQL)

---

## 🛠 Stack técnico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11 + FastAPI + asyncpg + httpx + Pydantic v2 |
| Base de datos | PostgreSQL en Neon.tech (free tier — 500MB) |
| Frontend | Vanilla JS + CSS variables — sin frameworks |
| Deploy backend | Render.com (free tier) |
| Deploy frontend | GitHub Pages (gratis) |
| CI/CD | GitHub Actions |

---

## 🚀 Setup local

### 1. Clonar y configurar entorno

```bash
git clone https://github.com/spomis1/soundcad-music.git
cd soundcad-music/backend
pip install -r requirements.txt
cp .env.example .env
# Completar las keys en .env
```

### 2. Variables de entorno necesarias

```env
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
LASTFM_API_KEY=...
YOUTUBE_API_KEY=...
SETLISTFM_API_KEY=...
DATABASE_URL=postgresql://...
```

### 3. Levantar backend

```bash
uvicorn main:app --reload
# Corre en http://localhost:8000
# Docs en http://localhost:8000/docs
```

### 4. Frontend

Abrir `frontend/index.html` en el browser. Auto-detecta localhost y apunta a `http://localhost:8000`.

---

## 📡 API Endpoints

```
GET  /api/artist/{name}     → perfil completo del artista (con caché)
GET  /api/song/{query}      → info de la canción + samples (con caché)
GET  /api/top-artists       → artistas en caché para autocomplete
GET  /api/top-songs         → canciones en caché para autocomplete
DEL  /api/cache/{artist}    → invalidar caché manualmente
GET  /health                → status del servidor
```

---

## 🌟 UX Features

- 🌙 / ☀️ Dark & Light mode con persistencia en localStorage
- 🔍 Autocomplete con artistas y canciones ya buscados
- 🔗 URLs compartibles: `?artist=bad+bunny` o `?song=titi+me+pregunto`
- 📤 Share button — copia el link al portapapeles
- ⚠️ Empty state — avisa cuando un artista tiene poca data disponible
- 📱 Diseño responsive mobile-first
- ⬅️ Back / Forward del browser funciona correctamente

---

---

## 💰 Hoja de ruta con financiamiento

### ¿Qué pasa con $0/mes? (situación actual — Beta)

La app funciona con infraestructura 100% gratuita. Las limitaciones son:

| Limitación | Impacto |
|-----------|---------|
| Render free tier duerme 15min sin uso | Primer request del día tarda ~30s |
| Neon.tech free: 500MB storage | Suficiente para ~10.000 artistas cacheados |
| YouTube API: 10.000 unidades/día | ~400 búsquedas de artistas nuevos por día |
| Setlist.fm: rate limit estricto | Ocasionalmente lento |
| MusicBrainz: 1 req/seg | Agrega ~1s de latencia en modo Song |
| WhoSampled: sin API pública | Samples limitados a MusicBrainz |
| Sin eventos en vivo confiables | Ticketmaster/Songkick sin integración completa |

---

### 🥉 Tier Starter — $50–80/mes

**Objetivo:** que la app funcione sin fricciones para uso real y demos.

| Servicio | Costo/mes | Qué resuelve |
|---------|-----------|-------------|
| Render.com Starter | $25 | Sin sleep — respuesta inmediata siempre |
| Neon.tech Pro (10GB) | $19 | 10x más artistas cacheados, backups |
| Dominio propio (ej. soundcard.music) | $1.5 | Presencia profesional |
| **Total** | **~$46/mes** | |

**Resultado esperado:**
- App siempre activa, sin espera de 30s
- Caché para 100.000+ artistas y canciones
- URL propia para portfolio y demos
- Base sólida para primeros usuarios reales

---

### 🥈 Tier Growth — $300–500/mes

**Objetivo:** convertirlo en una herramienta útil para managers, promotores y A&R.

| Servicio | Costo/mes | Qué agrega |
|---------|-----------|-----------|
| Render.com Standard | $85 | Más RAM, 0 downtime deploys |
| Neon.tech Pro | $69 | Alta disponibilidad, read replicas |
| **Songkick API** | ~$100–200 | Eventos en vivo globales (mucho mejor que Ticketmaster solo) |
| **Chartmetric API** | ~$100 | Chart history (Spotify, Apple Music, Billboard), social stats |
| Redis (Upstash) | $10 | Cache en memoria — respuesta en <50ms |
| Dominio + email profesional | $15 | hello@soundcard.music |
| **Total** | **~$380–480/mes** | |

**Resultado esperado:**
- Datos de charts históricos (Spotify Global, Billboard, Apple Music)
- Eventos en vivo confiables en todos los mercados
- Dashboard actualizado diariamente (no solo 7 días de caché)
- Suficiente para primeros 200–500 usuarios activos mensuales
- Base para empezar a monetizar con un plan freemium

---

### 🥇 Tier Scale — $1.500–3.000/mes

**Objetivo:** producto comercial real, competidor directo de Chartmetric/Soundcharts.

| Servicio | Costo/mes | Qué agrega |
|---------|-----------|-----------|
| Infraestructura dedicada (AWS/GCP) | $400–600 | Alta disponibilidad, auto-scaling |
| **WhoSampled API partnership** | $500–1.000 | La mejor base de datos de samples del mundo |
| **Luminate / MRC Data** | $800+ | Datos de radio, streaming certificados, charts pro |
| Songkick + Ticketmaster | $200 | Cobertura completa de eventos globales |
| Sendgrid (emails de alerta) | $20 | Notificaciones "artista anunció gira en tu ciudad" |
| Dev part-time | — | Para mantener y crecer el producto |
| **Total** | **~$1.500–3.000/mes** | |

**Resultado esperado:**
- Cobertura de samples tan buena o mejor que WhoSampled
- Charts certificados Billboard, Spotify, Apple Music con histórico
- Alertas de eventos por artista y región
- Sistema de usuarios con planes freemium / pro ($15–50/mes por usuario)
- Con 200 usuarios pagos a $15/mes → $3.000/mes de ingresos (break even)
- Con 500 usuarios pagos a $20/mes → $10.000/mes → escalable

---

### 📊 Resumen de proyección

```
$0/mes      → Beta funcional. Portfolio sólido. 
              ~400 búsquedas nuevas/día antes del límite de YouTube.

$50/mes     → Producto profesional sin fricciones.
              Ideal para demos, entrevistas y primeros usuarios.

$400/mes    → Herramienta real para la industria.
              Charts + eventos + cache diario.
              Puede monetizarse a partir de ~30 usuarios pagos.

$1.500/mes  → Competidor directo de Chartmetric.
              Break-even con ~100 usuarios a $15/mes.
              Escalable a $10K+/mes con 500 usuarios.
```

> **Contexto:** Chartmetric factura ~$150/mes por artista, Soundcharts ~$80/mes. El mercado existe y está dispuesto a pagar. SoundCard podría posicionarse como la opción accesible para managers y artistas independientes que no pueden pagar $150/mes.

---

## 👤 Autor

**Sebastian Pomi** — Data Engineer, Buenos Aires  
[GitHub](https://github.com/spomis1) · [LinkedIn](https://linkedin.com/in/sebastianpomi)

---

*SoundCard Music — Beta pública gratuita. Los datos son de uso informativo y provienen de APIs públicas de terceros.*
