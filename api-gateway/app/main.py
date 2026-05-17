from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.travelease_common import Role, Settings, sign_token, verify_token


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    service_port: int = 8500

    search_service_url: str = "http://search-service:8501"
    booking_service_url: str = "http://booking-service:8502"
    content_service_url: str = "http://content-service:8503"
    pricing_service_url: str = "http://pricing-service:8504"
    loyalty_service_url: str = "http://loyalty-service:8505"
    analytics_service_url: str = "http://analytics-service:8506"
    notification_service_url: str = "http://notification-service:8507"

    jwt_secret: str = Settings().jwt_secret
    token_exp_minutes: int = 240

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = GatewaySettings()
app = FastAPI(title="TravelEase API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5178",
        "http://127.0.0.1:5178",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    user_id: str
    role: Role


class SearchWorkflowRequest(BaseModel):
    city: str | None = None
    service_type: str | None = None
    guests: int = Field(default=1, ge=1, le=12)
    query_text: str | None = None
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    amenities: list[str] = Field(default_factory=list)
    user_id: str | None = None


class BookingWorkflowRequest(BaseModel):
    user_id: str
    item_id: str
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=12)
    payment_method: str = "card"


def _service_urls() -> dict[str, str]:
    return {
        "search": settings.search_service_url,
        "booking": settings.booking_service_url,
        "content": settings.content_service_url,
        "pricing": settings.pricing_service_url,
        "loyalty": settings.loyalty_service_url,
        "analytics": settings.analytics_service_url,
        "notification": settings.notification_service_url,
    }


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/auth/token")
async def issue_token(request: AuthRequest) -> dict[str, str]:
    token = sign_token(
        {"sub": request.user_id, "role": request.role.value},
        settings.jwt_secret,
        settings.token_exp_minutes,
    )
    return {"access_token": token, "token_type": "Bearer"}


@app.post("/auth/verify")
async def verify_auth(token: str) -> dict[str, Any]:
    payload = verify_token(token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.get("/services/health")
async def service_health() -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, base_url in _service_urls().items():
            try:
                statuses[name] = await _get_json(client, f"{base_url}/health")
            except Exception as exc:
                statuses[name] = {"status": "error", "detail": str(exc)}
    return statuses


@app.post("/workflow/search")
async def workflow_search(request: SearchWorkflowRequest) -> dict[str, Any]:
    params = {
        "city": request.city,
        "service_type": request.service_type,
        "guests": request.guests,
        "query_text": request.query_text,
        "price_min": request.price_min,
        "price_max": request.price_max,
        "min_rating": request.min_rating,
        "amenities": ",".join(request.amenities),
    }
    params = {key: value for key, value in params.items() if value not in {None, ""}}

    async with httpx.AsyncClient(timeout=15.0) as client:
        search = await _get_json(client, f"{settings.search_service_url}/search", params=params)
        if request.query_text:
            semantic = await _get_json(
                client,
                f"{settings.search_service_url}/search/semantic",
                params={"query": request.query_text},
            )
        else:
            semantic = {"semantic_tokens": []}
        if request.user_id:
            await _post_json(
                client,
                f"{settings.analytics_service_url}/analytics/events/search",
                {
                    "user_id": request.user_id,
                    "city": request.city,
                    "service_type": request.service_type,
                    "result_count": search.get("count", 0),
                },
            )
    return {"results": search, "semantic": semantic}


@app.post("/workflow/book-hotel")
async def workflow_book_hotel(request: BookingWorkflowRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        availability = await _get_json(
            client,
            f"{settings.booking_service_url}/availability/check",
            {
                "item_id": request.item_id,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
            },
        )
        if not availability.get("available", False):
            raise HTTPException(status_code=409, detail="Not available")

        quote = await _get_json(
            client,
            f"{settings.pricing_service_url}/pricing/quote",
            {
                "item_id": request.item_id,
                "user_id": request.user_id,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
            },
        )
        await _post_json(
            client,
            f"{settings.booking_service_url}/cart/{request.user_id}/items",
            {
                "item_id": request.item_id,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "travelers": request.travelers,
            },
        )
        booking = await _post_json(
            client,
            f"{settings.booking_service_url}/bookings/checkout",
            {"user_id": request.user_id, "payment_method": request.payment_method},
        )
        loyalty_state = await _get_json(client, f"{settings.loyalty_service_url}/loyalty/{request.user_id}")

    return {
        "availability": availability,
        "price_offer": quote["price"],
        "booking": booking["booking"],
        "payment": booking["payment"],
        "loyalty": loyalty_state,
    }
