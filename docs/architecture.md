# TravelEase Architecture

## Service map

- `api-gateway`: orchestration, auth token, unified workflows for search and booking.
- `search-service`: parametric and semantic search, cached responses, parallel source lookup.
- `booking-service`: availability, cart, booking state, payment mock, reservation lock.
- `content-service`: catalog, reviews, ratings, promotions and discounts.
- `pricing-service`: demand + competitor aware dynamic price calculation, price forecast.
- `loyalty-service`: points, levels, and personal offers.
- `analytics-service`: booking/search metrics, conversion KPI, hotelier reports, sentiment summary.
- `notification-service`: confirmation and promo notifications, delivery history.

## Infrastructure

- `PostgreSQL`: transactional storage target for bookings/content/loyalty.
- `Elasticsearch`: search index target for semantic and filtered search.
- `Redis`: cache layer for frequent search queries and short-lived workflow state.
- `RabbitMQ`: async event bus target for notifications and analytics ingestion.

## Main workflow

1. User sends `/workflow/search` via gateway.
2. `search-service` runs parallel queries (content + partner source), applies semantic ranking, returns cached result if available.
3. User sends `/workflow/book-hotel`.
4. `booking-service` checks availability and requests dynamic quote from `pricing-service`.
5. Booking is created and paid (mock payment).
6. Loyalty points are added in `loyalty-service`.
7. Event is sent to `analytics-service`.
8. Confirmation is sent by `notification-service`.

## Targets from task

- Search latency target: `< 2 sec` (with cache and parallel sources).
- Conversion target: `> 5%` (tracked in analytics API).
- Load target: `10M requests/day` (architecture-oriented target with horizontal scaling points in docs and compose layout).
