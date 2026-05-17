from __future__ import annotations

from datetime import date

from .schemas import LoyaltyLevel, PricingResult

LOYALTY_DISCOUNT_PERCENT: dict[LoyaltyLevel, float] = {
    LoyaltyLevel.BRONZE: 0.0,
    LoyaltyLevel.SILVER: 0.03,
    LoyaltyLevel.GOLD: 0.06,
    LoyaltyLevel.PLATINUM: 0.1,
}


def _season_multiplier(start_date: date, end_date: date) -> float:
    trip_days = max((end_date - start_date).days, 1)
    summer_peak = {6, 7, 8}
    winter_peak = {12, 1}
    base = 1.0
    if start_date.month in summer_peak:
        base += 0.12
    if start_date.month in winter_peak:
        base += 0.08
    if trip_days >= 7:
        base += 0.03
    return round(base, 4)


def _demand_multiplier(demand_index: float) -> float:
    # Demand index is expected in [0, 1], where 1 means very high demand.
    return round(0.85 + demand_index * 0.45, 4)


def _competitor_multiplier(base_price: float, competitor_price: float | None) -> float:
    if competitor_price is None or competitor_price <= 0:
        return 1.0
    diff_ratio = (competitor_price - base_price) / base_price
    adjustment = max(min(diff_ratio * 0.4, 0.12), -0.08)
    return round(1.0 + adjustment, 4)


def calculate_dynamic_price(
    *,
    base_price: float,
    demand_index: float,
    start_date: date,
    end_date: date,
    loyalty_level: LoyaltyLevel,
    promo_discount_percent: float,
    competitor_price: float | None = None,
) -> PricingResult:
    demand = _demand_multiplier(demand_index)
    season = _season_multiplier(start_date, end_date)
    competitor = _competitor_multiplier(base_price, competitor_price)

    gross = base_price * demand * season * competitor
    loyalty_discount = gross * LOYALTY_DISCOUNT_PERCENT[loyalty_level]
    promo_discount = gross * (promo_discount_percent / 100)
    final_price = max(gross - loyalty_discount - promo_discount, 0)

    savings_vs_competitor = 0.0
    if competitor_price:
        savings_vs_competitor = competitor_price - final_price

    return PricingResult(
        base_price=round(base_price, 2),
        dynamic_price=round(final_price, 2),
        demand_multiplier=demand,
        competitor_multiplier=competitor,
        season_multiplier=season,
        loyalty_discount_amount=round(loyalty_discount, 2),
        promo_discount_amount=round(promo_discount, 2),
        savings_vs_competitor=round(savings_vs_competitor, 2),
    )


def forecast_price_trend(base_price: float, days: int = 14) -> list[dict]:
    points: list[dict] = []
    for day in range(days):
        wave = (day % 7) / 10
        projected = base_price * (1 + wave)
        label = "buy_now" if day <= 2 else ("watch" if day <= 5 else "higher_risk")
        points.append({"day_offset": day, "projected_price": round(projected, 2), "signal": label})
    return points
