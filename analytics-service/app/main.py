from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.travelease_common import Settings, conversion_rate, sentiment_label, sentiment_score

settings = Settings(service_name="analytics-service", service_port=8506)
app = FastAPI(title="TravelEase Analytics Service", version="1.0.0")

events: list[dict] = []
search_counter = 0
booking_counter = 0
revenue_total = 0.0
revenue_by_city: dict[str, float] = defaultdict(float)
bookings_by_city: dict[str, int] = defaultdict(int)


class SearchEventRequest(BaseModel):
    user_id: str | None = None
    city: str | None = None
    service_type: str | None = None
    result_count: int = Field(default=0, ge=0)


class BookingEventRequest(BaseModel):
    user_id: str
    booking_id: str
    amount: float = Field(ge=0)
    city: str
    service_type: str


class ReviewBatchRequest(BaseModel):
    texts: list[str]


def _store_event(event_type: str, payload: dict) -> None:
    events.append({"event_type": event_type, "timestamp": datetime.now(UTC).isoformat(), "payload": payload})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/analytics/events/search")
async def register_search(request: SearchEventRequest) -> dict:
    global search_counter
    search_counter += 1
    _store_event("search", request.model_dump(mode="json"))
    return {"status": "ok", "search_events": search_counter}


@app.post("/analytics/events/booking")
async def register_booking(request: BookingEventRequest) -> dict:
    global booking_counter, revenue_total
    booking_counter += 1
    revenue_total += request.amount
    revenue_by_city[request.city] += request.amount
    bookings_by_city[request.city] += 1
    _store_event("booking", request.model_dump(mode="json"))
    return {"status": "ok", "booking_events": booking_counter}


@app.get("/analytics/conversion")
async def get_conversion() -> dict:
    return {
        "searches": search_counter,
        "bookings": booking_counter,
        "conversion_percent": conversion_rate(search_counter, booking_counter),
    }


@app.get("/analytics/kpi")
async def get_kpi() -> dict:
    return {
        "searches": search_counter,
        "bookings": booking_counter,
        "conversion_percent": conversion_rate(search_counter, booking_counter),
        "revenue_total": round(revenue_total, 2),
        "daily_capacity_target": "10m requests/day (design target)",
        "search_latency_target": "<2 sec (architectural target)",
    }


@app.get("/analytics/reports/hotelier")
async def hotelier_report(city: str | None = None) -> dict:
    if city:
        return {
            "city": city,
            "bookings": bookings_by_city.get(city, 0),
            "revenue": round(revenue_by_city.get(city, 0.0), 2),
            "avg_check": round(
                revenue_by_city.get(city, 0.0) / max(bookings_by_city.get(city, 0), 1),
                2,
            ),
        }
    rows = []
    for current_city, amount in revenue_by_city.items():
        count = bookings_by_city[current_city]
        rows.append(
            {
                "city": current_city,
                "bookings": count,
                "revenue": round(amount, 2),
                "avg_check": round(amount / max(count, 1), 2),
            }
        )
    return {"items": rows, "count": len(rows)}


@app.post("/analytics/reviews/sentiment")
async def reviews_sentiment(request: ReviewBatchRequest) -> dict:
    result = []
    for text in request.texts:
        score = sentiment_score(text)
        result.append({"text": text, "score": score, "label": sentiment_label(score)})
    summary_score = round(sum(row["score"] for row in result) / max(len(result), 1), 3)
    return {"items": result, "summary_score": summary_score, "summary_label": sentiment_label(summary_score)}


@app.get("/analytics/events")
async def list_events(limit: int = 200) -> dict:
    return {"items": events[-limit:], "count": min(limit, len(events))}
