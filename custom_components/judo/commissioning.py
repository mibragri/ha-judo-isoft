"""The commissioning date the user can set, since the device's own date is not reliable.

No Home Assistant imports, so it can be tested on its own.
"""
from __future__ import annotations

from datetime import date
from typing import Any


def parse_date(value: Any) -> date | None:
    """Return the stored ISO date, or None when nothing usable is stored."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def days_in_service(commissioned: date, today: date) -> int | None:
    """Days since commissioning; None for a date that lies in the future."""
    days = (today - commissioned).days
    return days if days >= 0 else None
