from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from shared.travelease_common import Settings

settings = Settings(service_name="notification-service", service_port=8507)
app = FastAPI(title="TravelEase Notification Service", version="1.0.0")

events: list[dict] = []


class BookingConfirmationRequest(BaseModel):
    user_id: str
    booking_id: str
    amount: float
    channel: str = "email"


class PromoMessageRequest(BaseModel):
    user_id: str
    message: str
    channel: str = "push"


def _store(kind: str, payload: dict) -> dict:
    event = {
        "event_id": str(uuid4()),
        "kind": kind,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    events.append(event)
    return event


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/notify/booking-confirmation")
async def notify_booking(request: BookingConfirmationRequest) -> dict:
    event = _store("booking_confirmation", request.model_dump(mode="json"))
    return {"status": "sent", "event": event}


@app.post("/notify/promo")
async def notify_promo(request: PromoMessageRequest) -> dict:
    event = _store("promo", request.model_dump(mode="json"))
    return {"status": "sent", "event": event}


@app.get("/notify/history")
async def history(limit: int = 100) -> dict:
    return {"items": events[-limit:], "count": min(limit, len(events))}
