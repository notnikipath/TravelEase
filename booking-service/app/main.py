from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.travelease_common import (
    Booking,
    BookingStatus,
    CartItem,
    CartItemRequest,
    PaymentResult,
    Settings,
)

settings = Settings(service_name="booking-service", service_port=8502)
app = FastAPI(title="TravelEase Booking Service", version="1.0.0")

carts: dict[str, list[CartItem]] = {}
bookings: dict[str, Booking] = {}
reservations: dict[str, list[tuple[date, date]]] = {}


class CheckoutRequest(BaseModel):
    user_id: str
    payment_method: str = "card"


def _overlap(start_a: date, end_a: date, start_b: date, end_b: date) -> bool:
    return start_a < end_b and start_b < end_a


def _is_available(item_id: str, start_date: date, end_date: date) -> bool:
    for reserved_start, reserved_end in reservations.get(item_id, []):
        if _overlap(start_date, end_date, reserved_start, reserved_end):
            return False
    return True


async def _quote_item(user_id: str, item: CartItem) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        quote = await client.get(
            f"{settings.pricing_service_url}/pricing/quote",
            params={
                "item_id": item.item_id,
                "user_id": user_id,
                "start_date": item.start_date.isoformat(),
                "end_date": item.end_date.isoformat(),
            },
        )
    if quote.status_code >= 400:
        raise HTTPException(status_code=quote.status_code, detail=f"Pricing failed for item {item.item_id}")
    return quote.json()


async def _load_catalog_item(item_id: str) -> dict:
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(f"{settings.content_service_url}/catalog/{item_id}")
    if response.status_code >= 400:
        raise HTTPException(status_code=404, detail=f"Catalog item {item_id} not found")
    return response.json()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/availability/check")
async def check_availability(item_id: str, start_date: date, end_date: date) -> dict:
    return {"item_id": item_id, "available": _is_available(item_id, start_date, end_date)}


@app.post("/cart/{user_id}/items")
async def add_to_cart(user_id: str, request: CartItemRequest) -> dict:
    if request.end_date <= request.start_date:
        raise HTTPException(status_code=400, detail="end_date must be greater than start_date")
    if not _is_available(request.item_id, request.start_date, request.end_date):
        raise HTTPException(status_code=409, detail="Requested dates are not available")
    quote_payload = await _quote_item(
        user_id,
        CartItem(
            item_id=request.item_id,
            start_date=request.start_date,
            end_date=request.end_date,
            travelers=request.travelers,
            price_preview=0,
        ),
    )
    dynamic_price = float(quote_payload["price"]["dynamic_price"])
    cart_item = CartItem(
        item_id=request.item_id,
        start_date=request.start_date,
        end_date=request.end_date,
        travelers=request.travelers,
        price_preview=dynamic_price,
    )
    carts.setdefault(user_id, []).append(cart_item)
    return {"user_id": user_id, "item": cart_item.model_dump(mode="json"), "cart_size": len(carts[user_id])}


@app.get("/cart/{user_id}")
async def get_cart(user_id: str) -> dict:
    items = carts.get(user_id, [])
    total_preview = round(sum(item.price_preview for item in items), 2)
    return {
        "user_id": user_id,
        "items": [item.model_dump(mode="json") for item in items],
        "total_preview": total_preview,
    }


@app.delete("/cart/{user_id}/clear")
async def clear_cart(user_id: str) -> dict:
    carts[user_id] = []
    return {"status": "cleared"}


@app.post("/bookings/checkout")
async def checkout(request: CheckoutRequest) -> dict:
    cart_items = carts.get(request.user_id, [])
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_price = 0.0
    priced_items: list[CartItem] = []
    first_item_city = "unknown"
    first_item_service_type = "hotel"
    for cart_item in cart_items:
        if not _is_available(cart_item.item_id, cart_item.start_date, cart_item.end_date):
            raise HTTPException(status_code=409, detail=f"{cart_item.item_id} is no longer available")
        quote_payload = await _quote_item(request.user_id, cart_item)
        dynamic_price = float(quote_payload["price"]["dynamic_price"])
        priced_items.append(cart_item.model_copy(update={"price_preview": dynamic_price}))
        total_price += dynamic_price
        catalog_item = await _load_catalog_item(cart_item.item_id)
        first_item_city = catalog_item["city"]
        first_item_service_type = catalog_item["service_type"]

    booking = Booking(
        booking_id=f"BK-{uuid4()}",
        user_id=request.user_id,
        items=priced_items,
        total_price=round(total_price, 2),
        loyalty_discount=0,
        status=BookingStatus.CREATED,
        created_at=datetime.now(UTC),
    )
    bookings[booking.booking_id] = booking

    payment = PaymentResult(payment_id=f"PAY-{uuid4()}", status="success", amount=booking.total_price)
    booking.status = BookingStatus.CONFIRMED

    for item in booking.items:
        reservations.setdefault(item.item_id, []).append((item.start_date, item.end_date))

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{settings.loyalty_service_url}/loyalty/earn",
            json={"user_id": request.user_id, "amount": booking.total_price},
        )
        await client.post(
            f"{settings.analytics_service_url}/analytics/events/booking",
            json={
                "user_id": request.user_id,
                "booking_id": booking.booking_id,
                "amount": booking.total_price,
                "city": first_item_city,
                "service_type": first_item_service_type,
            },
        )
        await client.post(
            f"{settings.notification_service_url}/notify/booking-confirmation",
            json={
                "user_id": request.user_id,
                "booking_id": booking.booking_id,
                "amount": booking.total_price,
                "channel": "email",
            },
        )

    carts[request.user_id] = []
    return {"booking": booking.model_dump(mode="json"), "payment": payment.model_dump(mode="json")}


@app.get("/bookings/{booking_id}")
async def get_booking(booking_id: str) -> dict:
    booking = bookings.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking.model_dump(mode="json")


@app.get("/bookings")
async def list_bookings(user_id: str | None = None) -> dict:
    items = []
    for booking in bookings.values():
        if user_id and booking.user_id != user_id:
            continue
        items.append(booking.model_dump(mode="json"))
    return {"items": items, "count": len(items)}
