"""
TMDB API Client - Handles all movie data fetching
"""
import os
import requests
from typing import Optional, Dict, List, Any

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

class TMDBClient:
    """Client for The Movie Database API"""

    def __init__(self):
        self.api_key = TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB_API_KEY not found in environment variables")

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a GET request to TMDB API"""
        url = f"{BASE_URL}/{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def search_movie(self, query: str) -> Optional[Dict]:
        """Search for a movie and return best match"""
        data = self._get("search/movie", {"query": query, "page": 1})
        results = data.get("results", [])
        return results[0] if results else None

    def get_movie_details(self, movie_id: int) -> Dict:
        """Get detailed info about a movie"""
        return self._get(f"movie/{movie_id}")

    def get_watch_providers(self, movie_id: int) -> Dict[str, Any]:
        """Get watch providers by country code"""
        return self._get(f"movie/{movie_id}/watch/providers")

    def get_movie_credits(self, movie_id: int) -> Dict:
        """Get cast and crew"""
        return self._get(f"movie/{movie_id}/credits")

    def get_similar_movies(self, movie_id: int) -> List[Dict]:
        """Get similar movie recommendations"""
        data = self._get(f"movie/{movie_id}/similar")
        return data.get("results", [])[:5]

    def get_now_playing(self) -> List[Dict]:
        """Get currently playing movies in theaters"""
        data = self._get("movie/now_playing", {"page": 1})
        return data.get("results", [])

    def get_poster_url(self, poster_path: str) -> str:
        """Build full poster URL"""
        return f"{IMAGE_BASE}{poster_path}" if poster_path else ""

    def format_providers(self, provider_list: List[Dict]) -> str:
        """Format provider list for display"""
        if not provider_list:
            return "❌ Not available"
        names = [p.get("provider_name", "Unknown") for p in provider_list]
        return ", ".join(names)

    def get_provider_logo_url(self, logo_path: str) -> str:
        """Get provider logo URL"""
        return f"{IMAGE_BASE}{logo_path}" if logo_path else ""

# Singleton instance
tmdb = TMDBClient()
