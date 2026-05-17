from __future__ import annotations

from shared.travelease_common import (
    CATALOG_ITEMS,
    CatalogItem,
    SearchFilters,
    SearchRequest,
    apply_search_filters,
    semantic_tokens,
)


def test_semantic_tokens_russian_and_english() -> None:
    tokens = semantic_tokens("все включено beach")
    assert "all_inclusive_tour" in tokens
    assert "beach" in tokens


def test_filter_by_city_and_rating() -> None:
    items = [CatalogItem(**item) for item in CATALOG_ITEMS]
    request = SearchRequest(city="Sochi", filters=SearchFilters(min_rating=4.7))
    results = apply_search_filters(items, request)
    assert results
    assert all(item.city == "Sochi" and item.rating >= 4.7 for item in results)
