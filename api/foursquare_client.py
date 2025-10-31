"""
Foursquare API Client for local places and activities
"""
import httpx
from typing import List, Dict, Any, Optional
from utils.config import settings
import logging

logger = logging.getLogger(__name__)


class FoursquareClient:
    """
    Client for Foursquare Places API
    Provides access to local attractions, restaurants, and activities
    """

    def __init__(self):
        self.api_key = settings.FOURSQUARE_API_KEY
        self.base_url = "https://api.foursquare.com/v3"

    async def search_places(
        self,
        location: str,
        categories: Optional[List[str]] = None,
        radius: int = 10000,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for places near a location

        Args:
            location: City name or coordinates
            categories: List of category IDs to filter by
            radius: Search radius in meters
            limit: Maximum number of results

        Returns:
            List of places
        """
        try:
            params = {
                "near": location,
                "radius": radius,
                "limit": limit,
            }

            if categories:
                params["categories"] = ",".join(categories)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/places/search",
                    params=params,
                    headers={"Authorization": self.api_key},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json().get("results", [])

        except Exception as e:
            logger.error(f"Error searching places: {str(e)}")
            return []

    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place

        Args:
            place_id: Foursquare place ID

        Returns:
            Place details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/places/{place_id}",
                    headers={"Authorization": self.api_key},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}")
            return None

    async def search_restaurants(
        self, location: str, cuisine: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for restaurants

        Args:
            location: City name or coordinates
            cuisine: Cuisine type filter
            limit: Maximum number of results

        Returns:
            List of restaurants
        """
        # Restaurant category ID in Foursquare
        categories = ["13065"]  # Food & Dining

        return await self.search_places(
            location=location, categories=categories, limit=limit
        )
