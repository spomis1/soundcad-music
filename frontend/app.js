// ── Config ──────────────────────────────────────────────────────────────────
// Change this to your Railway backend URL when deployed.
const _h = window.location.hostname;
const API_BASE = (_h === "localhost" || _h === "" || _h === "127.0.0.1")
  ? "http://localhost:8000"
  : "https://YOUR-RAILWAY-APP.up.railway.app";  // replace after deploy

// ── Demo data (works offline, no backend needed) ─────────────────────────────
const DEMO_DATA = {
  "the weeknd": {
    name: "The Weeknd", listeners: 12400000, playcount: 890000000,
    tags: ["pop", "r&b", "hip-hop", "soul", "synthpop"],
    image_url: "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png",
    country_presence: [
      { country: "United States", rank: 1, listeners: 4200000 },
      { country: "United Kingdom", rank: 2, listeners: 1800000 },
      { country: "Brazil", rank: 3, listeners: 1200000 },
      { country: "Germany", rank: 4, listeners: 900000 },
      { country: "France", rank: 5, listeners: 780000 },
      { country: "Canada", rank: 2, listeners: 1100000 },
      { country: "Australia", rank: 6, listeners: 650000 },
      { country: "Mexico", rank: 4, listeners: 820000 },
      { country: "Spain", rank: 7, listeners: 540000 },
      { country: "Argentina", rank: 5, listeners: 610000 },
    ],
    recent_concerts: [
      { date: "2024-03-15", venue_name: "Rogers Centre", city: "Toronto", country: "Canada", lat: 43.6, lon: -79.4, tour_name: "After Hours Til Dawn" },
      { date: "2024-02-28", venue_name: "Rose Bowl Stadium", city: "Los Angeles", country: "United States", lat: 34.1, lon: -118.2, tour_name: "After Hours Til Dawn" },
      { date: "2023-11-05", venue_name: "Wembley Stadium", city: "London", country: "United Kingdom", lat: 51.5, lon: -0.3, tour_name: "After Hours Til Dawn" },
      { date: "2023-10-20", venue_name: "Stade de France", city: "Paris", country: "France", lat: 48.9, lon: 2.4, tour_name: "After Hours Til Dawn" },
      { date: "2023-09-10", venue_name: "Estadio GNP Seguros", city: "Mexico City", country: "Mexico", lat: 19.3, lon: -99.2, tour_name: "After Hours Til Dawn" },
      { date: "2023-08-01", venue_name: "Allianz Arena", city: "Munich", country: "Germany", lat: 48.2, lon: 11.6, tour_name: "After Hours Til Dawn" },
    ],
    tour_timeline: [
      { tour: "Kiss Land Tour", start_date: "2013-09-01", end_date: "2013-11-30", show_count: 18, countries: ["US", "CA", "UK"] },
      { tour: "Beauty Behind the Madness", start_date: "2015-10-01", end_date: "2016-02-28", show_count: 34, countries: ["US", "CA", "UK", "AU", "FR"] },
      { tour: "Starboy: Legend of the Fall", start_date: "2017-02-01", end_date: "2017-05-30", show_count: 41, countries: ["US", "CA", "UK", "DE", "FR", "AU"] },
      { tour: "After Hours Tour", start_date: "2022-01-14", end_date: "2022-09-09", show_count: 65, countries: ["US", "CA", "UK", "DE", "FR", "AU", "MX", "BR"] },
      { tour: "After Hours Til Dawn", start_date: "2023-07-08", end_date: "2024-04-01", show_count: 89, countries: ["US", "CA", "UK", "DE", "FR", "AU", "MX", "BR", "AR", "ES"] },
    ],
    upcoming_events: [
      { name: "The Weeknd - Hurry Up Tomorrow Tour", date: "2025-06-14", venue_name: "Allegiant Stadium", city: "Las Vegas", country: "United States", estimated_capacity: 65000, min_price: 89, max_price: 450, currency: "USD", ticket_url: "https://www.ticketmaster.com", lat: 36.09, lon: -115.18 },
      { name: "The Weeknd - Hurry Up Tomorrow Tour", date: "2025-06-21", venue_name: "SoFi Stadium", city: "Inglewood", country: "United States", estimated_capacity: 70000, min_price: 95, max_price: 520, currency: "USD", ticket_url: "https://www.ticketmaster.com", lat: 33.95, lon: -118.33 },
      { name: "The Weeknd - Hurry Up Tomorrow Tour", date: "2025-07-05", venue_name: "Wembley Stadium", city: "London", country: "United Kingdom", estimated_capacity: 90000, min_price: 75, max_price: 400, currency: "GBP", ticket_url: "https://www.ticketmaster.com", lat: 51.55, lon: -0.28 },
      { name: "The Weeknd - Hurry Up Tomorrow Tour", date: "2025-07-19", venue_name: "Stade de France", city: "Paris", country: "France", estimated_capacity: 80000, min_price: 70, max_price: 380, currency: "EUR", ticket_url: "https://www.ticketmaster.com", lat: 48.92, lon: 2.36 },
    ],
    top_videos: [
      { video_id: "XXYlFuWEuKI", title: "Blinding Lights (Official Video)", published_at: "2019-11-29", thumbnail: "https://i.ytimg.com/vi/XXYlFuWEuKI/mqdefault.jpg", views: 820000000, likes: 7200000 },
      { video_id: "4NRXx6U8ABQ", title: "Save Your Tears (Official Music Video)", published_at: "2020-11-05", thumbnail: "https://i.ytimg.com/vi/4NRXx6U8ABQ/mqdefault.jpg", views: 590000000, likes: 5100000 },
      { video_id: "ZTM8EHEV77w", title: "Starboy ft. Daft Punk (Official Video)", published_at: "2016-10-27", thumbnail: "https://i.ytimg.com/vi/ZTM8EHEV77w/mqdefault.jpg", views: 680000000, likes: 6000000 },
    ],
    trending_regions: [
      { region: "US", rank: 3, video_title: "Blinding Lights" },
      { region: "GB", rank: 7, video_title: "Blinding Lights" },
      { region: "CA", rank: 2, video_title: "Starboy" },
      { region: "BR", rank: 5, video_title: "Save Your Tears" },
      { region: "FR", rank: 11, video_title: "Blinding Lights" },
      { region: "AU", rank: 8, video_title: "Blinding Lights" },
    ],
    trending_region_count: 6, total_views_top5: 2090000000,
    momentum: { score: 84.5, label: "Rising", factors: { followers_score: 30, popularity_score: 27, upcoming_score: 20, tour_score: 7.5 } },
    cached_at: "2025-05-01T00:00:00Z",
  },
  "bad bunny": {
    name: "Bad Bunny", listeners: 14800000, playcount: 1200000000,
    tags: ["reggaeton", "latin trap", "latin pop", "urbano", "perreo"],
    image_url: "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png",
    country_presence: [
      { country: "United States", rank: 1, listeners: 5100000 },
      { country: "Mexico", rank: 1, listeners: 3200000 },
      { country: "Argentina", rank: 1, listeners: 2100000 },
      { country: "Spain", rank: 1, listeners: 1800000 },
      { country: "Colombia", rank: 1, listeners: 1500000 },
      { country: "Brazil", rank: 4, listeners: 900000 },
      { country: "Germany", rank: 8, listeners: 600000 },
      { country: "France", rank: 9, listeners: 550000 },
    ],
    recent_concerts: [
      { date: "2024-08-10", venue_name: "Estadio Monumental", city: "Buenos Aires", country: "Argentina", lat: -34.5, lon: -58.5, tour_name: "Most Wanted Tour" },
      { date: "2024-07-20", venue_name: "Foro Sol", city: "Mexico City", country: "Mexico", lat: 19.4, lon: -99.1, tour_name: "Most Wanted Tour" },
      { date: "2024-06-15", venue_name: "MetLife Stadium", city: "East Rutherford", country: "United States", lat: 40.8, lon: -74.1, tour_name: "Most Wanted Tour" },
      { date: "2023-10-05", venue_name: "Estadio Santiago Bernabéu", city: "Madrid", country: "Spain", lat: 40.4, lon: -3.7, tour_name: "El Último Tour del Mundo" },
    ],
    tour_timeline: [
      { tour: "La Nueva Religion Tour", start_date: "2019-02-01", end_date: "2019-04-30", show_count: 22, countries: ["US", "MX", "AR", "ES"] },
      { tour: "El Último Tour del Mundo", start_date: "2022-02-10", end_date: "2022-08-20", show_count: 52, countries: ["US", "MX", "AR", "ES", "CO", "PE"] },
      { tour: "World's Hottest Tour", start_date: "2022-07-01", end_date: "2022-10-15", show_count: 48, countries: ["US", "MX", "AR", "ES", "PR", "CO"] },
      { tour: "Most Wanted Tour", start_date: "2024-02-01", end_date: "2024-09-30", show_count: 71, countries: ["US", "MX", "AR", "ES", "CO", "BR", "DE", "FR"] },
    ],
    upcoming_events: [
      { name: "Bad Bunny Live", date: "2025-08-02", venue_name: "Estadio Azteca", city: "Mexico City", country: "Mexico", estimated_capacity: 87000, min_price: 65, max_price: 350, currency: "USD", ticket_url: "https://www.ticketmaster.com", lat: 19.3, lon: -99.15 },
      { name: "Bad Bunny Live", date: "2025-08-16", venue_name: "Hard Rock Stadium", city: "Miami", country: "United States", estimated_capacity: 65000, min_price: 80, max_price: 420, currency: "USD", ticket_url: "https://www.ticketmaster.com", lat: 25.9, lon: -80.2 },
    ],
    top_videos: [
      { video_id: "iocm8oQS4Z4", title: "Titi Me Preguntó (Video Oficial)", published_at: "2022-05-06", thumbnail: "https://i.ytimg.com/vi/iocm8oQS4Z4/mqdefault.jpg", views: 620000000, likes: 4800000 },
      { video_id: "GtSRCCUkxoo", title: "Me Porto Bonito (Video Oficial)", published_at: "2022-05-06", thumbnail: "https://i.ytimg.com/vi/GtSRCCUkxoo/mqdefault.jpg", views: 540000000, likes: 4200000 },
      { video_id: "kTlv5_nf-IM", title: "Dakiti (Video Oficial)", published_at: "2020-10-02", thumbnail: "https://i.ytimg.com/vi/kTlv5_nf-IM/mqdefault.jpg", views: 830000000, likes: 6500000 },
    ],
    trending_regions: [
      { region: "US", rank: 1, video_title: "Titi Me Preguntó" },
      { region: "MX", rank: 1, video_title: "Me Porto Bonito" },
      { region: "AR", rank: 1, video_title: "Dakiti" },
      { region: "ES", rank: 2, video_title: "Titi Me Preguntó" },
      { region: "BR", rank: 4, video_title: "Dakiti" },
      { region: "DE", rank: 12, video_title: "Titi Me Preguntó" },
      { region: "FR", rank: 14, video_title: "Titi Me Preguntó" },
      { region: "IT", rank: 9, video_title: "Me Porto Bonito" },
    ],
    trending_region_count: 8, total_views_top5: 1990000000,
    momentum: { score: 91.2, label: "Rising", factors: { followers_score: 30, popularity_score: 30, upcoming_score: 15, tour_score: 16.2 } },
    cached_at: "2025-05-01T00:00:00Z",
  },
  "taylor swift": {
    name: "Taylor Swift", listeners: 16200000, playcount: 1800000000,
    tags: ["pop", "country pop", "indie folk", "alternative", "singer-songwriter"],
    image_url: "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png",
    country_presence: [
      { country: "United States", rank: 1, listeners: 6800000 },
      { country: "United Kingdom", rank: 1, listeners: 2100000 },
      { country: "Australia", rank: 1, listeners: 1400000 },
      { country: "Canada", rank: 1, listeners: 1200000 },
      { country: "Germany", rank: 2, listeners: 900000 },
      { country: "France", rank: 3, listeners: 750000 },
      { country: "Brazil", rank: 2, listeners: 1100000 },
      { country: "Japan", rank: 3, listeners: 680000 },
      { country: "Sweden", rank: 2, listeners: 500000 },
    ],
    recent_concerts: [
      { date: "2024-11-23", venue_name: "BC Place", city: "Vancouver", country: "Canada", lat: 49.2, lon: -123.1, tour_name: "The Eras Tour" },
      { date: "2024-10-18", venue_name: "Hard Rock Stadium", city: "Miami", country: "United States", lat: 25.9, lon: -80.2, tour_name: "The Eras Tour" },
      { date: "2024-08-19", venue_name: "Wembley Stadium", city: "London", country: "United Kingdom", lat: 51.55, lon: -0.28, tour_name: "The Eras Tour" },
      { date: "2024-07-07", venue_name: "Aviva Stadium", city: "Dublin", country: "Ireland", lat: 53.3, lon: -6.2, tour_name: "The Eras Tour" },
      { date: "2024-02-07", venue_name: "Tokyo Dome", city: "Tokyo", country: "Japan", lat: 35.7, lon: 139.75, tour_name: "The Eras Tour" },
    ],
    tour_timeline: [
      { tour: "Fearless Tour", start_date: "2009-04-23", end_date: "2010-07-10", show_count: 111, countries: ["US", "CA", "UK", "AU"] },
      { tour: "The Red Tour", start_date: "2013-03-13", end_date: "2014-06-12", show_count: 86, countries: ["US", "CA", "UK", "AU", "NZ"] },
      { tour: "The 1989 World Tour", start_date: "2015-05-05", end_date: "2015-12-12", show_count: 85, countries: ["US", "CA", "UK", "AU", "JP", "DE", "FR"] },
      { tour: "Reputation Stadium Tour", start_date: "2018-05-08", end_date: "2018-11-21", show_count: 53, countries: ["US", "CA", "UK", "AU", "NZ", "JP"] },
      { tour: "The Eras Tour", start_date: "2023-03-17", end_date: "2024-12-08", show_count: 149, countries: ["US", "CA", "UK", "AU", "JP", "DE", "FR", "BR", "MX", "AR", "SG", "SE"] },
    ],
    upcoming_events: [],
    top_videos: [
      { video_id: "nfWlot6h_JM", title: "Shake It Off (Taylor's Version) (Lyric Video)", published_at: "2023-07-07", thumbnail: "https://i.ytimg.com/vi/nfWlot6h_JM/mqdefault.jpg", views: 390000000, likes: 2800000 },
      { video_id: "q3zqJs7JUCQ", title: "Anti-Hero (Official Music Video)", published_at: "2022-10-21", thumbnail: "https://i.ytimg.com/vi/q3zqJs7JUCQ/mqdefault.jpg", views: 520000000, likes: 4100000 },
      { video_id: "k1-TrAvp_xs", title: "Blank Space", published_at: "2014-11-10", thumbnail: "https://i.ytimg.com/vi/k1-TrAvp_xs/mqdefault.jpg", views: 3100000000, likes: 18000000 },
    ],
    trending_regions: [
      { region: "US", rank: 2, video_title: "Anti-Hero" },
      { region: "GB", rank: 3, video_title: "Anti-Hero" },
      { region: "AU", rank: 1, video_title: "Shake It Off" },
      { region: "CA", rank: 1, video_title: "Anti-Hero" },
      { region: "DE", rank: 5, video_title: "Anti-Hero" },
      { region: "JP", rank: 6, video_title: "Anti-Hero" },
      { region: "SE", rank: 4, video_title: "Blank Space" },
    ],
    trending_region_count: 7, total_views_top5: 4010000000,
    momentum: { score: 78.3, label: "Rising", factors: { followers_score: 30, popularity_score: 28, upcoming_score: 10, tour_score: 10 } },
    cached_at: "2025-05-01T00:00:00Z",
  },
  "rosalia": {
    name: "Rosalía", listeners: 5800000, playcount: 320000000,
    tags: ["flamenco", "pop", "urban", "experimental", "catalan"],
    image_url: "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png",
    country_presence: [
      { country: "Spain", rank: 1, listeners: 1800000 },
      { country: "Mexico", rank: 2, listeners: 1200000 },
      { country: "Argentina", rank: 2, listeners: 900000 },
      { country: "United States", rank: 8, listeners: 700000 },
      { country: "United Kingdom", rank: 9, listeners: 420000 },
      { country: "France", rank: 7, listeners: 380000 },
      { country: "Germany", rank: 11, listeners: 280000 },
    ],
    recent_concerts: [
      { date: "2023-08-12", venue_name: "Palau Sant Jordi", city: "Barcelona", country: "Spain", lat: 41.4, lon: 2.15, tour_name: "MOTOMAMI World Tour" },
      { date: "2023-07-18", venue_name: "Forum", city: "Los Angeles", country: "United States", lat: 33.96, lon: -118.27, tour_name: "MOTOMAMI World Tour" },
      { date: "2023-06-25", venue_name: "Ziggo Dome", city: "Amsterdam", country: "Netherlands", lat: 52.31, lon: 4.94, tour_name: "MOTOMAMI World Tour" },
      { date: "2023-05-15", venue_name: "Royal Festival Hall", city: "London", country: "United Kingdom", lat: 51.5, lon: -0.11, tour_name: "MOTOMAMI World Tour" },
    ],
    tour_timeline: [
      { tour: "El Mal Querer Tour", start_date: "2018-03-01", end_date: "2018-12-15", show_count: 24, countries: ["ES", "MX", "AR", "US"] },
      { tour: "MOTOMAMI World Tour", start_date: "2022-07-01", end_date: "2023-09-30", show_count: 58, countries: ["ES", "MX", "AR", "US", "UK", "FR", "DE", "NL", "IT"] },
    ],
    upcoming_events: [
      { name: "Rosalía", date: "2025-09-12", venue_name: "Palacio de los Deportes", city: "Madrid", country: "Spain", estimated_capacity: 18000, min_price: 55, max_price: 200, currency: "EUR", ticket_url: "https://www.ticketmaster.es", lat: 40.42, lon: -3.66 },
    ],
    top_videos: [
      { video_id: "MpnHMH17KFc", title: "DESPECHÁ (Official Video)", published_at: "2022-08-26", thumbnail: "https://i.ytimg.com/vi/MpnHMH17KFc/mqdefault.jpg", views: 140000000, likes: 1200000 },
      { video_id: "6vRa1BHTQ2s", title: "BIZCOCHITO (Official Video)", published_at: "2022-10-28", thumbnail: "https://i.ytimg.com/vi/6vRa1BHTQ2s/mqdefault.jpg", views: 95000000, likes: 820000 },
      { video_id: "7SXXbCKlA2Q", title: "Con Altura (Official Video)", published_at: "2019-04-05", thumbnail: "https://i.ytimg.com/vi/7SXXbCKlA2Q/mqdefault.jpg", views: 210000000, likes: 1900000 },
    ],
    trending_regions: [
      { region: "ES", rank: 1, video_title: "DESPECHÁ" },
      { region: "MX", rank: 3, video_title: "DESPECHÁ" },
      { region: "AR", rank: 4, video_title: "BIZCOCHITO" },
      { region: "US", rank: 18, video_title: "Con Altura" },
    ],
    trending_region_count: 4, total_views_top5: 445000000,
    momentum: { score: 62.1, label: "Rising", factors: { followers_score: 18, popularity_score: 19, upcoming_score: 10, tour_score: 15 } },
    cached_at: "2025-05-01T00:00:00Z",
  },
};

function getDemoData(name) {
  return DEMO_DATA[name.toLowerCase().trim()] || null;
}

// ── Country code → coords mapping (centroid) ────────────────────────────────
const COUNTRY_COORDS = {
  "United States": [37.1, -95.7], "United Kingdom": [55.4, -3.4],
  "Germany": [51.2, 10.5], "Brazil": [-14.2, -51.9], "France": [46.2, 2.2],
  "Mexico": [23.6, -102.5], "Argentina": [-38.4, -63.6], "Spain": [40.5, -3.7],
  "Australia": [-25.3, 133.8], "Canada": [56.1, -106.3], "Japan": [36.2, 138.3],
  "South Korea": [35.9, 127.8], "Italy": [41.9, 12.6], "Netherlands": [52.1, 5.3],
  "Poland": [51.9, 19.1], "Sweden": [60.1, 18.6], "Russia": [61.5, 105.3],
  "Turkey": [38.9, 35.2], "India": [20.6, 78.9], "Indonesia": [-0.8, 113.9],
};

// ── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n) => n >= 1_000_000
  ? (n / 1_000_000).toFixed(1) + "M"
  : n >= 1_000 ? (n / 1_000).toFixed(0) + "K" : String(n);

const $ = (id) => document.getElementById(id);

function showEl(id)  { const el = $(id); if (el) el.classList.remove("hidden"); }
function hideEl(id)  { const el = $(id); if (el) el.classList.add("hidden"); }

// ── Autocomplete ─────────────────────────────────────────────────────────────
let cachedArtists = [];

async function loadAutocomplete() {
  // Always seed with demo artists so autocomplete works offline
  cachedArtists = Object.values(DEMO_DATA).map(d => d.name);
  try {
    const res = await fetch(`${API_BASE}/api/top-artists`);
    if (res.ok) {
      const live = await res.json();
      cachedArtists = [...new Set([...cachedArtists, ...live])];
    }
  } catch { /* silent — demo artists already loaded */ }
}

$("search-input").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase().trim();
  const list = $("autocomplete-list");
  if (!q || cachedArtists.length === 0) { list.classList.add("hidden"); return; }
  const matches = cachedArtists.filter((a) => a.toLowerCase().includes(q)).slice(0, 6);
  if (!matches.length) { list.classList.add("hidden"); return; }
  list.innerHTML = matches
    .map((a) => `<div class="autocomplete-item" data-name="${a}">${a}</div>`)
    .join("");
  list.classList.remove("hidden");
});

document.addEventListener("click", (e) => {
  if (e.target.classList.contains("autocomplete-item")) {
    $("search-input").value = e.target.dataset.name;
    $("autocomplete-list").classList.add("hidden");
    doSearch();
  } else {
    $("autocomplete-list").classList.add("hidden");
  }
});

$("search-btn").addEventListener("click", doSearch);
$("search-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});

// ── Main search ───────────────────────────────────────────────────────────────
async function doSearch() {
  const name = $("search-input").value.trim();
  if (!name) return;

  hideEl("dashboard");
  hideEl("error-box");
  showEl("loading");

  // 1. Try live backend first
  try {
    const res = await fetch(`${API_BASE}/api/artist/${encodeURIComponent(name)}`);
    if (!res.ok) throw new Error(`API returned ${res.status}`);
    const data = await res.json();
    hideEl("loading");
    renderDashboard(data);
    showEl("dashboard");
    $("dashboard").scrollIntoView({ behavior: "smooth" });
    return;
  } catch (err) {
    // 2. Fall back to demo data if backend unavailable
    const demo = getDemoData(name);
    if (demo) {
      hideEl("loading");
      renderDashboard(demo);
      showEl("dashboard");
      $("dashboard").scrollIntoView({ behavior: "smooth" });
      return;
    }
    hideEl("loading");
    const box = $("error-box");
    box.innerHTML = `No results for <b>"${name}"</b>. Try: <em>The Weeknd</em>, <em>Bad Bunny</em>, <em>Taylor Swift</em> or <em>Rosalía</em>.<br><small style="opacity:.6">Live search requires the backend running on localhost:8000.</small>`;
    showEl("error-box");
  }
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderDashboard(d) {
  // Artist photo
  const img = $("artist-img");
  if (d.image_url) { img.src = d.image_url; img.style.display = "block"; }
  else { img.style.display = "none"; }

  $("artist-name").textContent = d.name;

  // Origin line: 🇵🇷 Puerto Rico · Solo Artist · Since 2013
  const originEl = $("artist-origin");
  if (originEl) {
    const parts = [];
    if (d.country_flag && d.country_name) {
      parts.push(`<span class="origin-flag">${d.country_flag}</span><span>${d.country_name}</span>`);
    } else if (d.country_name) {
      parts.push(`<span>${d.country_name}</span>`);
    }
    if (d.artist_type) {
      const typeLabel = d.artist_type === "Person" ? "Solo Artist" : d.artist_type;
      parts.push(`<span class="origin-dot">·</span><span>${typeLabel}</span>`);
    }
    if (d.begin_year) {
      // For solo artists begin_year = birth year; for bands = founding year
      const yearLabel = d.artist_type === "Person"
        ? `b. ${d.begin_year}`
        : `est. ${d.begin_year}`;
      parts.push(`<span class="origin-dot">·</span><span>${yearLabel}</span>`);
    }
    originEl.innerHTML = parts.join("");
  }

  $("artist-tags").innerHTML = (d.tags || []).slice(0, 5)
    .map((t) => `<span class="tag">${t}</span>`).join("");

  // Stats
  $("stat-listeners").textContent = fmt(d.spotify_followers || d.listeners || 0);
  $("stat-listeners-label").textContent = d.spotify_followers ? "SPOTIFY FOLLOWERS" : "GLOBAL LISTENERS";
  $("stat-plays").textContent = d.spotify_popularity ? `${d.spotify_popularity}/100` : fmt(d.playcount || 0);
  $("stat-plays-label").textContent = d.spotify_popularity ? "SPOTIFY POPULARITY" : "ALL-TIME PLAYS";
  $("stat-shows").textContent = (d.upcoming_events || []).length;
  $("stat-albums").textContent = (d.albums || []).length || "—";  // only full albums

  renderMomentum(d.momentum);
  renderTopTracks(d.top_tracks || []);
  renderYoutube(d.top_videos || []);
  renderAlbums(d.albums || []);
  renderSingles(d.singles || []);
  renderUpcoming(d.upcoming_events || []);
  renderRelatedArtists(d.related_artists || []);
}

// ── Momentum ──────────────────────────────────────────────────────────────────
function renderMomentum(m) {
  if (!m) return;
  const cls = m.label.toLowerCase();
  const icon = cls === "rising" ? "▲" : cls === "declining" ? "▼" : "→";

  $("momentum-label").textContent = `${icon} ${m.label}`;
  $("momentum-label").className = `momentum-label ${cls}`;
  $("momentum-score").textContent = m.score;
  $("momentum-bar").className = `momentum-bar ${cls}`;
  $("momentum-bar").style.width = `${m.score}%`;

  // Factors breakdown
  const f = m.factors || {};
  const factorsEl = $("momentum-factors");
  if (factorsEl) {
    const desc = cls === "rising"
      ? "High global relevance — strong fanbase, active on tour."
      : cls === "stable"
      ? "Established artist — consistent presence, moderate activity."
      : "Low current activity — small fanbase or off-tour.";
    factorsEl.innerHTML = `
      <div class="mf-row"><span>Followers</span><span>${f.followers_score ?? f.listener_score ?? "—"}/30</span></div>
      <div class="mf-row"><span>Popularity</span><span>${f.popularity_score ?? f.country_score ?? "—"}/30</span></div>
      <div class="mf-row"><span>Upcoming shows</span><span>${f.upcoming_score ?? f.youtube_score ?? "—"}/20</span></div>
      <div class="mf-row"><span>Tour history</span><span>${f.tour_score ?? "—"}/20</span></div>
      <p class="momentum-desc">${desc}</p>
    `;
  }
}

// ── Top Tracks with 30s Preview ──────────────────────────────────────────────
let _currentPlayBtn = null;

function renderTopTracks(tracks) {
  if (!tracks.length) { hideEl("tracks-section"); return; }
  const player = $("preview-player");

  $("tracks-list").innerHTML = tracks.map((t, i) => `
    <div class="track-row" id="track-${i}">
      <span class="track-num">${i + 1}</span>
      ${t.album_cover
        ? `<img class="track-cover" src="${t.album_cover}" alt="">`
        : `<div class="track-cover"></div>`}
      <div class="track-info">
        <div class="track-name">${t.name}</div>
        <div class="track-pop">Popularity ${t.popularity}/100</div>
      </div>
      ${t.preview_url
        ? `<button class="track-play-btn" id="play-${i}" onclick="togglePreview(${i}, '${t.preview_url}')">▶</button>`
        : ""}
      ${t.deezer_url
        ? `<a class="track-deezer" href="${t.deezer_url}" target="_blank" rel="noopener">Deezer</a>`
        : ""}
    </div>
  `).join("");

  showEl("tracks-section");

  // Stop preview when audio ends
  if (player) {
    player.addEventListener("ended", () => {
      if (_currentPlayBtn) { _currentPlayBtn.textContent = "▶"; _currentPlayBtn.classList.remove("playing"); }
      _currentPlayBtn = null;
    }, { once: false });
  }
}

function togglePreview(idx, url) {
  const player = $("preview-player");
  const btn = $(`play-${idx}`);
  if (!player || !btn) return;

  if (_currentPlayBtn && _currentPlayBtn !== btn) {
    _currentPlayBtn.textContent = "▶";
    _currentPlayBtn.classList.remove("playing");
  }

  if (player.src === url && !player.paused) {
    player.pause();
    btn.textContent = "▶";
    btn.classList.remove("playing");
    _currentPlayBtn = null;
  } else {
    player.src = url;
    player.play();
    btn.textContent = "■";
    btn.classList.add("playing");
    _currentPlayBtn = btn;
  }
}

// ── YouTube Top Videos ────────────────────────────────────────────────────────
function renderYoutube(videos) {
  const el = $("yt-videos");
  if (!videos.length) {
    el.innerHTML = '<p style="color:var(--muted);font-size:.85rem">No YouTube videos found.</p>';
    return;
  }
  el.innerHTML = videos.slice(0, 5).map((v) => `
    <a class="yt-video-item" href="https://youtube.com/watch?v=${v.video_id}" target="_blank" rel="noopener">
      <img class="yt-thumb" src="${v.thumbnail || ""}" alt="" />
      <div class="yt-meta">
        <div class="yt-title">${v.title}</div>
        <div class="yt-views">${v.views ? fmt(v.views) + " views" : "—"}</div>
      </div>
    </a>
  `).join("");
}

// ── Albums ────────────────────────────────────────────────────────────────────
function renderAlbums(albums) {
  if (!albums.length) { hideEl("albums-section"); return; }
  $("albums-list").innerHTML = albums.map(a => `
    <div class="album-card">
      ${a.image ? `<img class="album-cover" src="${a.image}" alt="${a.name}" />` : '<div class="album-cover album-no-img">♪</div>'}
      <div class="album-name">${a.name}</div>
      <div class="album-meta">${a.year || ""}${a.total_tracks ? ` · ${a.total_tracks} tracks` : ""}</div>
    </div>
  `).join("");
  showEl("albums-section");
}

// ── Country name normalizer ───────────────────────────────────────────────────
const COUNTRY_SHORT = {
  "United States Of America": "USA", "United States": "USA",
  "United Kingdom": "UK", "The Netherlands": "Netherlands",
  "South Korea": "South Korea", "Czech Republic": "Czech Republic",
};
function shortCountry(name) {
  return COUNTRY_SHORT[name] || name || "";
}

// ── Singles ───────────────────────────────────────────────────────────────────
function renderSingles(singles) {
  if (!singles.length) { hideEl("singles-section"); return; }
  $("singles-list").innerHTML = singles.map(s => `
    <div class="single-row">
      ${s.image
        ? `<img class="single-cover" src="${s.image}" alt="${s.name}">`
        : `<div class="single-cover-placeholder">♪</div>`}
      <div class="single-info">
        <div class="single-name">${s.name}</div>
        <div class="single-year">${s.year || "—"}</div>
      </div>
    </div>
  `).join("");
  showEl("singles-section");
}

// ── Upcoming Shows ────────────────────────────────────────────────────────────
function renderUpcoming(events) {
  const el = $("upcoming-list");
  if (!events.length) {
    el.innerHTML = '<p class="no-shows">No upcoming shows found.</p>';
    return;
  }
  el.innerHTML = events.slice(0, 15).map((ev) => {
    // Parse "YYYY-MM-DD" as local date (not UTC) to avoid off-by-one in non-UTC timezones
    const dateStr = ev.date ? (() => {
      const [y, m, d] = ev.date.split("-").map(Number);
      return new Date(y, m - 1, d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    })() : "TBA";
    const mapsUrl = ev.venue_name && ev.city
      ? `https://www.google.com/maps/search/${encodeURIComponent(ev.venue_name + " " + ev.city)}`
      : null;
    const price = ev.min_price ? `From ${ev.currency} ${ev.min_price}` : "";
    return `
      <div class="show-card">
        <div class="show-date">${dateStr}</div>
        <div class="show-venue">${ev.venue_name || "—"}</div>
        <div class="show-location">${[ev.city, shortCountry(ev.country)].filter(Boolean).join(", ")}</div>
        ${price ? `<div class="show-price">${price}</div>` : ""}
        <div class="show-actions">
          ${mapsUrl ? `<a class="show-maps-btn" href="${mapsUrl}" target="_blank" rel="noopener">📍 Maps</a>` : ""}
          ${ev.ticket_url ? `<a class="show-ticket-btn" href="${ev.ticket_url}" target="_blank" rel="noopener">🎟 Tickets</a>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

// ── Related Artists ───────────────────────────────────────────────────────────
function renderRelatedArtists(artists) {
  if (!artists.length) { hideEl("related-section"); return; }
  $("related-artists").innerHTML = artists.map(a => `
    <div class="related-card" onclick="$('search-input').value='${a.name.replace(/'/g,"\\'")}';doSearch()">
      <span class="related-name">${a.name}</span>
      <span class="related-pop">${a.popularity}/100</span>
    </div>
  `).join("");
  showEl("related-section");
}

loadAutocomplete();
