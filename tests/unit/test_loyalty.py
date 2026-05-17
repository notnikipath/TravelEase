from __future__ import annotations

from shared.travelease_common import LoyaltyLevel, level_by_points, personal_offers, points_from_amount


def test_level_boundaries() -> None:
    assert level_by_points(0) == LoyaltyLevel.BRONZE
    assert level_by_points(1000) == LoyaltyLevel.SILVER
    assert level_by_points(3000) == LoyaltyLevel.GOLD
    assert level_by_points(7000) == LoyaltyLevel.PLATINUM


def test_points_conversion() -> None:
    assert points_from_amount(399.0) == 19
    assert points_from_amount(400.0) == 20


def test_offers_increase_with_level() -> None:
    bronze = personal_offers(LoyaltyLevel.BRONZE, favorite_city="Sochi")
    platinum = personal_offers(LoyaltyLevel.PLATINUM, favorite_city="Sochi")
    assert len(platinum) > len(bronze)
