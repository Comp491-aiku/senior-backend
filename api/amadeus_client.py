"""
Amadeus API Client for flights and hotels
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.config import settings
import logging

logger = logging.getLogger(__name__)


class AmadeusClient:
    """
    Client for Amadeus Travel API
    Provides access to flight and hotel search
    """

    def __init__(self):
        self.api_key = settings.AMADEUS_API_KEY
        self.api_secret = settings.AMADEUS_API_SECRET
        self.base_url = "https://test.api.amadeus.com/v2"
        self.access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token
        """
        if self.access_token:
            return self.access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://test.api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            return self.access_token

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime] = None,
        passengers: int = 1,
        travel_class: str = "ECONOMY",
    ) -> List[Dict[str, Any]]:
        """
        Search for flights

        Args:
            origin: Origin airport code (IATA)
            destination: Destination airport code (IATA)
            departure_date: Departure date
            return_date: Return date (optional for one-way)
            passengers: Number of passengers
            travel_class: Travel class (ECONOMY, BUSINESS, FIRST)

        Returns:
            List of flight offers
        """
        try:
            token = await self._get_access_token()

            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date.strftime("%Y-%m-%d"),
                "adults": passengers,
                "travelClass": travel_class,
                "max": 50,
            }

            if return_date:
                params["returnDate"] = return_date.strftime("%Y-%m-%d")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/shopping/flight-offers",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json().get("data", [])

        except Exception as e:
            logger.error(f"Error searching flights: {str(e)}")
            return []

    async def search_hotels(
        self,
        location: str,
        check_in: datetime,
        check_out: datetime,
        guests: int = 1,
        budget: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels

        Args:
            location: City name or coordinates
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            budget: Maximum price per night

        Returns:
            List of hotel offers
        """
        try:
            token = await self._get_access_token()

            # First, get city code from location name
            # Then search for hotels
            params = {
                "cityCode": location,  # TODO: Convert city name to code
                "checkInDate": check_in.strftime("%Y-%m-%d"),
                "checkOutDate": check_out.strftime("%Y-%m-%d"),
                "adults": guests,
            }

            if budget:
                params["priceRange"] = f"0-{int(budget)}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/shopping/hotel-offers",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json().get("data", [])

        except Exception as e:
            logger.error(f"Error searching hotels: {str(e)}")
            return []
