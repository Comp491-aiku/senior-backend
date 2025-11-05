# AIKU Backend - Docker Setup

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2+

## Quick Start

### 1. Build and Start All Services

```bash
cd /Users/ilkeryoru/Desktop/aiku/backend

# Start all services (PostgreSQL, Redis, Backend)
docker-compose up --build
```

This will:
- Create and start PostgreSQL database on port 5432
- Create and start Redis cache on port 6379
- Build and start the Backend API on port 8000
- Automatically create database tables

### 2. Access the Services

- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
  - User: `aiku_user`
  - Password: `aiku_password`
  - Database: `aiku_db`
- **Redis**: localhost:6379

### 3. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes database data)
docker-compose down -v
```

## Development Workflow

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Restart Backend Only

```bash
docker-compose restart backend
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up --build backend
```

### Execute Commands in Containers

```bash
# Backend shell
docker-compose exec backend bash

# PostgreSQL shell
docker-compose exec postgres psql -U aiku_user -d aiku_db

# Redis CLI
docker-compose exec redis redis-cli
```

## Environment Variables

Edit `.env` file to configure:

```env
# Database
DATABASE_URL=postgresql://aiku_user:aiku_password@postgres:5432/aiku_db

# API Keys (required for full functionality)
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
AMADEUS_API_KEY=your_key_here
AMADEUS_API_SECRET=your_secret_here
```

## Troubleshooting

### Port Already in Use

If you get "port already in use" error:

```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Find process using port 5432
lsof -ti:5432 | xargs kill -9
```

### Database Connection Issues

```bash
# Check if PostgreSQL is healthy
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up --build
```

### Reset Everything

```bash
# Stop all containers
docker-compose down -v

# Remove all images
docker-compose rm -f

# Rebuild from scratch
docker-compose up --build
```

## Production Deployment

For production, update:

1. Change `SECRET_KEY` in `.env` to a secure random string
2. Set `DEBUG=False`
3. Update `CORS_ORIGINS` to your frontend URL
4. Use strong database passwords
5. Add SSL certificates for HTTPS

```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build -d
```
