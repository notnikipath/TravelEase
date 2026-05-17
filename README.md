# Task 15 - TravelEase

TravelEase is a microservice platform for smart travel search and booking:

- hotels and apartments
- flights
- railway tickets
- excursions
- all-inclusive tours

## Implemented modules

- `search-service`
  - search by date/city/guests
  - filters by price/rating/amenities
  - semantic search
  - result caching
  - parallel lookup in multiple sources
- `booking-service`
  - availability check
  - cart
  - checkout + payment mock
- `content-service`
  - catalog (descriptions/photos-ready fields)
  - reviews and ratings
  - promotions and discounts
- `pricing-service`
  - demand-aware dynamic pricing
  - competitor-aware price correction
  - price forecast ("best day to buy")
- `loyalty-service`
  - points, levels (bronze/silver/gold/platinum)
  - personal offers
- `analytics-service`
  - booking and search statistics
  - conversion KPI
  - reports for hoteliers
  - review sentiment analytics
- `notification-service`
  - booking confirmation and promo notifications

## Architecture

```text
travelease/
├── api-gateway/
├── search-service/
├── booking-service/
├── content-service/
├── pricing-service/
├── loyalty-service/
├── analytics-service/
└── notification-service/
```

See full architecture notes: `docs/architecture.md`.

## Stack

- Backend: Python FastAPI
- DB: PostgreSQL
- Search infra: Elasticsearch
- Cache: Redis
- Queue: RabbitMQ
- Payments: mock endpoint (integration point for Stripe/YooKassa)
- Frontend: React + Vite

## Optional improvements implemented

- Group A:
  - recommendation endpoint (`/recommendations/{item_id}`)
  - price forecast (`/pricing/forecast/{item_id}`)
  - sentiment analysis for reviews
- Group C:
  - search caching
  - parallel source search

## Local run

```bash
cd d:\Шарага\Кинжа4\Task_15_TravelEase
docker compose up --build -d
```

## Useful URLs

- Frontend: `http://localhost:5178`
- API Gateway health: `http://localhost:8500/health`
- Aggregated service health: `http://localhost:8500/services/health`
- Gateway docs: `http://localhost:8500/docs`

## Quick workflow example

```bash
curl -X POST http://localhost:8500/workflow/search \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"user-demo\",\"city\":\"Sochi\",\"query_text\":\"beach all inclusive\"}"
```

```bash
curl -X POST http://localhost:8500/workflow/book-hotel \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"user-demo\",\"item_id\":\"HTL-003\",\"start_date\":\"2026-06-20\",\"end_date\":\"2026-06-25\",\"travelers\":2}"
```

## Checks

```bash
python -m ruff check .
python -m pytest -q
docker compose config
```

## Demo scripts

```bash
python scripts/generate_sample_data.py
python scripts/demo_workflow.py
```
