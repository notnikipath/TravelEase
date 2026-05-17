from __future__ import annotations

from fastapi import FastAPI

from shared.travelease_common import (
    EarnPointsRequest,
    LoyaltyState,
    Settings,
    level_by_points,
    personal_offers,
    points_from_amount,
)

settings = Settings(service_name="loyalty-service", service_port=8505)
app = FastAPI(title="TravelEase Loyalty Service", version="1.0.0")

loyalty_db: dict[str, LoyaltyState] = {
    "user-demo": LoyaltyState(
        user_id="user-demo",
        points=1350,
        level=level_by_points(1350),
        personal_offers=personal_offers(level_by_points(1350), favorite_city="Sochi"),
    )
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


def _load_or_create(user_id: str) -> LoyaltyState:
    existing = loyalty_db.get(user_id)
    if existing:
        return existing
    state = LoyaltyState(
        user_id=user_id,
        points=0,
        level=level_by_points(0),
        personal_offers=personal_offers(level_by_points(0)),
    )
    loyalty_db[user_id] = state
    return state


@app.get("/loyalty/{user_id}")
async def get_loyalty(user_id: str, favorite_city: str | None = None) -> dict:
    state = _load_or_create(user_id)
    state.personal_offers = personal_offers(state.level, favorite_city=favorite_city)
    return state.model_dump(mode="json")


@app.post("/loyalty/earn")
async def earn_points(request: EarnPointsRequest) -> dict:
    state = _load_or_create(request.user_id)
    state.points += points_from_amount(request.amount)
    state.level = level_by_points(state.points)
    state.personal_offers = personal_offers(state.level)
    return state.model_dump(mode="json")


@app.get("/loyalty/{user_id}/offers")
async def loyalty_offers(user_id: str, city: str | None = None) -> dict:
    state = _load_or_create(user_id)
    offers = personal_offers(state.level, favorite_city=city)
    return {"user_id": user_id, "level": state.level, "offers": offers}
