# AIKU Backend

AI-powered travel planning backend built with FastAPI, featuring intelligent agents for itinerary generation.

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Task Queue**: Celery
- **AI/ML**: Anthropic Claude, OpenAI
- **APIs**: Amadeus (flights/hotels), Foursquare (places), OpenWeatherMap, SerpApi

## Features

- Multi-agent AI system for intelligent trip planning
- Flight search and recommendations via Amadeus API
- Hotel search and booking information
- Activity recommendations based on user preferences
- Real-time weather forecasts
- Budget optimization and cost tracking
- Asynchronous task processing with Celery
- Comprehensive API documentation (OpenAPI/Swagger)

## Project Structure

```
backend/
├── agents/                    # AI Agents
│   ├── orchestrator_agent.py # Main coordinator
│   ├── flight_agent.py       # Flight search
│   ├── accommodation_agent.py # Hotel search
│   ├── activity_agent.py     # Activity planning
│   └── weather_agent.py      # Weather forecasts
├── api/                      # External API clients
│   ├── amadeus_client.py    # Amadeus API
│   ├── foursquare_client.py # Foursquare API
│   ├── openweather_client.py # OpenWeatherMap
│   └── serpapi_client.py    # SerpApi
├── models/                   # Database models
│   ├── user.py
│   ├── trip.py
│   └── itinerary.py
├── routers/                  # API endpoints
│   ├── trips.py
│   ├── itinerary.py
│   ├── flights.py
│   ├── accommodations.py
│   └── weather.py
├── services/                 # Business logic
│   ├── itinerary_generator.py
│   ├── scheduler.py
│   └── optimizer.py
├── utils/                    # Utilities
│   ├── config.py
│   ├── validators.py
│   └── helpers.py
├── tests/                    # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── main.py                   # FastAPI app entry point
└── requirements.txt          # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (optional, for caching)
- API Keys (see Environment Variables section)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your configuration:
```env
# Application
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/aiku

# API Keys
AMADEUS_API_KEY=your-amadeus-key
AMADEUS_API_SECRET=your-amadeus-secret
FOURSQUARE_API_KEY=your-foursquare-key
OPENWEATHER_API_KEY=your-openweather-key
SERPAPI_API_KEY=your-serpapi-key
ANTHROPIC_API_KEY=your-anthropic-key
```

5. Set up the database:
```bash
# Create database tables
alembic upgrade head
```

6. Run the development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000)

API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Application secret key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | No |
| `AMADEUS_API_KEY` | Amadeus API key | Yes |
| `AMADEUS_API_SECRET` | Amadeus API secret | Yes |
| `FOURSQUARE_API_KEY` | Foursquare API key | Yes |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | Yes |
| `SERPAPI_API_KEY` | SerpApi API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Yes |

## API Endpoints

### Trips
- `GET /api/trips` - List all trips
- `POST /api/trips` - Create new trip
- `GET /api/trips/{trip_id}` - Get trip details
- `PUT /api/trips/{trip_id}` - Update trip
- `DELETE /api/trips/{trip_id}` - Delete trip

### Itinerary
- `POST /api/trips/{trip_id}/itinerary/generate` - Generate AI-powered itinerary
- `GET /api/trips/{trip_id}/itinerary` - Get itinerary
- `PUT /api/trips/{trip_id}/itinerary` - Update itinerary

### Flights
- `GET /api/flights/search` - Search flights

### Accommodations
- `GET /api/accommodations/search` - Search hotels

### Weather
- `GET /api/weather` - Get weather forecast

## Agent Architecture

The backend uses a multi-agent system to generate personalized travel itineraries:

### Orchestrator Agent
Coordinates all specialized agents and combines their outputs into a complete itinerary.

### Flight Agent
- Searches for flights using Amadeus API
- Ranks options based on price, duration, and preferences
- Provides best recommendations within budget

### Accommodation Agent
- Searches for hotels using Amadeus API
- Filters by location, budget, and amenities
- Recommends optimal accommodations

### Activity Agent
- Uses Foursquare and SerpApi to find attractions
- Creates day-by-day activity schedules
- Optimizes for travel time and user interests

### Weather Agent
- Fetches forecasts from OpenWeatherMap
- Influences activity recommendations
- Provides packing suggestions

## Database Models

### User
- Email, name, password
- Related trips

### Trip
- Destination, dates, budget
- Travelers count
- User preferences
- Status (draft, planning, confirmed, completed)

### Itinerary
- Generated itinerary data
- Daily schedules
- Activities, meals, accommodations
- Total cost breakdown

## Testing

Run tests with pytest:

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/unit/test_agents.py
```

## Development

### Adding a New Agent

1. Create new agent file in `agents/` directory
2. Inherit from `BaseAgent` class
3. Implement `execute()` method
4. Register with orchestrator

### Adding a New API Endpoint

1. Create/update router in `routers/` directory
2. Define Pydantic schemas
3. Implement endpoint logic
4. Add to `main.py` router includes

## Deployment

### Using Docker

```bash
docker build -t aiku-backend .
docker run -p 8000:8000 --env-file .env aiku-backend
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Run linting: `ruff check .`
5. Format code: `black .`
6. Submit a pull request

## License

MIT
