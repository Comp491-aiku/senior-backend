"""
Comprehensive Tool Tests for AIKU Travel Agent

Tests all external travel agent APIs and the FlightsAPI.
Run with: pytest tests/test_all_tools.py -v -s
"""

import asyncio
import pytest
from datetime import datetime, timedelta

# Test dates
TODAY = datetime.now()
START_DATE = (TODAY + timedelta(days=45)).strftime("%Y-%m-%d")
END_DATE = (TODAY + timedelta(days=52)).strftime("%Y-%m-%d")


class TestWeatherTool:
    """Test Weather Agent API"""

    @pytest.mark.asyncio
    async def test_weather_forecast_paris(self):
        """Test weather forecast for Paris"""
        from app.agentic.tools.travel.weather import WeatherTool

        tool = WeatherTool()
        result = await tool.execute(
            destination="Paris",
            start_date=START_DATE,
            end_date=END_DATE
        )

        print(f"\n{'='*60}")
        print(f"WEATHER TOOL - Paris ({START_DATE} to {END_DATE})")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:500]}..." if len(result.output) > 500 else f"Output: {result.output}")

        assert result.success, f"Weather tool failed: {result.error}"
        assert result.data is not None
        assert "daily_forecast" in result.data

    @pytest.mark.asyncio
    async def test_weather_forecast_istanbul(self):
        """Test weather forecast for Istanbul"""
        from app.agentic.tools.travel.weather import WeatherTool

        tool = WeatherTool()
        result = await tool.execute(
            destination="Istanbul",
            start_date=START_DATE,
            end_date=END_DATE
        )

        print(f"\n{'='*60}")
        print(f"WEATHER TOOL - Istanbul")
        print(f"{'='*60}")
        print(f"Success: {result.success}")

        assert result.success, f"Weather tool failed: {result.error}"


class TestFlightsTool:
    """Test Flight Agent API (Vercel)"""

    @pytest.mark.asyncio
    async def test_search_flights_ist_cdg(self):
        """Test flight search IST -> CDG"""
        from app.agentic.tools.travel.flights import SearchFlightsTool

        tool = SearchFlightsTool()
        result = await tool.execute(
            origin="IST",
            destination="CDG",
            departure_date=START_DATE,
            adults=2,
            cabin="ECONOMY"
        )

        print(f"\n{'='*60}")
        print(f"FLIGHTS TOOL - IST → CDG ({START_DATE})")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:800]}..." if len(result.output) > 800 else f"Output: {result.output}")

        assert result.success, f"Flights tool failed: {result.error}"
        assert result.data is not None
        assert "flights" in result.data

    @pytest.mark.asyncio
    async def test_search_flights_roundtrip(self):
        """Test round-trip flight search"""
        from app.agentic.tools.travel.flights import SearchFlightsTool

        tool = SearchFlightsTool()
        result = await tool.execute(
            origin="IST",
            destination="BCN",
            departure_date=START_DATE,
            return_date=END_DATE,
            adults=1
        )

        print(f"\n{'='*60}")
        print(f"FLIGHTS TOOL - Round Trip IST ↔ BCN")
        print(f"{'='*60}")
        print(f"Success: {result.success}")

        assert result.success, f"Flights tool failed: {result.error}"

    @pytest.mark.asyncio
    async def test_analyze_flight_prices(self):
        """Test flight price analysis"""
        from app.agentic.tools.travel.flights import AnalyzeFlightPricesTool

        tool = AnalyzeFlightPricesTool()
        result = await tool.execute(
            origin="IST",
            destination="LHR",
            departure_date=START_DATE
        )

        print(f"\n{'='*60}")
        print(f"FLIGHT PRICE ANALYSIS - IST → LHR")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:500]}..." if len(result.output) > 500 else f"Output: {result.output}")

        assert result.success, f"Price analysis failed: {result.error}"


class TestHotelsTool:
    """Test Hotel Agent API"""

    @pytest.mark.asyncio
    async def test_search_hotels_paris(self):
        """Test hotel search in Paris"""
        from app.agentic.tools.travel.hotels import SearchHotelsTool

        tool = SearchHotelsTool()
        result = await tool.execute(
            city_code="PAR",
            check_in_date=START_DATE,
            check_out_date=END_DATE,
            adults=2,
            rooms=1
        )

        print(f"\n{'='*60}")
        print(f"HOTELS TOOL - Paris ({START_DATE} to {END_DATE})")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:800]}..." if len(result.output) > 800 else f"Output: {result.output}")

        assert result.success, f"Hotels tool failed: {result.error}"
        assert result.data is not None
        assert "hotels" in result.data

    @pytest.mark.asyncio
    async def test_search_hotels_istanbul(self):
        """Test hotel search in Istanbul"""
        from app.agentic.tools.travel.hotels import SearchHotelsTool

        tool = SearchHotelsTool()
        result = await tool.execute(
            city_code="IST",
            check_in_date=START_DATE,
            check_out_date=END_DATE,
            adults=2,
            ratings="4,5"
        )

        print(f"\n{'='*60}")
        print(f"HOTELS TOOL - Istanbul (4-5 star)")
        print(f"{'='*60}")
        print(f"Success: {result.success}")

        assert result.success, f"Hotels tool failed: {result.error}"

    @pytest.mark.asyncio
    async def test_get_hotel_offers(self):
        """Test hotel offers"""
        from app.agentic.tools.travel.hotels import GetHotelOffersTool

        tool = GetHotelOffersTool()
        result = await tool.execute(
            city_code="LON",
            check_in_date=START_DATE,
            check_out_date=END_DATE,
            adults=2,
            rooms=1,
            currency="USD"
        )

        print(f"\n{'='*60}")
        print(f"HOTEL OFFERS - London")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:500]}..." if len(result.output) > 500 else f"Output: {result.output}")

        assert result.success, f"Hotel offers failed: {result.error}"


class TestTransfersTool:
    """Test Transfer Agent API"""

    @pytest.mark.asyncio
    async def test_search_transfers_cdg(self):
        """Test transfer search from CDG airport"""
        from app.agentic.tools.travel.transfers import SearchTransfersTool

        tool = SearchTransfersTool()
        # Eiffel Tower coordinates
        result = await tool.execute(
            **{"from": "CDG"},
            to_lat=48.8584,
            to_lng=2.2945,
            date_time=f"{START_DATE}T14:00:00",
            passengers=2
        )

        print(f"\n{'='*60}")
        print(f"TRANSFERS TOOL - CDG → Eiffel Tower")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:500]}..." if len(result.output) > 500 else f"Output: {result.output}")

        # Transfer may return no results but API should work
        assert result.success or "No transfers found" in str(result.output)

    @pytest.mark.asyncio
    async def test_search_transfers_ist(self):
        """Test transfer search from IST airport"""
        from app.agentic.tools.travel.transfers import SearchTransfersTool

        tool = SearchTransfersTool()
        result = await tool.execute(
            **{"from": "IST"},
            to_address="Taksim Square",
            to_city="Istanbul",
            date_time=f"{START_DATE}T10:00:00",
            passengers=3
        )

        print(f"\n{'='*60}")
        print(f"TRANSFERS TOOL - IST → Taksim")
        print(f"{'='*60}")
        print(f"Success: {result.success}")

        assert result.success or "No transfers found" in str(result.output)


class TestActivitiesTool:
    """Test Activities Agent API"""

    @pytest.mark.asyncio
    async def test_search_activities_paris(self):
        """Test activities search in Paris"""
        from app.agentic.tools.travel.activities import SearchActivitiesTool

        tool = SearchActivitiesTool()
        result = await tool.execute(
            city="PAR",
            radius=10,
            currency="USD"
        )

        print(f"\n{'='*60}")
        print(f"ACTIVITIES TOOL - Paris")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:800]}..." if len(result.output) > 800 else f"Output: {result.output}")

        assert result.success, f"Activities tool failed: {result.error}"
        assert result.data is not None
        assert "activities" in result.data

    @pytest.mark.asyncio
    async def test_search_activities_barcelona(self):
        """Test activities search in Barcelona"""
        from app.agentic.tools.travel.activities import SearchActivitiesTool

        tool = SearchActivitiesTool()
        result = await tool.execute(
            city="BCN",
            radius=5
        )

        print(f"\n{'='*60}")
        print(f"ACTIVITIES TOOL - Barcelona")
        print(f"{'='*60}")
        print(f"Success: {result.success}")

        assert result.success, f"Activities tool failed: {result.error}"

    @pytest.mark.asyncio
    async def test_search_activities_by_coordinates(self):
        """Test activities search by coordinates (Rome - Colosseum)"""
        from app.agentic.tools.travel.activities import SearchActivitiesTool

        tool = SearchActivitiesTool()
        result = await tool.execute(
            lat=41.8902,
            lng=12.4922,
            radius=2
        )

        print(f"\n{'='*60}")
        print(f"ACTIVITIES TOOL - Rome (Colosseum area)")
        print(f"{'='*60}")
        print(f"Success: {result.success}")

        assert result.success, f"Activities tool failed: {result.error}"


class TestExchangeTool:
    """Test Exchange Agent API"""

    @pytest.mark.asyncio
    async def test_convert_currency_usd_try(self):
        """Test USD to TRY conversion"""
        from app.agentic.tools.travel.exchange import ConvertCurrencyTool

        tool = ConvertCurrencyTool()
        result = await tool.execute(
            **{"from": "USD"},
            to="TRY",
            amount=1000
        )

        print(f"\n{'='*60}")
        print(f"EXCHANGE TOOL - Convert 1000 USD → TRY")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")

        assert result.success, f"Exchange tool failed: {result.error}"
        assert result.data is not None
        assert "converted_amount" in result.data

    @pytest.mark.asyncio
    async def test_convert_currency_multi(self):
        """Test conversion to multiple currencies"""
        from app.agentic.tools.travel.exchange import ConvertCurrencyTool

        tool = ConvertCurrencyTool()
        result = await tool.execute(
            **{"from": "EUR"},
            to="USD,GBP,TRY,JPY",
            amount=500
        )

        print(f"\n{'='*60}")
        print(f"EXCHANGE TOOL - Convert 500 EUR → Multiple")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")

        assert result.success, f"Exchange tool failed: {result.error}"

    @pytest.mark.asyncio
    async def test_get_exchange_rates(self):
        """Test get exchange rates"""
        from app.agentic.tools.travel.exchange import GetExchangeRatesTool

        tool = GetExchangeRatesTool()
        result = await tool.execute(
            base="USD",
            symbols="EUR,GBP,TRY,JPY"
        )

        print(f"\n{'='*60}")
        print(f"EXCHANGE RATES - USD base")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")

        assert result.success, f"Exchange rates failed: {result.error}"

    @pytest.mark.asyncio
    async def test_travel_budget(self):
        """Test travel budget calculation"""
        from app.agentic.tools.travel.exchange import CalculateTravelBudgetTool

        tool = CalculateTravelBudgetTool()
        result = await tool.execute(
            **{"from": "TRY"},
            amount=50000,
            destinations="EUR,USD,GBP"
        )

        print(f"\n{'='*60}")
        print(f"TRAVEL BUDGET - 50000 TRY")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")

        assert result.success, f"Travel budget failed: {result.error}"


class TestFlightsAPITool:
    """Test FlightsAPI (Google Cloud Run)"""

    @pytest.mark.asyncio
    async def test_flights_api_ist_cdg(self):
        """Test FlightsAPI IST -> CDG"""
        from app.agentic.tools.travel.flights_api import FlightsAPITool

        tool = FlightsAPITool()
        result = await tool.execute(
            from_airport="IST",
            to_airport="CDG",
            date=START_DATE,
            adults=1,
            seat="economy"
        )

        print(f"\n{'='*60}")
        print(f"FLIGHTS API (GCP) - IST → CDG ({START_DATE})")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:1000]}..." if len(result.output) > 1000 else f"Output: {result.output}")

        assert result.success, f"FlightsAPI failed: {result.error}"
        assert result.data is not None
        assert "flights" in result.data

    @pytest.mark.asyncio
    async def test_flights_api_business_class(self):
        """Test FlightsAPI with business class"""
        from app.agentic.tools.travel.flights_api import FlightsAPITool

        tool = FlightsAPITool()
        result = await tool.execute(
            from_airport="IST",
            to_airport="LHR",
            date=START_DATE,
            adults=2,
            seat="business"
        )

        print(f"\n{'='*60}")
        print(f"FLIGHTS API (GCP) - IST → LHR (Business)")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Output: {result.output[:800]}..." if len(result.output) > 800 else f"Output: {result.output}")

        assert result.success, f"FlightsAPI failed: {result.error}"

    @pytest.mark.asyncio
    async def test_flights_api_roundtrip(self):
        """Test FlightsAPI round-trip"""
        from app.agentic.tools.travel.flights_api import FlightsAPITool

        tool = FlightsAPITool()
        result = await tool.execute(
            from_airport="SAW",
            to_airport="AMS",
            date=START_DATE,
            return_date=END_DATE,
            adults=1,
            seat="economy"
        )

        print(f"\n{'='*60}")
        print(f"FLIGHTS API (GCP) - SAW ↔ AMS (Round-trip)")
        print(f"{'='*60}")
        print(f"Success: {result.success}")

        assert result.success, f"FlightsAPI failed: {result.error}"


class TestAllToolsTogether:
    """Integration test - simulate a travel planning scenario"""

    @pytest.mark.asyncio
    async def test_complete_trip_planning(self):
        """Test complete trip planning flow"""
        from app.agentic.tools.travel.weather import WeatherTool
        from app.agentic.tools.travel.flights import SearchFlightsTool
        from app.agentic.tools.travel.hotels import SearchHotelsTool
        from app.agentic.tools.travel.activities import SearchActivitiesTool
        from app.agentic.tools.travel.exchange import ConvertCurrencyTool
        from app.agentic.tools.travel.transfers import SearchTransfersTool

        print(f"\n{'='*60}")
        print(f"COMPLETE TRIP PLANNING - Istanbul to Barcelona")
        print(f"{'='*60}")

        # 1. Weather
        weather_tool = WeatherTool()
        weather = await weather_tool.execute(
            destination="Barcelona",
            start_date=START_DATE,
            end_date=END_DATE
        )
        print(f"\n1. WEATHER: {'✅' if weather.success else '❌'}")

        # 2. Flights
        flights_tool = SearchFlightsTool()
        flights = await flights_tool.execute(
            origin="IST",
            destination="BCN",
            departure_date=START_DATE,
            return_date=END_DATE,
            adults=2
        )
        print(f"2. FLIGHTS: {'✅' if flights.success else '❌'}")

        # 3. Hotels
        hotels_tool = SearchHotelsTool()
        hotels = await hotels_tool.execute(
            city_code="BCN",
            check_in_date=START_DATE,
            check_out_date=END_DATE,
            adults=2
        )
        print(f"3. HOTELS: {'✅' if hotels.success else '❌'}")

        # 4. Activities
        activities_tool = SearchActivitiesTool()
        activities = await activities_tool.execute(city="BCN", radius=10)
        print(f"4. ACTIVITIES: {'✅' if activities.success else '❌'}")

        # 5. Exchange
        exchange_tool = ConvertCurrencyTool()
        exchange = await exchange_tool.execute(
            **{"from": "TRY"},
            to="EUR",
            amount=20000
        )
        print(f"5. EXCHANGE: {'✅' if exchange.success else '❌'}")

        # 6. Transfers
        transfers_tool = SearchTransfersTool()
        transfers = await transfers_tool.execute(
            **{"from": "BCN"},
            to_address="La Rambla",
            to_city="Barcelona",
            date_time=f"{START_DATE}T14:00:00",
            passengers=2
        )
        print(f"6. TRANSFERS: {'✅' if transfers.success or 'No transfers' in str(transfers.output) else '❌'}")

        print(f"\n{'='*60}")
        print(f"TRIP PLANNING COMPLETE!")
        print(f"{'='*60}")

        # All should succeed (transfers may have no results)
        assert weather.success
        assert flights.success
        assert hotels.success
        assert activities.success
        assert exchange.success


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
