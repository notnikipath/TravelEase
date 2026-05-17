from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field

from .security import Role


class ServiceType(str, Enum):
    HOTEL = "hotel"
    APARTMENT = "apartment"
    FLIGHT = "flight"
    RAIL = "rail"
    EXCURSION = "excursion"
    ALL_INCLUSIVE_TOUR = "all_inclusive_tour"


class BookingStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"


class LoyaltyLevel(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class CatalogItem(BaseModel):
    item_id: str
    service_type: ServiceType
    name: str
    city: str
    country: str
    base_price: float
    rating: float = Field(ge=0, le=5)
    amenities: list[str] = Field(default_factory=list)
    description: str
    tags: list[str] = Field(default_factory=list)


class SearchFilters(BaseModel):
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    amenities: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    city: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    guests: int = Field(default=1, ge=1, le=12)
    service_type: ServiceType | None = None
    query_text: str | None = None
    filters: SearchFilters = Field(default_factory=SearchFilters)


class SearchResponse(BaseModel):
    items: list[CatalogItem]
    count: int
    source_count: int
    cache_hit: bool = False


class Review(BaseModel):
    review_id: str
    author: str
    rating: int = Field(ge=1, le=5)
    text: str
    sentiment: str | None = None


class ReviewCreateRequest(BaseModel):
    author: str
    rating: int = Field(ge=1, le=5)
    text: str
    actor_role: Role = Role.CUSTOMER


class Promotion(BaseModel):
    promotion_id: str
    title: str
    city: str
    service_type: ServiceType
    discount_percent: float = Field(ge=0, le=100)
    valid_until: date


class CartItemRequest(BaseModel):
    item_id: str
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=12)


class CartItem(BaseModel):
    item_id: str
    start_date: date
    end_date: date
    travelers: int
    price_preview: float


class BookingCreateRequest(BaseModel):
    user_id: str
    cart_items: list[CartItem]
    total_price: float
    loyalty_discount: float = 0


class Booking(BaseModel):
    booking_id: str
    user_id: str
    items: list[CartItem]
    total_price: float
    loyalty_discount: float
    status: BookingStatus
    created_at: datetime


class PaymentRequest(BaseModel):
    booking_id: str
    payment_method: str = Field(default="card")
    amount: float = Field(ge=0)


class PaymentResult(BaseModel):
    payment_id: str
    status: str
    amount: float


class PricingRequest(BaseModel):
    user_id: str | None = None
    item_id: str
    service_type: ServiceType
    start_date: date
    end_date: date
    base_price: float = Field(ge=0)
    demand_index: float = Field(default=0.5, ge=0, le=1)
    promo_discount_percent: float = Field(default=0, ge=0, le=100)
    loyalty_level: LoyaltyLevel = LoyaltyLevel.BRONZE


class PricingResult(BaseModel):
    base_price: float
    dynamic_price: float
    demand_multiplier: float
    competitor_multiplier: float
    season_multiplier: float
    loyalty_discount_amount: float
    promo_discount_amount: float
    savings_vs_competitor: float


class LoyaltyState(BaseModel):
    user_id: str
    points: int
    level: LoyaltyLevel
    personal_offers: list[str]


class EarnPointsRequest(BaseModel):
    user_id: str
    amount: float = Field(ge=0)


class AnalyticsEvent(BaseModel):
    event_type: str
    user_id: str | None = None
    item_id: str | None = None
    city: str | None = None
    amount: float = Field(default=0, ge=0)
    service_type: ServiceType | None = None
    timestamp: datetime
