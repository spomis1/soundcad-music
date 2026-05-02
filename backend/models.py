from pydantic import BaseModel
from typing import Optional


class CountryPresence(BaseModel):
    country: str
    country_code: Optional[str] = None
    rank: Optional[int] = None
    listeners: Optional[int] = None


class Concert(BaseModel):
    date: str
    year: Optional[int] = None
    venue_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    lat: float = 0.0
    lon: float = 0.0
    tour_name: Optional[str] = None
    songs_count: int = 0


class TourEra(BaseModel):
    tour: str
    start_date: str
    end_date: str
    show_count: int
    countries: list[str]


class UpcomingEvent(BaseModel):
    name: str
    date: str
    venue_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    lat: float = 0.0
    lon: float = 0.0
    ticket_url: Optional[str] = None
    estimated_capacity: int = 1000
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    currency: str = "USD"


class YoutubeVideo(BaseModel):
    video_id: str
    title: str
    published_at: str
    thumbnail: Optional[str] = None
    views: int = 0
    likes: int = 0


class TrendingRegion(BaseModel):
    region: str
    rank: int
    video_title: Optional[str] = None
    video_id: Optional[str] = None


class MomentumScore(BaseModel):
    score: float  # 0-100
    label: str    # "Rising", "Stable", "Declining"
    factors: dict


class RelatedArtist(BaseModel):
    name: str
    popularity: int = 0


class TopTrack(BaseModel):
    name: str
    popularity: int = 0
    preview_url: Optional[str] = None
    spotify_url: Optional[str] = None
    deezer_url: Optional[str] = None
    album_cover: Optional[str] = None


class Album(BaseModel):
    name: str
    year: Optional[str] = None
    total_tracks: Optional[int] = None
    image: Optional[str] = None
    album_type: Optional[str] = None


class ArtistResponse(BaseModel):
    name: str
    listeners: int = 0
    playcount: int = 0
    bio_summary: str = ""
    tags: list[str] = []
    image_url: Optional[str] = None
    spotify_url: Optional[str] = None
    # MusicBrainz metadata
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    country_flag: Optional[str] = None
    artist_type: Optional[str] = None   # "Person" | "Group"
    begin_year: Optional[str] = None
    origin_area: Optional[str] = None
    # Spotify
    spotify_followers: int = 0
    spotify_popularity: int = 0
    spotify_market_count: int = 0
    related_artists: list[RelatedArtist] = []
    top_tracks: list[TopTrack] = []
    albums: list[Album] = []
    singles: list[Album] = []
    # Geo presence
    country_presence: list[CountryPresence] = []
    # Tour data
    recent_concerts: list[Concert] = []
    tour_timeline: list[TourEra] = []
    # Upcoming
    upcoming_events: list[UpcomingEvent] = []
    # YouTube
    top_videos: list[YoutubeVideo] = []
    trending_regions: list[TrendingRegion] = []
    trending_region_count: int = 0
    total_views_top5: int = 0
    # Momentum
    momentum: MomentumScore
    # Meta
    cached_at: Optional[str] = None
