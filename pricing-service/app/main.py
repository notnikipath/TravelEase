from __future__ import annotations

from datetime import date

import httpx
from fastapi import FastAPI, HTTPException, Query

from shared.travelease_common import (
    COMPETITOR_PRICE_INDEX,
    PricingRequest,
    ServiceType,
    Settings,
    calculate_dynamic_price,
    forecast_price_trend,
)

settings = Settings(service_name="pricing-service", service_port=8504)
app = FastAPI(title="TravelEase Pricing Service", version="1.0.0")


def _auto_demand_index(start_date: date) -> float:
    days_to_trip = max((start_date - date.today()).days, 0)
    if days_to_trip <= 7:
        return 0.9
    if days_to_trip <= 21:
        return 0.72
    if days_to_trip <= 45:
        return 0.58
    return 0.44


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/pricing/calculate")
async def calculate_pricing(request: PricingRequest) -> dict:
    competitor = COMPETITOR_PRICE_INDEX.get(request.item_id)
    demand_index = max(request.demand_index, _auto_demand_index(request.start_date))
    result = calculate_dynamic_price(
        base_price=request.base_price,
        demand_index=demand_index,
        start_date=request.start_date,
        end_date=request.end_date,
        loyalty_level=request.loyalty_level,
        promo_discount_percent=request.promo_discount_percent,
        competitor_price=competitor,
    )
    return result.model_dump(mode="json")


@app.get("/pricing/quote")
async def pricing_quote(
    item_id: str,
    user_id: str | None = None,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service_type: ServiceType | None = None,
) -> dict:
    async with httpx.AsyncClient(timeout=8.0) as client:
        catalog_response = await client.get(f"{settings.content_service_url}/catalog/{item_id}")
    if catalog_response.status_code >= 400:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    item = catalog_response.json()

    loyalty_level = "bronze"
    if user_id:
        async with httpx.AsyncClient(timeout=8.0) as client:
            loyalty_response = await client.get(f"{settings.loyalty_service_url}/loyalty/{user_id}")
        if loyalty_response.status_code < 400:
            loyalty_level = loyalty_response.json().get("level", "bronze")

    request = PricingRequest(
        user_id=user_id,
        item_id=item_id,
        service_type=service_type or item["service_type"],
        start_date=start_date,
        end_date=end_date,
        base_price=item["base_price"],
        demand_index=_auto_demand_index(start_date),
        promo_discount_percent=0,
        loyalty_level=loyalty_level,
    )
    result = await calculate_pricing(request)
    return {"item": item, "price": result}


@app.get("/pricing/forecast/{item_id}")
async def forecast_price(item_id: str, horizon_days: int = Query(default=14, ge=3, le=30)) -> dict:
    competitor = COMPETITOR_PRICE_INDEX.get(item_id, 10000.0)
    trend = forecast_price_trend(base_price=competitor * 0.95, days=horizon_days)
    best_day = min(trend, key=lambda point: point["projected_price"])
    return {"item_id": item_id, "best_day_to_buy": best_day, "trend": trend}
