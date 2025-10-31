"""
SerpApi Client for supplementary search data
"""
import httpx
from typing import List, Dict, Any, Optional
from utils.config import settings
import logging

logger = logging.getLogger(__name__)


class SerpApiClient:
    """
    Client for SerpApi
    Provides access to Google search results for attractions and local information
    """

    def __init__(self):
        self.api_key = settings.SERPAPI_API_KEY
        self.base_url = "https://serpapi.com/search"

    async def search_attractions(
        self, location: str, query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for attractions in a location

        Args:
            location: City or region name
            query: Additional search query

        Returns:
            List of attractions from search results
        """
        try:
            search_query = f"top attractions in {location}"
            if query:
                search_query += f" {query}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": search_query,
                        "api_key": self.api_key,
                        "engine": "google",
                        "num": 20,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                # Extract relevant results
                results = []
                for item in data.get("organic_results", []):
                    results.append(
                        {
                            "title": item.get("title"),
                            "link": item.get("link"),
                            "snippet": item.get("snippet"),
                            "source": "google_search",
                        }
                    )

                return results

        except Exception as e:
            logger.error(f"Error searching attractions: {str(e)}")
            return []

    async def search_local_info(
        self, location: str, info_type: str
    ) -> List[Dict[str, Any]]:
        """
        Search for specific local information

        Args:
            location: City or region name
            info_type: Type of information (restaurants, events, etc.)

        Returns:
            List of search results
        """
        try:
            search_query = f"{info_type} in {location}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": search_query,
                        "api_key": self.api_key,
                        "engine": "google",
                        "num": 15,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("organic_results", []):
                    results.append(
                        {
                            "title": item.get("title"),
                            "link": item.get("link"),
                            "snippet": item.get("snippet"),
                        }
                    )

                return results

        except Exception as e:
            logger.error(f"Error searching local info: {str(e)}")
            return []
