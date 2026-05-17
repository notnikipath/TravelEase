from __future__ import annotations

from datetime import date, timedelta

from shared.travelease_common import LoyaltyLevel, calculate_dynamic_price


def test_dynamic_price_reacts_to_demand() -> None:
    start = date.today() + timedelta(days=5)
    end = start + timedelta(days=4)
    high_demand = calculate_dynamic_price(
        base_price=10000,
        demand_index=0.9,
        start_date=start,
        end_date=end,
        loyalty_level=LoyaltyLevel.BRONZE,
        promo_discount_percent=0,
        competitor_price=11500,
    )
    low_demand = calculate_dynamic_price(
        base_price=10000,
        demand_index=0.2,
        start_date=start,
        end_date=end,
        loyalty_level=LoyaltyLevel.BRONZE,
        promo_discount_percent=0,
        competitor_price=11500,
    )
    assert high_demand.dynamic_price > low_demand.dynamic_price


def test_loyalty_discount_is_applied() -> None:
    start = date.today() + timedelta(days=15)
    end = start + timedelta(days=6)
    bronze = calculate_dynamic_price(
        base_price=12000,
        demand_index=0.5,
        start_date=start,
        end_date=end,
        loyalty_level=LoyaltyLevel.BRONZE,
        promo_discount_percent=0,
        competitor_price=12200,
    )
    platinum = calculate_dynamic_price(
        base_price=12000,
        demand_index=0.5,
        start_date=start,
        end_date=end,
        loyalty_level=LoyaltyLevel.PLATINUM,
        promo_discount_percent=0,
        competitor_price=12200,
    )
    assert platinum.dynamic_price < bronze.dynamic_price
