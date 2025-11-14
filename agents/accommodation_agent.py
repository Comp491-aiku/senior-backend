"""
Accommodation Agent - Handles accommodation search and recommendations
"""
from typing import Any, Dict, List
from .base_agent import BaseAgent
from api.amadeus_client import AmadeusClient
from models.internal.amadeus_hotel import AmadeusHotelOffer

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
            recommended = self._rank_accommodations(accommodations, context)[0]

            return {
                "options": recommended,
                "total_cost": self._calculate_accommodation_cost(recommended),
            }

        except Exception as e:
            self.log_error(f"Error searching accommodations: {str(e)}")
            return {"options": [], "total_cost": 0.0}

    def _rank_accommodations(
        self, accommodations: List[AmadeusHotelOffer], context: Dict[str, Any]
    ) -> list:
        """
        Rank accommodations based on price, location, cancellation policy, and preferences

        Scoring breakdown:
        - 50% price fit (within budget)
        - 30% location quality (has coordinates)
        - 20% cancellation policy flexibility
        - 10% room quality (description, estimated type)
        # TODO: based on preference options rework on scoring
        """
        if not accommodations:
            return []

        budget = context.get("budget")
        preferences = context.get("preferences", {})
        # TODO: Decide on given preferences, also how are preferences defined?
        #       on orchestrator agent, preferences are extracted in user intent but prompt
        #       does not specify intents for accommodations, which probably would make it
        #       useless for this case. Additional call to anthropic for agent specific context refinement?

        preferred_room_type = preferences.get("room_type", "").lower()

        scored_accommodations = []

        for accommodation in accommodations:
            try:
                if not accommodation.available or not accommodation.offers:
                    continue

                # Using first offer for scoring
                offer = accommodation.offers[0]
                price = float(offer.price.total)
                hotel = accommodation.hotel

                score = 0.0

                if budget and price > 0:
                    price_ratio = price / budget
                    if price <= budget:
                        score += 30 + (1 - price_ratio) * 20
                    else:
                        score += max(0, 30 * (2 - price_ratio))
                else:
                    score += 20

                if hotel.latitude is not None and hotel.longitude is not None:
                    # coordinates good mapping and navigation
                    score += 30
                else:
                    score += 15

                if offer.policies and offer.policies.cancellation:
                    cancellation = offer.policies.cancellation
                    if cancellation.type:
                        cancel_type = cancellation.type.upper()
                        if "FULL_REFUND" in cancel_type:
                            score += 20
                        elif "REFUNDABLE" in cancel_type:
                            score += 15
                        elif "PARTIAL_REFUND" in cancel_type:
                            score += 10
                        else:
                            score += 5
                    else:
                        score += 10
                else:
                    score += 0

                room_score = 0.0

                if offer.room.description:
                    room_score += 3

                if offer.room.typeEstimated:
                    room_score += 2
                    type_est = offer.room.typeEstimated

                    if preferred_room_type:
                        if type_est.category and preferred_room_type in type_est.category.lower():
                            room_score += 3
                        elif type_est.bedType and preferred_room_type in type_est.bedType.lower():
                            room_score += 2

                score += room_score

                scored_accommodations.append((score, accommodation))

            except Exception as e:
                self.log_error(f"Error scoring accommodation {accommodation.hotel.hotelId}: {str(e)}")
                continue

        scored_accommodations.sort(key=lambda x: x[0], reverse=True)
        return [acc for _, acc in scored_accommodations[:10]]

    def _calculate_accommodation_cost(self, accommodation: AmadeusHotelOffer) -> float:
        """Calculate total accommodation cost"""
        return float(accommodation.offers[0].price.total)

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
            #       Based on what?
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
