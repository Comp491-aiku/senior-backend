"""
Orchestration Tests - Levels 1 to 10

Tests the TravelAgentOrchestrator with increasing complexity:
- Level 1: Single simple tool call
- Level 2: Tool with parameter inference
- Level 3: Two related tool calls
- Level 4: Parallel tool execution
- Level 5: Sequential tool chain
- Level 6: Multi-step with context
- Level 7: Complex single domain
- Level 8: Full trip planning
- Level 9: Multi-city itinerary
- Level 10: Complex constraints & reasoning
"""

import pytest
import asyncio
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.agentic.orchestrator import TravelAgentOrchestrator
from app.agentic.history import ConversationHistory
from app.agentic.llm import AnthropicLLM
from app.db.supabase import get_supabase_admin_client
from app.db.models.conversation import get_conversation_service


# Test dates (2 weeks from now)
BASE_DATE = datetime.now() + timedelta(days=14)
START_DATE = BASE_DATE.strftime("%Y-%m-%d")
END_DATE = (BASE_DATE + timedelta(days=7)).strftime("%Y-%m-%d")
RETURN_DATE = (BASE_DATE + timedelta(days=5)).strftime("%Y-%m-%d")

# Test user email
TEST_USER_EMAIL = "test-orchestration@aiku-test.com"
TEST_USER_PASSWORD = "test-password-123!"
_test_user_id = None


class MockEventEmitter:
    """Mock event emitter to capture events during testing."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.tool_calls: List[str] = []
        self.structured_results: List[Dict[str, Any]] = []

    async def emit_thinking(self, message: str):
        self.events.append({"type": "thinking", "message": message})

    async def emit_iteration(self, current: int, max_iterations: int):
        self.events.append({"type": "iteration", "current": current, "max": max_iterations})

    async def emit_tool_start(self, tool_name: str, parameters: Dict[str, Any]):
        self.events.append({"type": "tool_start", "tool": tool_name, "params": parameters})
        self.tool_calls.append(tool_name)

    async def emit_tool_end(self, tool_name: str, result: Any, success: bool = True):
        self.events.append({"type": "tool_end", "tool": tool_name, "success": success})

    async def emit_tool_error(self, tool_name: str, error: str):
        self.events.append({"type": "tool_error", "tool": tool_name, "error": error})

    async def emit_message(self, message: str):
        self.events.append({"type": "message", "content": message})

    async def emit_error(self, error: str):
        self.events.append({"type": "error", "error": error})

    async def emit_complete(self):
        self.events.append({"type": "complete"})

    async def emit_weather(self, weather: Dict, city: str, tool_execution_id: str):
        self.structured_results.append({"type": "weather", "city": city, "data": weather})

    async def emit_flights(self, flights: List, search_params: Dict, tool_execution_id: str):
        self.structured_results.append({"type": "flights", "data": flights})

    async def emit_hotels(self, hotels: List, search_params: Dict, tool_execution_id: str):
        self.structured_results.append({"type": "hotels", "data": hotels})

    async def emit_transfers(self, transfers: List, search_params: Dict, tool_execution_id: str):
        self.structured_results.append({"type": "transfers", "data": transfers})

    async def emit_activities(self, activities: List, search_params: Dict, tool_execution_id: str):
        self.structured_results.append({"type": "activities", "data": activities})

    async def emit_exchange(self, exchange_data: Dict, tool_execution_id: str):
        self.structured_results.append({"type": "exchange", "data": exchange_data})


async def get_or_create_test_user() -> str:
    """Get or create test user and return user ID."""
    global _test_user_id
    if _test_user_id:
        return _test_user_id

    client = get_supabase_admin_client()

    # Try to find existing test user
    try:
        users = client.auth.admin.list_users()
        for user in users:
            if user.email == TEST_USER_EMAIL:
                _test_user_id = user.id
                return _test_user_id
    except Exception:
        pass

    # Create test user
    try:
        response = client.auth.admin.create_user({
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "email_confirm": True,
        })
        _test_user_id = response.user.id
        return _test_user_id
    except Exception as e:
        # User might already exist
        users = client.auth.admin.list_users()
        for user in users:
            if user.email == TEST_USER_EMAIL:
                _test_user_id = user.id
                return _test_user_id
        raise e


def create_orchestrator() -> TravelAgentOrchestrator:
    """Create a fresh orchestrator instance."""
    return TravelAgentOrchestrator(max_iterations=10)


async def create_conversation() -> ConversationHistory:
    """Create a fresh conversation in database."""
    user_id = await get_or_create_test_user()
    conv_service = get_conversation_service()

    # Create conversation in database
    db_conv = await conv_service.create_conversation(
        user_id=user_id,
        title="Orchestration Test",
    )

    return ConversationHistory(conversation_id=db_conv["id"])


# =============================================================================
# LEVEL 1: Single Simple Tool Call
# =============================================================================

class TestLevel1SingleToolCall:
    """Level 1: Simple single tool execution"""

    @pytest.mark.asyncio
    async def test_weather_simple(self):
        """Test simple weather query"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        query = f"What's the weather like in Paris from {START_DATE} to {END_DATE}?"
        response = await orchestrator.run(
            user_message=query,
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 1: Simple Weather Query")
        print(f"{'='*60}")
        print(f"User: {query}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:500]}...")

        assert len(emitter.tool_calls) >= 1
        assert "get_weather_forecast" in emitter.tool_calls
        assert "paris" in response.lower() or "weather" in response.lower()

    @pytest.mark.asyncio
    async def test_exchange_rate_simple(self):
        """Test simple exchange rate query"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message="What's the exchange rate from USD to EUR?",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 1: Exchange Rate Query")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:300]}...")

        assert len(emitter.tool_calls) >= 1
        assert any(t in emitter.tool_calls for t in ["get_exchange_rates", "convert_currency"])


# =============================================================================
# LEVEL 2: Tool with Parameter Inference
# =============================================================================

class TestLevel2ParameterInference:
    """Level 2: LLM must infer correct parameters"""

    @pytest.mark.asyncio
    async def test_hotel_city_inference(self):
        """Test hotel search with city name → city code inference"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"Find me hotels in Paris from {START_DATE} to {END_DATE}",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 2: Hotel City Code Inference")
        print(f"{'='*60}")
        print(f"User: Find me hotels in Paris from {START_DATE} to {END_DATE}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:500]}...")

        assert "search_hotels" in emitter.tool_calls
        # LLM should infer PAR as city code for Paris
        assert "hotel" in response.lower()

    @pytest.mark.asyncio
    async def test_flight_airport_inference(self):
        """Test flight search with city → airport code inference"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"Search flights from Istanbul to London on {START_DATE}",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 2: Airport Code Inference")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:500]}...")

        assert any(t in emitter.tool_calls for t in ["search_flights", "search_flights_fast"])


# =============================================================================
# LEVEL 3: Two Related Tool Calls
# =============================================================================

class TestLevel3TwoToolCalls:
    """Level 3: Two related tools for complete answer"""

    @pytest.mark.asyncio
    async def test_weather_and_activities(self):
        """Test weather + activities for trip planning"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"I'm going to Rome from {START_DATE} to {END_DATE}. What's the weather and what activities can I do?",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 3: Weather + Activities")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:600]}...")

        assert len(emitter.tool_calls) >= 2
        assert "get_weather_forecast" in emitter.tool_calls
        assert "search_activities" in emitter.tool_calls

    @pytest.mark.asyncio
    async def test_currency_and_budget(self):
        """Test currency conversion for budget planning"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message="I have 1000 USD budget for my trip to Turkey. How much is that in Turkish Lira and what's the exchange rate?",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 3: Currency + Budget")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:500]}...")

        assert len(emitter.tool_calls) >= 1
        assert any(t in emitter.tool_calls for t in ["convert_currency", "get_exchange_rates", "calculate_travel_budget"])


# =============================================================================
# LEVEL 4: Parallel Tool Execution
# =============================================================================

class TestLevel4ParallelExecution:
    """Level 4: Multiple independent tools executed in parallel"""

    @pytest.mark.asyncio
    async def test_flights_and_hotels_parallel(self):
        """Test parallel flight and hotel search"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"I need flights and hotels for a trip from Istanbul to Paris, {START_DATE} to {RETURN_DATE}",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 4: Parallel Flights + Hotels")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:700]}...")

        assert len(emitter.tool_calls) >= 2
        assert any(t in emitter.tool_calls for t in ["search_flights", "search_flights_fast"])
        assert "search_hotels" in emitter.tool_calls


# =============================================================================
# LEVEL 5: Sequential Tool Chain
# =============================================================================

class TestLevel5SequentialChain:
    """Level 5: Tools that depend on results of previous tools"""

    @pytest.mark.asyncio
    async def test_hotels_then_offers(self):
        """Test hotel search followed by getting offers"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"Find 5-star hotels in London for {START_DATE} to {END_DATE} and show me their room prices",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 5: Hotels → Offers Chain")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:700]}...")

        assert "search_hotels" in emitter.tool_calls or "get_hotel_offers" in emitter.tool_calls

    @pytest.mark.asyncio
    async def test_flights_then_price_analysis(self):
        """Test flight search followed by price analysis"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"Search flights from Istanbul to Barcelona on {START_DATE} and tell me if it's a good price or should I wait",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 5: Flights → Price Analysis")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:700]}...")

        assert any(t in emitter.tool_calls for t in ["search_flights", "search_flights_fast", "analyze_flight_prices"])


# =============================================================================
# LEVEL 6: Multi-Step with Context
# =============================================================================

class TestLevel6MultiStepContext:
    """Level 6: Complex queries requiring context understanding"""

    @pytest.mark.asyncio
    async def test_budget_trip_planning(self):
        """Test trip planning with budget constraints"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"I have $2000 for a 5-day trip from New York to Paris starting {START_DATE}. Find me flights and hotels that fit my budget.",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 6: Budget Trip Planning")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:800]}...")

        assert len(emitter.tool_calls) >= 2
        # Should search for both flights and hotels


# =============================================================================
# LEVEL 7: Complex Single Domain
# =============================================================================

class TestLevel7ComplexSingleDomain:
    """Level 7: Deep exploration within one domain"""

    @pytest.mark.asyncio
    async def test_comprehensive_flight_search(self):
        """Test comprehensive flight analysis"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"I need to fly from Istanbul to Amsterdam on {START_DATE}. Compare economy and business class options, and tell me the best dates to fly based on price trends.",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 7: Comprehensive Flight Analysis")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Response: {response[:800]}...")

        assert len(emitter.tool_calls) >= 1
        # Should use multiple flight searches or analysis


# =============================================================================
# LEVEL 8: Full Trip Planning
# =============================================================================

class TestLevel8FullTripPlanning:
    """Level 8: Complete trip with all components"""

    @pytest.mark.asyncio
    async def test_complete_trip_package(self):
        """Test complete trip planning with all services"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"""Plan a complete trip for me:
            - Flying from Istanbul to Barcelona
            - Dates: {START_DATE} to {RETURN_DATE}
            - Need: flights, hotel (4-5 star), airport transfer, and some activities
            - Also tell me about the weather""",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 8: Complete Trip Package")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Total tools: {len(emitter.tool_calls)}")
        print(f"Response length: {len(response)} chars")
        print(f"Response: {response[:1000]}...")

        # Should use multiple tools for comprehensive planning
        assert len(emitter.tool_calls) >= 3

        # Check for various services
        tool_set = set(emitter.tool_calls)
        print(f"Unique tools used: {tool_set}")


# =============================================================================
# LEVEL 9: Multi-City Itinerary
# =============================================================================

class TestLevel9MultiCityItinerary:
    """Level 9: Complex multi-destination trip"""

    @pytest.mark.asyncio
    async def test_multi_city_trip(self):
        """Test multi-city trip planning"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        date2 = (BASE_DATE + timedelta(days=3)).strftime("%Y-%m-%d")
        date3 = (BASE_DATE + timedelta(days=6)).strftime("%Y-%m-%d")

        response = await orchestrator.run(
            user_message=f"""Plan a multi-city trip:
            1. Istanbul → Paris on {START_DATE} (3 nights)
            2. Paris → Rome on {date2} (3 nights)
            3. Rome → Istanbul on {date3}
            I need flights and hotels for each leg.""",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 9: Multi-City Itinerary")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Total tools: {len(emitter.tool_calls)}")
        print(f"Response: {response[:1200]}...")

        # Should make multiple flight and hotel searches
        assert len(emitter.tool_calls) >= 4


# =============================================================================
# LEVEL 10: Complex Constraints & Reasoning
# =============================================================================

class TestLevel10ComplexReasoning:
    """Level 10: Ultimate test with complex requirements"""

    @pytest.mark.asyncio
    async def test_complex_family_trip(self):
        """Test complex family trip with multiple constraints"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"""I need to plan a family vacation:
            - 2 adults and 2 children
            - From Istanbul to Barcelona
            - Dates: {START_DATE} to {RETURN_DATE}
            - Budget: approximately $3000 total
            - Requirements:
              * Direct flights preferred
              * 4+ star family-friendly hotel
              * Need airport transfer for 4 people
              * Kid-friendly activities
              * Check weather to pack appropriately

            Please provide a complete plan with estimated costs in USD and also in EUR.""",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 10: Complex Family Trip")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Total tools: {len(emitter.tool_calls)}")
        print(f"Unique tools: {set(emitter.tool_calls)}")
        print(f"Response length: {len(response)} chars")
        print(f"Response: {response[:1500]}...")

        # Should use many different tools
        assert len(emitter.tool_calls) >= 5

        # Check response mentions key elements
        response_lower = response.lower()
        assert any(word in response_lower for word in ["flight", "hotel", "€", "$", "eur", "usd"])

    @pytest.mark.asyncio
    async def test_business_trip_optimization(self):
        """Test business trip with time and cost optimization"""
        orchestrator = create_orchestrator()
        conversation = await create_conversation()
        emitter = MockEventEmitter()

        response = await orchestrator.run(
            user_message=f"""I have a business meeting in London on {START_DATE}. I need to:
            1. Fly from Istanbul in business class
            2. Stay 2 nights at a 5-star hotel near the financial district
            3. Have airport transfer arranged
            4. Know the weather to dress appropriately
            5. Convert my expense budget of 50000 TRY to GBP and USD

            Find the most efficient options considering both time and cost.""",
            conversation=conversation,
            emitter=emitter,
        )

        print(f"\n{'='*60}")
        print("LEVEL 10: Business Trip Optimization")
        print(f"{'='*60}")
        print(f"Tools called: {emitter.tool_calls}")
        print(f"Total tools: {len(emitter.tool_calls)}")
        print(f"Response: {response[:1500]}...")

        assert len(emitter.tool_calls) >= 4


# =============================================================================
# Test Runner Summary
# =============================================================================

class TestOrchestrationSummary:
    """Summary test to verify all levels work"""

    @pytest.mark.asyncio
    async def test_all_levels_smoke(self):
        """Quick smoke test of all complexity levels"""
        orchestrator = create_orchestrator()

        test_cases = [
            ("Level 1", "What's the weather in Tokyo?"),
            ("Level 2", f"Find hotels in Istanbul for {START_DATE} to {END_DATE}"),
            ("Level 3", f"Weather and activities in Paris for {START_DATE}"),
            ("Level 4", f"Flights and hotels from Istanbul to Rome {START_DATE}"),
        ]

        results = []

        for level, query in test_cases:
            conversation = await create_conversation()
            emitter = MockEventEmitter()

            try:
                response = await orchestrator.run(
                    user_message=query,
                    conversation=conversation,
                    emitter=emitter,
                )
                results.append({
                    "level": level,
                    "query": query,
                    "tools": emitter.tool_calls,
                    "success": True,
                    "response_length": len(response),
                })
            except Exception as e:
                results.append({
                    "level": level,
                    "query": query,
                    "error": str(e),
                    "success": False,
                })

        print(f"\n{'='*60}")
        print("ORCHESTRATION SMOKE TEST SUMMARY")
        print(f"{'='*60}")

        for r in results:
            status = "✅" if r["success"] else "❌"
            print(f"{status} {r['level']}: {r.get('tools', r.get('error', 'N/A'))}")

        # At least 3 out of 4 should pass
        passed = sum(1 for r in results if r["success"])
        assert passed >= 3, f"Only {passed}/4 smoke tests passed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
