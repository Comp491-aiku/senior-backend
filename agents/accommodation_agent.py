"""
Accommodation Agent - Handles accommodation search and recommendations
"""
from typing import Any, Dict
from .base_agent import BaseAgent
from api.amadeus_client import AmadeusClient


class AccommodationAgent(BaseAgent):
    """
    Agent responsible for searching and recommending accommodations
    """

    def __init__(self):
        super().__init__("AccommodationAgent")
        self.amadeus_client = AmadeusClient()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for accommodations based on trip requirements

        Args:
            context: Dictionary containing:
                - destination: str
                - start_date: datetime
                - end_date: datetime
                - travelers: int
                - budget: float
                - preferences: dict (accommodation type, amenities, etc.)

        Returns:
            Dictionary with accommodation recommendations
        """
        self.log_info(f"Searching accommodations in {context.get('destination')}")

        try:
            # TODO: Implement actual accommodation search
            # TODO: Need to extract preferences given the amadeus's offered amenities for each hotel
            #       would be an agentic operation using user intent. Currently everything is searched

            accommodations = await self.amadeus_client.search_hotels(
                location=context["destination"],
                check_in=context["start_date"],
                check_out=context["end_date"],
                guests=context["travelers"],
                budget=context.get("budget"),
            )

            # Filter and rank based on preferences
            recommended = self._rank_accommodations(accommodations, context)

            return {
                "options": recommended,
                "total_cost": self._calculate_accommodation_cost(recommended),
            }

        except Exception as e:
            self.log_error(f"Error searching accommodations: {str(e)}")
            return {"options": [], "total_cost": 0.0}

    def _rank_accommodations(self, accommodations: list, context: Dict[str, Any]) -> list:
        """
        Rank accommodations based on rating, budget fit, and preferences

        Simple scoring
        - 40% rating
        - 40% budget fit
        - 20% preference
        """
        if not accommodations:
            return []

        budget = context.get("budget")
        preferences = context.get("preferences", {})
        # TODO: Decide on given preferences, also how are preferences defined?
        #       on orchestrator agent, preferences are extracted in user intent but prompt
        #       does not specify intents for accommodations, which probably would make it
        #       useless for this case. Additional call to anthropic for agent specific context refinement?

        # TODO: Adjust preferences, this is a blueprint
        preferred_amenities = preferences.get("amenities", [])
        preferred_type = preferences.get("type", "").lower()

        scored_accommodations = []

        for accommodation in accommodations:
            try:
                # Extract data
                offers = accommodation.get("offers", [])
                if not offers:
                    continue

                offer = offers[0]
                price = float(offer.get("price", {}).get("total", 0))
                hotel = accommodation.get("hotel", {})
                rating = hotel.get("rating", 0)
                hotel_amenities = hotel.get("amenities", [])
                hotel_type = hotel.get("type", "").lower()

                score = 0

                # 1. Rating score (0-40 points)
                if rating:
                    score += (rating / 5.0) * 40

                # 2. Budget score (0-40 points)
                if budget and price > 0:
                    if price <= budget:
                        # Within budget - higher score for better value
                        score += 40 * (1 - price / budget)
                    else:
                        # Over budget - penalty
                        score -= (price - budget) / budget * 20

                # 3. Preference score (0-20 points)
                pref_score = 0

                # Check amenities match (0-10 points)
                if preferred_amenities and hotel_amenities:
                    matches = sum(
                        1 for pref in preferred_amenities
                        if any(pref.lower() in amenity.lower() for amenity in hotel_amenities)
                    )
                    pref_score += (matches / len(preferred_amenities)) * 10

                # Check type match (0-10 points)
                if preferred_type and hotel_type:
                    if preferred_type in hotel_type:
                        pref_score += 10

                score += pref_score

                accommodation["score"] = round(score, 2)
                scored_accommodations.append(accommodation)

            except Exception as e:
                self.log_error(f"Error scoring accommodation: {str(e)}")
                continue

        # Sort by score descending and return top 10
        scored_accommodations.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored_accommodations[:10]

    def _calculate_accommodation_cost(self, accommodations: list) -> float:
        """Calculate total accommodation cost"""
        # TODO: Implement cost calculation
        return 0.0

    async def find_alternatives(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find alternative accommodations

        Args:
            context: Dictionary with search criteria

        Returns:
            Dictionary with alternative accommodations
        """
        self.log_info("Finding alternative accommodations")

        try:
            # TODO: Implement alternative accommodation search
            return {
                "accommodations": [
                    {
                        "id": "alt_hotel_1",
                        "name": "Alternative Hotel",
                        "price": 150,
                        "rating": 4.5,
                    }
                ]
            }
        except Exception as e:
            self.log_error(f"Error finding alternatives: {str(e)}")
            return {"accommodations": []}
