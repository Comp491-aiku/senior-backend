# AIKU Travel Agent - Complete Architecture Documentation

## Overview

**AIKU** (AI Knowledge Utility) is an AI-powered travel planning assistant built with a modern cloud-native microservices architecture. It uses **Anthropic Claude** as the orchestrating LLM with **8 specialized microservices** for travel functionality.

**Live URL:** https://secoa.ai

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Users["👤 Users"]
        Browser["Web Browser"]
    end

    subgraph VercelFrontend["☁️ Vercel - Frontend"]
        Frontend["secoa.ai<br/>Next.js 15 + TypeScript"]
    end

    subgraph GCP["☁️ Google Cloud Platform (europe-west1)"]
        subgraph CloudRunServices["Cloud Run Services"]
            Backend["AIKU Backend<br/>FastAPI + Python 3.13<br/>aiku-backend-*.run.app"]
            FastFlightsAPI["Fast Flights API<br/>FastAPI + Amadeus SDK<br/>fast-flights-api-*.run.app"]
        end

        subgraph Infrastructure["Infrastructure"]
            ArtifactRegistry["Artifact Registry<br/>Docker Images"]
            SecretManager["Secret Manager<br/>API Keys"]
            CloudBuild["Cloud Build<br/>CI/CD"]
        end
    end

    subgraph Supabase["🔐 Supabase"]
        SupabaseAuth["Supabase Auth<br/>+ Google OAuth 2.0"]
        PostgreSQL[("PostgreSQL<br/>+ Row Level Security")]
    end

    subgraph Anthropic["🤖 Anthropic API"]
        Claude["Claude claude-sonnet-4-5<br/>(Orchestrator LLM)"]
    end

    subgraph VercelAgents["☁️ Vercel - Microservice Agents"]
        WeatherAgent["Weather Agent<br/>OpenWeatherMap API"]
        FlightAgent["Flight Agent<br/>Amadeus API"]
        HotelAgent["Hotel Agent<br/>Amadeus API"]
        TransferAgent["Transfer Agent<br/>Amadeus API"]
        ActivitiesAgent["Activities Agent<br/>Amadeus API"]
        ExchangeAgent["Exchange Agent<br/>ExchangeRate API"]
        UtilityAgent["Utility Agent<br/>TimeZoneDB + GeoNames"]
    end

    subgraph Google["🔑 Google Cloud"]
        GoogleOAuth["Google OAuth 2.0<br/>Identity Provider"]
    end

    Browser -->|"HTTPS"| Frontend
    Frontend -->|"REST API + SSE"| Backend
    Frontend -->|"OAuth Redirect"| SupabaseAuth
    SupabaseAuth <-->|"OAuth 2.0"| GoogleOAuth
    Backend -->|"LLM API"| Claude
    Backend -->|"Verify JWT"| SupabaseAuth
    Backend -->|"CRUD + RLS"| PostgreSQL
    Backend -->|"HTTP"| FastFlightsAPI
    Backend -->|"HTTP"| WeatherAgent
    Backend -->|"HTTP"| FlightAgent
    Backend -->|"HTTP"| HotelAgent
    Backend -->|"HTTP"| TransferAgent
    Backend -->|"HTTP"| ActivitiesAgent
    Backend -->|"HTTP"| ExchangeAgent
    Backend -->|"HTTP"| UtilityAgent
    CloudBuild --> ArtifactRegistry
    ArtifactRegistry --> CloudRunServices
    SecretManager --> CloudRunServices

    style Frontend fill:#000,stroke:#fff,color:#fff
    style Backend fill:#009688,stroke:#fff,color:#fff
    style FastFlightsAPI fill:#4285F4,stroke:#fff,color:#fff
    style Claude fill:#D97706,stroke:#fff,color:#fff
    style PostgreSQL fill:#3ECF8E,stroke:#fff,color:#fff
    style SupabaseAuth fill:#3ECF8E,stroke:#fff,color:#fff
    style GoogleOAuth fill:#4285F4,stroke:#fff,color:#fff
```

---

## 2. All Services & URLs

### Production Endpoints

| Service | URL | Platform | Tech Stack |
|---------|-----|----------|------------|
| **Frontend** | https://secoa.ai | Vercel | Next.js 15, TypeScript, Tailwind |
| **Backend API** | https://aiku-backend-899018378108.europe-west1.run.app | GCP Cloud Run | FastAPI, Python 3.13 |
| **Fast Flights API** | https://fast-flights-api-1042410626896.europe-west1.run.app | GCP Cloud Run | FastAPI, Amadeus SDK |
| **Weather Agent** | https://weather-agent-seven.vercel.app | Vercel | Next.js API Routes |
| **Flight Agent** | https://flight-agent.vercel.app | Vercel | Next.js API Routes |
| **Hotel Agent** | https://hotel-agent-delta.vercel.app | Vercel | Next.js API Routes |
| **Transfer Agent** | https://transfer-agent.vercel.app | Vercel | Next.js API Routes |
| **Activities Agent** | https://activities-agent.vercel.app | Vercel | Next.js API Routes |
| **Exchange Agent** | https://exchange-agent.vercel.app | Vercel | Next.js API Routes |
| **Utility Agent** | https://utility-agent.vercel.app | Vercel | Next.js API Routes |
| **Supabase** | https://ixjgkcabzhrriektaotm.supabase.co | Supabase | PostgreSQL 15 |

---

## 3. Agent Architecture with External APIs

```mermaid
flowchart TB
    subgraph Orchestrator["🧠 AIKU Backend (Cloud Run)"]
        TravelAgent["TravelAgentOrchestrator<br/>ReAct Pattern"]
        AnthropicLLM["AnthropicLLM<br/>claude-sonnet-4-5-20250929"]
        ToolRegistry["Tool Registry<br/>18 Tools"]
    end

    subgraph FlightServices["✈️ Flight Services"]
        direction TB
        FlightTool["SearchFlightsTool<br/>AnalyzeFlightPricesTool"]
        FlightsAPITool["FlightsAPITool"]

        subgraph FlightAgentBox["Flight Agent (Vercel)"]
            FA_API["flight-agent.vercel.app"]
            FA_Amadeus["Amadeus Flight Offers API"]
        end

        subgraph FastFlightsBox["Fast Flights API (Cloud Run)"]
            FF_API["fast-flights-api-*.run.app"]
            FF_Amadeus["Amadeus Flight Offers Search v2"]
            FF_Key["API Key: ff-2026-*"]
        end
    end

    subgraph HotelServices["🏨 Hotel Services"]
        HotelTool["SearchHotelsTool<br/>GetHotelOffersTool"]
        subgraph HotelAgentBox["Hotel Agent (Vercel)"]
            HA_API["hotel-agent-delta.vercel.app"]
            HA_Amadeus["Amadeus Hotel List API<br/>Amadeus Hotel Offers API"]
        end
    end

    subgraph WeatherServices["🌤️ Weather Services"]
        WeatherTool["WeatherTool"]
        subgraph WeatherAgentBox["Weather Agent (Vercel)"]
            WA_API["weather-agent-seven.vercel.app"]
            WA_OWM["OpenWeatherMap API<br/>5-day Forecast"]
        end
    end

    subgraph TransferServices["🚕 Transfer Services"]
        TransferTool["SearchTransfersTool"]
        subgraph TransferAgentBox["Transfer Agent (Vercel)"]
            TA_API["transfer-agent.vercel.app"]
            TA_Amadeus["Amadeus Transfer API"]
        end
    end

    subgraph ActivityServices["🎯 Activity Services"]
        ActivityTool["SearchActivitiesTool"]
        subgraph ActivityAgentBox["Activities Agent (Vercel)"]
            AA_API["activities-agent.vercel.app"]
            AA_Amadeus["Amadeus Tours & Activities API"]
        end
    end

    subgraph ExchangeServices["💱 Exchange Services"]
        ExchangeTool["ConvertCurrencyTool<br/>GetExchangeRatesTool<br/>CalculateTravelBudgetTool"]
        subgraph ExchangeAgentBox["Exchange Agent (Vercel)"]
            EA_API["exchange-agent.vercel.app"]
            EA_XR["ExchangeRate-API<br/>Open Exchange Rates"]
        end
    end

    subgraph UtilityServices["🔧 Utility Services"]
        UtilityTool["GetCityTimeTool<br/>GetDistanceTool<br/>LookupIATACodeTool<br/>+ 5 more tools"]
        subgraph UtilityAgentBox["Utility Agent (Vercel)"]
            UA_API["utility-agent.vercel.app"]
            UA_APIs["TimeZoneDB API<br/>GeoNames API<br/>IATA Database"]
        end
    end

    TravelAgent --> AnthropicLLM
    TravelAgent --> ToolRegistry

    ToolRegistry --> FlightTool
    ToolRegistry --> FlightsAPITool
    ToolRegistry --> HotelTool
    ToolRegistry --> WeatherTool
    ToolRegistry --> TransferTool
    ToolRegistry --> ActivityTool
    ToolRegistry --> ExchangeTool
    ToolRegistry --> UtilityTool

    FlightTool --> FA_API
    FA_API --> FA_Amadeus

    FlightsAPITool --> FF_API
    FF_API --> FF_Amadeus

    HotelTool --> HA_API
    HA_API --> HA_Amadeus

    WeatherTool --> WA_API
    WA_API --> WA_OWM

    TransferTool --> TA_API
    TA_API --> TA_Amadeus

    ActivityTool --> AA_API
    AA_API --> AA_Amadeus

    ExchangeTool --> EA_API
    EA_API --> EA_XR

    UtilityTool --> UA_API
    UA_API --> UA_APIs

    style TravelAgent fill:#D97706,stroke:#fff,color:#fff
    style AnthropicLLM fill:#D97706,stroke:#fff,color:#fff
    style FF_API fill:#4285F4,stroke:#fff,color:#fff
```

---

## 4. AI Models & LLM Configuration

### Anthropic Claude Models Used

| Model | Model ID | Usage | Pricing (per MTok) |
|-------|----------|-------|-------------------|
| **Claude Sonnet 4.5** | `claude-sonnet-4-5-20250929` | Default orchestrator | $3 input / $15 output |
| Claude Opus 4.5 | `claude-opus-4-5-20251101` | Complex reasoning (optional) | $15 input / $75 output |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Fast, simple tasks | $1 input / $5 output |

### LLM Configuration

```python
# Backend Configuration (app/config.py)
DEFAULT_LLM_MODEL = "claude-sonnet-4-5-20250929"
LLM_MAX_TOKENS = 4096
LLM_TEMPERATURE = 0.7
LLM_MAX_ITERATIONS = 25  # ReAct loop limit
```

### Tool Use Format

Claude uses **native tool use** (function calling) with JSON schemas:

```json
{
  "name": "search_flights",
  "description": "Search for flights between airports",
  "input_schema": {
    "type": "object",
    "properties": {
      "origin": { "type": "string", "description": "IATA code" },
      "destination": { "type": "string", "description": "IATA code" },
      "date": { "type": "string", "format": "date" }
    },
    "required": ["origin", "destination", "date"]
  }
}
```

---

## 5. Google OAuth 2.0 Authentication Flow

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant F as Frontend (secoa.ai)
    participant S as Supabase Auth
    participant G as Google OAuth 2.0
    participant B as Backend API
    participant D as PostgreSQL

    Note over U,D: 1. Initial Login Flow

    U->>F: Click "Sign in with Google"
    F->>S: signInWithOAuth({ provider: 'google' })
    S->>U: Redirect to Google
    U->>G: Google Login Page
    G->>U: Consent Screen (email, profile)
    U->>G: Approve Access
    G->>S: Authorization Code
    S->>G: Exchange for Tokens
    G-->>S: Access Token + ID Token + Refresh Token
    S->>S: Create Supabase Session
    S->>S: Create/Update auth.users record
    S->>F: Redirect to /auth/callback?code=xxx
    F->>S: Exchange code for session
    S-->>F: JWT Access Token + Refresh Token
    F->>F: Store tokens in localStorage

    Note over U,D: 2. Authenticated API Requests

    U->>F: Interact with Chat
    F->>B: POST /api/v1/chat/stream<br/>Authorization: Bearer {JWT}
    B->>S: Verify JWT Token
    S-->>B: User Info (id, email, metadata)
    B->>D: Query with RLS Policy<br/>(user_id = auth.uid())
    D-->>B: User's Data Only
    B-->>F: SSE Response Stream

    Note over U,D: 3. Token Refresh (Automatic)

    F->>S: onAuthStateChange listener
    S->>S: Auto-refresh before expiry
    S-->>F: New JWT Token
```

### OAuth Configuration

**Google Cloud Console:**
- Project: `fast-flights-api-2026`
- OAuth 2.0 Client ID: Web application
- Authorized redirect URIs:
  - `https://ixjgkcabzhrriektaotm.supabase.co/auth/v1/callback`

**Supabase Auth Settings:**
- Provider: Google
- Client ID: `xxx.apps.googleusercontent.com`
- Client Secret: `GOCSPX-xxx`
- Scopes: `email`, `profile`, `openid`

**JWT Token Structure:**
```json
{
  "aud": "authenticated",
  "exp": 1704067200,
  "sub": "uuid-user-id",
  "email": "user@gmail.com",
  "app_metadata": {
    "provider": "google"
  },
  "user_metadata": {
    "full_name": "User Name",
    "avatar_url": "https://...",
    "email_verified": true
  }
}
```

---

## 6. Complete Tool Registry

| Tool Name | Description | Agent | External API |
|-----------|-------------|-------|--------------|
| `search_flights` | Search flights between airports | Flight Agent | Amadeus Flight Offers |
| `analyze_flight_prices` | Analyze price trends | Flight Agent | Amadeus Flight Prices |
| `search_flights_api` | Direct flight search (faster) | **Fast Flights API** | Amadeus Flight Offers v2 |
| `search_hotels` | Search hotels by city | Hotel Agent | Amadeus Hotel List |
| `get_hotel_offers` | Get room prices and offers | Hotel Agent | Amadeus Hotel Offers |
| `get_weather_forecast` | Weather for travel dates | Weather Agent | OpenWeatherMap 5-day |
| `search_transfers` | Airport/city transfers | Transfer Agent | Amadeus Transfer |
| `search_activities` | Tours and activities | Activities Agent | Amadeus Tours & Activities |
| `convert_currency` | Currency conversion | Exchange Agent | ExchangeRate-API |
| `get_exchange_rates` | Current exchange rates | Exchange Agent | ExchangeRate-API |
| `calculate_travel_budget` | Budget in destination currency | Exchange Agent | ExchangeRate-API |
| `get_city_time` | Current time in city | Utility Agent | TimeZoneDB |
| `get_time_difference` | Time difference between cities | Utility Agent | TimeZoneDB |
| `get_country_info` | Country information | Utility Agent | REST Countries |
| `get_distance` | Distance between locations | Utility Agent | Haversine + GeoNames |
| `get_days_between` | Days between dates | Utility Agent | Native calculation |
| `lookup_iata_code` | Airport IATA code lookup | Utility Agent | IATA Database |
| `search_iata_by_city` | Search airports by city | Utility Agent | IATA Database |

---

## 7. ReAct Orchestration Pattern

```mermaid
flowchart TB
    subgraph Input
        UserMsg["User Message"]
    end

    subgraph ReActLoop["ReAct Loop (max 25 iterations)"]
        direction TB

        Think["🧠 THINK<br/>Claude analyzes context"]
        Decide{"Need tools?"}
        Act["🔧 ACT<br/>Execute tool(s)"]
        Observe["👁️ OBSERVE<br/>Process results"]
        Respond["💬 RESPOND<br/>Generate answer"]
    end

    subgraph Tools["Available Tools"]
        T1["✈️ Flights"]
        T2["🏨 Hotels"]
        T3["🌤️ Weather"]
        T4["🚕 Transfers"]
        T5["🎯 Activities"]
        T6["💱 Exchange"]
        T7["🔧 Utilities"]
    end

    subgraph Output
        SSE["SSE Events to Frontend"]
        DB["Save to Database"]
    end

    UserMsg --> Think
    Think --> Decide
    Decide -->|"Yes"| Act
    Act --> T1 & T2 & T3 & T4 & T5 & T6 & T7
    T1 & T2 & T3 & T4 & T5 & T6 & T7 --> Observe
    Observe --> Think
    Decide -->|"No"| Respond
    Respond --> SSE
    Respond --> DB

    style Think fill:#D97706,stroke:#fff,color:#fff
    style Act fill:#3B82F6,stroke:#fff,color:#fff
    style Observe fill:#10B981,stroke:#fff,color:#fff
    style Respond fill:#8B5CF6,stroke:#fff,color:#fff
```

---

## 8. Database Schema (Supabase PostgreSQL)

```mermaid
erDiagram
    AUTH_USERS ||--o{ CONVERSATIONS : "owns"
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    CONVERSATIONS ||--o{ TOOL_EXECUTIONS : "logs"
    TOOL_EXECUTIONS ||--o{ TRAVEL_RESULTS : "produces"

    AUTH_USERS {
        uuid id PK "Supabase managed"
        text email UK
        jsonb raw_user_meta_data "Google profile"
        jsonb raw_app_meta_data "provider info"
        timestamp created_at
        timestamp updated_at
    }

    CONVERSATIONS {
        uuid id PK
        uuid user_id FK "RLS: auth.uid()"
        text title "First message truncated"
        text summary
        timestamp created_at
        timestamp updated_at
    }

    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        text role "user|assistant|tool"
        text content
        jsonb tool_calls "Claude tool_use blocks"
        text tool_call_id
        timestamp created_at
    }

    TOOL_EXECUTIONS {
        uuid id PK
        uuid conversation_id FK
        text tool_name
        jsonb input_params
        jsonb output_data
        text output_type "flights|hotels|weather|..."
        boolean success
        text error_message
        integer duration_ms
        text tool_call_id
        timestamp created_at
    }

    TRAVEL_RESULTS {
        uuid id PK
        uuid conversation_id FK
        uuid tool_execution_id FK
        text result_type "flight|hotel|activity|..."
        jsonb data "Structured result data"
        timestamp created_at
    }
```

### Row Level Security (RLS) Policies

```sql
-- Users can only see their own conversations
CREATE POLICY "Users view own conversations" ON conversations
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own conversations
CREATE POLICY "Users insert own conversations" ON conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Similar policies for messages, tool_executions, travel_results
```

---

## 9. SSE Event Types

```mermaid
flowchart LR
    subgraph Backend["Backend EventEmitter"]
        E["emit()"]
    end

    subgraph EventTypes["Event Types"]
        E1["thinking<br/>{message}"]
        E2["tool_start<br/>{tool, params}"]
        E3["tool_end<br/>{tool, result, success}"]
        E4["flights<br/>{items: Flight[]}"]
        E5["hotels<br/>{items: Hotel[]}"]
        E6["weather<br/>{forecast}"]
        E7["activities<br/>{items: Activity[]}"]
        E8["transfers<br/>{items: Transfer[]}"]
        E9["exchange<br/>{rates, budget}"]
        E10["message<br/>{content}"]
        E11["complete<br/>{message: 'Done'}"]
        E12["error<br/>{error, code}"]
    end

    subgraph Frontend["Frontend Handler"]
        UI["React State Update"]
        Cards["Render Cards"]
    end

    E --> E1 & E2 & E3 & E4 & E5 & E6 & E7 & E8 & E9 & E10 & E11 & E12
    E1 --> UI
    E2 --> UI
    E3 --> UI
    E4 --> Cards
    E5 --> Cards
    E6 --> Cards
    E7 --> Cards
    E8 --> Cards
    E9 --> UI
    E10 --> UI
    E11 --> UI
    E12 --> UI
```

---

## 10. Deployment Architecture

```mermaid
flowchart TB
    subgraph Dev["👨‍💻 Development"]
        LocalCode["Local Code"]
        GitPush["git push"]
    end

    subgraph GitHub["GitHub Repository"]
        Repo["aiku repo"]
    end

    subgraph VercelDeploy["Vercel (Frontend)"]
        VercelBuild["Auto Build"]
        VercelDeploy2["Deploy to Edge"]
        SecoaDomain["secoa.ai"]
    end

    subgraph GCPDeploy["Google Cloud Platform"]
        subgraph CloudBuildPipeline["Cloud Build Pipeline"]
            Trigger["Build Trigger"]
            DockerBuild["Docker Build<br/>--platform linux/amd64"]
            PushRegistry["Push to Artifact Registry"]
        end

        subgraph ArtifactReg["Artifact Registry"]
            BackendImage["aiku-backend:latest"]
            FlightsImage["fast-flights-api:latest"]
        end

        subgraph SecretMgr["Secret Manager"]
            S1["ANTHROPIC_API_KEY"]
            S2["SUPABASE_URL"]
            S3["SUPABASE_SERVICE_ROLE_KEY"]
            S4["SUPABASE_ANON_KEY"]
            S5["FLIGHTS_API_KEY"]
        end

        subgraph CloudRunDeploy["Cloud Run (europe-west1)"]
            BackendService["aiku-backend<br/>Memory: 1Gi<br/>CPU: 1<br/>Instances: 0-10"]
            FlightsService["fast-flights-api<br/>Memory: 512Mi<br/>CPU: 1<br/>Instances: 0-5"]
        end
    end

    LocalCode --> GitPush
    GitPush --> Repo
    Repo --> VercelBuild
    VercelBuild --> VercelDeploy2
    VercelDeploy2 --> SecoaDomain

    Repo --> Trigger
    Trigger --> DockerBuild
    DockerBuild --> PushRegistry
    PushRegistry --> BackendImage & FlightsImage
    BackendImage --> BackendService
    FlightsImage --> FlightsService
    S1 & S2 & S3 & S4 --> BackendService
    S5 --> FlightsService

    style SecoaDomain fill:#000,stroke:#fff,color:#fff
    style BackendService fill:#4285F4,stroke:#fff,color:#fff
    style FlightsService fill:#4285F4,stroke:#fff,color:#fff
```

---

## 11. Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (secoa.ai)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Framework: Next.js 15 (App Router)                                          │
│  Language: TypeScript 5.x                                                    │
│  Styling: Tailwind CSS + shadcn/ui                                          │
│  State: Zustand + TanStack Query                                            │
│  Animation: Framer Motion                                                    │
│  Auth: Supabase Auth (@supabase/supabase-js)                                │
│  Hosting: Vercel (Edge Network)                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              HTTPS + SSE
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (Cloud Run)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Framework: FastAPI 0.115.x                                                  │
│  Language: Python 3.13                                                       │
│  Server: Uvicorn (ASGI)                                                      │
│  Validation: Pydantic v2                                                     │
│  HTTP Client: httpx (async)                                                  │
│  Streaming: Server-Sent Events (SSE)                                         │
│  Container: Docker (linux/amd64)                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              Anthropic API
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AI / LLM LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Provider: Anthropic                                                         │
│  Model: claude-sonnet-4-5-20250929 (default)                                │
│  Pattern: ReAct (Reason + Act)                                              │
│  Features: Native Tool Use, Streaming, Multi-turn Context                   │
│  Max Tokens: 4096 per response                                              │
│  Temperature: 0.7                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              HTTP + API Keys
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL APIS (via Agents)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Amadeus for Developers: Flights, Hotels, Transfers, Activities             │
│  OpenWeatherMap: Weather Forecasts                                           │
│  ExchangeRate-API: Currency Conversion                                       │
│  TimeZoneDB: Time Zone Data                                                  │
│  GeoNames: Geographic Data                                                   │
│  Google OAuth 2.0: Authentication                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              Supabase Client
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Provider: Supabase                                                          │
│  Database: PostgreSQL 15                                                     │
│  Auth: Supabase Auth + Google OAuth 2.0                                     │
│  Security: Row Level Security (RLS)                                         │
│  Tables: conversations, messages, tool_executions, travel_results           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLOUD INFRASTRUCTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │   Google Cloud       │  │      Vercel          │  │    Supabase      │  │
│  │   Platform           │  │                      │  │                  │  │
│  │   ─────────────      │  │   ─────────────      │  │   ─────────      │  │
│  │   • Cloud Run        │  │   • Frontend Host    │  │   • PostgreSQL   │  │
│  │   • Artifact Reg.    │  │   • Edge Network     │  │   • Auth         │  │
│  │   • Cloud Build      │  │   • Auto Deploy      │  │   • Realtime     │  │
│  │   • Secret Manager   │  │   • Agent Hosting    │  │   • Storage      │  │
│  │   • IAM              │  │   • SSL/TLS          │  │   • RLS          │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Environment Variables

### Backend (.env)

```bash
# Application
APP_NAME=AIKU Travel Agent
APP_ENV=production
APP_DEBUG=false
API_VERSION=v1
HOST=0.0.0.0
PORT=8080

# Supabase
SUPABASE_URL=https://ixjgkcabzhrriektaotm.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Anthropic LLM
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_LLM_MODEL=claude-sonnet-4-5-20250929
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.7
LLM_MAX_ITERATIONS=25

# Fast Flights API (GCP Cloud Run)
FLIGHTS_API_URL=https://fast-flights-api-1042410626896.europe-west1.run.app
FLIGHTS_API_KEY=your-flights-api-key

# External Agents (Vercel)
WEATHER_AGENT_URL=https://weather-agent-seven.vercel.app
FLIGHT_AGENT_URL=https://flight-agent.vercel.app
HOTEL_AGENT_URL=https://hotel-agent-delta.vercel.app
TRANSFER_AGENT_URL=https://transfer-agent.vercel.app
ACTIVITIES_AGENT_URL=https://activities-agent.vercel.app
EXCHANGE_AGENT_URL=https://exchange-agent.vercel.app
UTILITY_AGENT_URL=https://utility-agent.vercel.app

# CORS
CORS_ORIGINS=["https://secoa.ai","http://localhost:3000"]
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_SUPABASE_URL=https://ixjgkcabzhrriektaotm.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_API_URL=https://aiku-backend-899018378108.europe-west1.run.app
```

---

## 13. Data Flow Example

```mermaid
sequenceDiagram
    participant U as User
    participant F as secoa.ai
    participant B as Backend
    participant C as Claude
    participant FF as Fast Flights API
    participant HA as Hotel Agent
    participant DB as Supabase

    U->>F: "Plan a trip to Paris Feb 15-20"
    F->>B: POST /api/v1/chat/stream
    B->>DB: Get conversation history
    B->>C: Messages + Tools

    loop ReAct Loop
        C-->>B: tool_use: search_flights_api
        B->>F: SSE: tool_start
        B->>FF: GET /api/v1/flights/search
        FF-->>B: Flight results
        B->>DB: Log tool_execution
        B->>F: SSE: flights {items}

        C-->>B: tool_use: search_hotels
        B->>F: SSE: tool_start
        B->>HA: GET /api/hotels
        HA-->>B: Hotel results
        B->>DB: Log tool_execution
        B->>F: SSE: hotels {items}

        C-->>B: Final response
    end

    B->>F: SSE: message {content}
    B->>F: SSE: complete
    B->>DB: Save messages
    F->>U: Display flights, hotels, message
```

---

*Generated: January 2026 | AIKU v1.0*
