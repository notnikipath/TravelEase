from __future__ import annotations

from .schemas import CatalogItem, SearchRequest

SEMANTIC_HINTS: dict[str, set[str]] = {
    "all inclusive": {"all_inclusive", "all_inclusive_tour", "resort"},
    "beach": {"beach", "resort", "sea"},
    "business": {"business", "city_center"},
    "museum": {"culture", "museum", "guided"},
    "family": {"family", "kids_club"},
    "апартаменты": {"apartment", "long_stay"},
    "экскурсия": {"excursion", "guided", "culture"},
    "все включено": {"all_inclusive", "all_inclusive_tour", "resort"},
}


def semantic_tokens(query: str | None) -> set[str]:
    if not query:
        return set()
    normalized = query.strip().lower()
    tokens = set(normalized.replace("-", " ").split())
    for key, mapped in SEMANTIC_HINTS.items():
        if key in normalized:
            tokens.update(mapped)
    return tokens


def apply_search_filters(items: list[CatalogItem], request: SearchRequest) -> list[CatalogItem]:
    tokens = semantic_tokens(request.query_text)
    result: list[CatalogItem] = []
    amenities = {a.lower() for a in request.filters.amenities}
    city_query = request.city.lower() if request.city else None
    for item in items:
        if city_query and item.city.lower() != city_query:
            continue
        if request.service_type and item.service_type != request.service_type:
            continue
        if request.filters.price_min is not None and item.base_price < request.filters.price_min:
            continue
        if request.filters.price_max is not None and item.base_price > request.filters.price_max:
            continue
        if request.filters.min_rating is not None and item.rating < request.filters.min_rating:
            continue
        if amenities and not amenities.issubset({a.lower() for a in item.amenities}):
            continue
        if tokens:
            searchable = " ".join(
                [item.name, item.description, item.service_type.value, *item.tags, *item.amenities]
            ).lower()
            if not any(token in searchable for token in tokens):
                continue
        result.append(item)
    return result


def merge_ranked_results(*sources: list[CatalogItem], max_items: int = 25) -> list[CatalogItem]:
    seen: set[str] = set()
    merged: list[CatalogItem] = []
    for source in sources:
        for item in sorted(source, key=lambda x: (x.rating, -x.base_price), reverse=True):
            if item.item_id in seen:
                continue
            seen.add(item.item_id)
            merged.append(item)
            if len(merged) >= max_items:
                return merged
    return merged
