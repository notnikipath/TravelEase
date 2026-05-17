from __future__ import annotations

from shared.travelease_common import (
    CATALOG_ITEMS,
    CatalogItem,
    LoyaltyLevel,
    SearchFilters,
    SearchRequest,
    apply_search_filters,
    calculate_dynamic_price,
    conversion_rate,
    points_from_amount,
)
from tests.integration.helpers import trip_window


def test_core_pipeline_math() -> None:
    start, end = trip_window()
    hotels = [CatalogItem(**item) for item in CATALOG_ITEMS if item["service_type"] == "hotel"]
    search_request = SearchRequest(city="Sochi", query_text="beach", filters=SearchFilters(min_rating=4.5))
    filtered = apply_search_filters(hotels, search_request)
    assert filtered
    assert all(item.city == "Sochi" for item in filtered)

    base_price = hotels[0].base_price
    quote = calculate_dynamic_price(
        base_price=base_price,
        demand_index=0.8,
        start_date=start,
        end_date=end,
        loyalty_level=LoyaltyLevel.SILVER,
        promo_discount_percent=5,
        competitor_price=base_price * 1.1,
    )
    assert quote.dynamic_price > 0
    assert points_from_amount(quote.dynamic_price) >= 1
    assert conversion_rate(search_count=1000, booking_count=80) == 8.0
