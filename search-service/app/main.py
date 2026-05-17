from __future__ import annotations

import asyncio
import json
from copy import deepcopy

import httpx
from fastapi import FastAPI, Query

from shared.travelease_common import (
    CATALOG_ITEMS,
    CatalogItem,
    SearchFilters,
    SearchRequest,
    SearchResponse,
    ServiceType,
    Settings,
    TTLCache,
    apply_search_filters,
    merge_ranked_results,
    semantic_tokens,
)

settings = Settings(service_name="search-service", service_port=8501)
app = FastAPI(title="TravelEase Search Service", version="1.0.0")

cache = TTLCache(ttl_seconds=90)
partner_inventory = [
    CatalogItem(**item)
    for item in deepcopy(CATALOG_ITEMS)
    if item["service_type"] in {"hotel", "all_inclusive_tour", "excursion"}
]


async def _search_content_source(request: SearchRequest) -> list[CatalogItem]:
    params: dict[str, str] = {}
    if request.city:
        params["city"] = request.city
    if request.service_type:
        params["service_type"] = request.service_type.value
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(f"{settings.content_service_url}/catalog", params=params)
    response.raise_for_status()
    items = [CatalogItem(**item) for item in response.json().get("items", [])]
    return apply_search_filters(items, request)


async def _search_partner_source(request: SearchRequest) -> list[CatalogItem]:
    await asyncio.sleep(0.02)
    return apply_search_filters(partner_inventory, request)


def _cache_key(request: SearchRequest) -> str:
    payload = request.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/search")
async def search(
    city: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    guests: int = Query(default=1, ge=1, le=12),
    service_type: ServiceType | None = None,
    query_text: str | None = None,
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    amenities: str | None = None,
) -> dict:
    request = SearchRequest(
        city=city,
        start_date=start_date,
        end_date=end_date,
        guests=guests,
        service_type=service_type,
        query_text=query_text,
        filters=SearchFilters(
            price_min=price_min,
            price_max=price_max,
            min_rating=min_rating,
            amenities=[a.strip() for a in amenities.split(",")] if amenities else [],
        ),
    )
    key = _cache_key(request)
    cached = cache.get(key)
    if cached is not None:
        payload = SearchResponse(**cached)
        return payload.model_dump(mode="json") | {"cache_hit": True}

    source_a, source_b = await asyncio.gather(_search_content_source(request), _search_partner_source(request))
    merged = merge_ranked_results(source_a, source_b, max_items=30)
    payload = SearchResponse(items=merged, count=len(merged), source_count=2, cache_hit=False)
    cache.set(key, payload.model_dump(mode="python"))
    return payload.model_dump(mode="json")


@app.get("/search/semantic")
async def semantic_search(query: str) -> dict:
    tokens = sorted(semantic_tokens(query))
    return {"query": query, "semantic_tokens": tokens}


@app.get("/recommendations/{item_id}")
async def recommendations(item_id: str, limit: int = Query(default=4, ge=1, le=20)) -> dict:
    items = [CatalogItem(**item) for item in CATALOG_ITEMS]
    source = next((item for item in items if item.item_id == item_id), None)
    if source is None:
        return {"items": [], "count": 0}
    scored = []
    source_tags = set(source.tags)
    for item in items:
        if item.item_id == item_id:
            continue
        overlap = len(source_tags.intersection(set(item.tags)))
        score = overlap * 2 + item.rating
        scored.append((score, item))
    ranked = [item for _, item in sorted(scored, key=lambda row: row[0], reverse=True)[:limit]]
    return {"items": [item.model_dump(mode="json") for item in ranked], "count": len(ranked)}
