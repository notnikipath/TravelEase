from __future__ import annotations

from .schemas import LoyaltyLevel


def level_by_points(points: int) -> LoyaltyLevel:
    if points >= 7000:
        return LoyaltyLevel.PLATINUM
    if points >= 3000:
        return LoyaltyLevel.GOLD
    if points >= 1000:
        return LoyaltyLevel.SILVER
    return LoyaltyLevel.BRONZE


def points_from_amount(amount: float) -> int:
    return int(amount // 20)


def personal_offers(level: LoyaltyLevel, favorite_city: str | None = None) -> list[str]:
    city = favorite_city or "your next destination"
    base = [f"Free cancellation upgrade for trips to {city}"]
    if level in {LoyaltyLevel.SILVER, LoyaltyLevel.GOLD, LoyaltyLevel.PLATINUM}:
        base.append("Priority support in booking chat")
    if level in {LoyaltyLevel.GOLD, LoyaltyLevel.PLATINUM}:
        base.append("10% discount on selected all-inclusive tours")
    if level == LoyaltyLevel.PLATINUM:
        base.append("Complimentary airport transfer once per quarter")
    return base
