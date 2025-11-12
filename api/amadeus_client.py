"""
Amadeus API Client for flights and hotels
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.config import settings
import logging
from models.internal.amadeus_hotel import AmadeusHotelOffer, parse_hotel_offer

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
        self.base_url_v3 = "https://test.api.amadeus.com/v3"
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

    async def get_city_code(self, city_name: str) -> Optional[str]:
        """
        Convert city name to IATA city code
        """
        try:
            token = await self._get_access_token()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url_v3}/reference-data/locations/cities",
                    params={
                        "keyword": city_name,
                        "max": 1,
                    },
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json().get("data", [])

                if data:
                    return data[0].get("iataCode")
                return None

        except Exception as e:
            logger.error(f"Error getting city code for {city_name}: {str(e)}")
            return None

    async def search_hotels(
        self,
        location: str,
        check_in: datetime,
        check_out: datetime,
        guests: int = 1,
        budget: Optional[float] = None,
        hotel_limit: int = 20
    ) -> List[AmadeusHotelOffer]:
        """
        Search for hotels using two-step process:
        1. Convert city name to IATA code
        2. Search hotels by city to get hotel IDs
        3. Get offers for those hotel IDs

        Args:
            location: City name or IATA code (e.g., "Paris" or "PAR")
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            budget: Maximum price per night
            hotel_limit: number of hotels returned

        Returns:
            List of parsed hotel offers
        """
        try:
            token = await self._get_access_token()

            city_code = await self.get_city_code(location)
            if not city_code:
                logger.warning(f"Could not find city code for: {location}")
                return []

            hotel_ids = await self._get_hotel_ids_by_city(token, city_code)

            if not hotel_ids:
                logger.warning(f"No hotels found in city: {city_code}")
                return []

            # TODO: add currency to the params and send with budget constraint
            # TODO: We can search by preferences and amenities
            params = {
                "hotelIds": hotel_ids[:hotel_limit],
                "checkInDate": check_in.strftime("%Y-%m-%d"),
                "checkOutDate": check_out.strftime("%Y-%m-%d"),
                "adults": guests
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url_v3}/shopping/hotel-offers",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json().get("data", [])

                parsed_offers = []
                for hotel_offer_json in data:
                    try:
                        parsed_offer = parse_hotel_offer(hotel_offer_json)
                        parsed_offers.append(parsed_offer)
                    except ValueError as e:
                        logger.warning(f"Failed to parse hotel offer: {str(e)}")
                        continue

                return parsed_offers

        except Exception as e:
            logger.error(f"Error searching hotels: {str(e)}")
            return []

    async def _get_hotel_ids_by_city(self, token: str, city_code: str, radius: int = 5) -> List[str]:
        """
        Get hotel IDs for a given city code

        Returns:
            List of hotel IDs
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url_v3}/reference-data/locations/hotels/by-city",
                    params={
                        "cityCode": city_code,
                        "radius": radius
                    },
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )

                response.raise_for_status()
                data = response.json().get("data", [])

                return [hotel["hotelId"] for hotel in data]

        except Exception as e:
            logger.error(f"Error getting hotel IDs for city {city_code}: {str(e)}")
            return []
