from __future__ import annotations

from datetime import date, timedelta


def trip_window(days_until_start: int = 7, duration_days: int = 5) -> tuple[date, date]:
    start = date.today() + timedelta(days=days_until_start)
    end = start + timedelta(days=duration_days)
    return start, end
