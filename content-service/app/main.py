from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.travelease_common import (
    CATALOG_ITEMS,
    PROMOTIONS,
    REVIEWS,
    CatalogItem,
    Promotion,
    Review,
    ReviewCreateRequest,
    Role,
    ServiceType,
    Settings,
    has_permission,
    sentiment_label,
    sentiment_score,
)

settings = Settings(service_name="content-service", service_port=8503)
app = FastAPI(title="TravelEase Content Service", version="1.0.0")

catalog: dict[str, CatalogItem] = {item["item_id"]: CatalogItem(**item) for item in CATALOG_ITEMS}
reviews: dict[str, list[Review]] = {
    item_id: [Review(**review, sentiment=sentiment_label(sentiment_score(review["text"]))) for review in item_reviews]
    for item_id, item_reviews in REVIEWS.items()
}
promotions: list[Promotion] = [Promotion(**promo) for promo in PROMOTIONS]
audit_log: list[dict] = []


def _audit(action: str, details: dict) -> None:
    audit_log.append({"ts": datetime.now(UTC).isoformat(), "action": action, "details": details})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/catalog")
async def get_catalog(city: str | None = None, service_type: ServiceType | None = None) -> dict:
    items = []
    for item in catalog.values():
        if city and item.city.lower() != city.lower():
            continue
        if service_type and item.service_type != service_type:
            continue
        items.append(item.model_dump(mode="json"))
    return {"items": items, "count": len(items)}


@app.get("/catalog/{item_id}")
async def get_catalog_item(item_id: str) -> dict:
    item = catalog.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.model_dump(mode="json")


@app.get("/reviews/{item_id}")
async def get_reviews(item_id: str) -> dict:
    return {"item_id": item_id, "items": [review.model_dump(mode="json") for review in reviews.get(item_id, [])]}


@app.post("/reviews/{item_id}")
async def add_review(item_id: str, request: ReviewCreateRequest) -> dict:
    if not has_permission(request.actor_role, "review:create"):
        raise HTTPException(status_code=403, detail="Role cannot create reviews")
    if item_id not in catalog:
        raise HTTPException(status_code=404, detail="Item not found")
    score = sentiment_score(request.text)
    review = Review(
        review_id=str(uuid4()),
        author=request.author,
        rating=request.rating,
        text=request.text,
        sentiment=sentiment_label(score),
    )
    reviews.setdefault(item_id, []).append(review)
    _audit("review.create", {"item_id": item_id, "sentiment": review.sentiment})
    return review.model_dump(mode="json")


@app.get("/promotions")
async def get_promotions(city: str | None = None, service_type: ServiceType | None = None) -> dict:
    result = []
    for promotion in promotions:
        if city and promotion.city.lower() != city.lower():
            continue
        if service_type and promotion.service_type != service_type:
            continue
        result.append(promotion.model_dump(mode="json"))
    return {"items": result, "count": len(result)}


@app.get("/audit")
async def get_audit(actor_role: Role = Role.ADMIN) -> dict:
    if not has_permission(actor_role, "content:update"):
        raise HTTPException(status_code=403, detail="Access denied")
    return {"items": audit_log[-100:]}
