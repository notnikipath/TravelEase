from __future__ import annotations

import asyncio
from datetime import date, timedelta

import httpx


async def book_hotel(user_id: str, item_id: str, start_date: date, end_date: date) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        available = await client.post(
            "http://localhost:8500/workflow/book-hotel",
            json={
                "user_id": user_id,
                "item_id": item_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "travelers": 2,
                "payment_method": "card",
            },
        )
    available.raise_for_status()
    return available.json()


async def main() -> None:
    start = date.today() + timedelta(days=6)
    end = start + timedelta(days=5)
    result = await book_hotel("user-demo", "HTL-003", start, end)
    print("Booking ID:", result["booking"]["booking_id"])
    print("Total:", result["booking"]["total_price"])
    print("Loyalty:", result["loyalty"]["level"])


if __name__ == "__main__":
    asyncio.run(main())
