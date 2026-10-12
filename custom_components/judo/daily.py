"""Daily water consumption derived from the total counter.

The device's own day statistics (FB00) are not reliable while the day is still
running, so today's consumption is counted from the total counter (register
2800) instead. This module holds the bookkeeping and has no Home Assistant
imports, which keeps it testable on its own.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True, slots=True)
class DayMeter:
    """Where today's count stands.

    date    local day (ISO) the count belongs to
    base_l  counter value that corresponds to 0 litres today
    last_l  last counter reading that was accepted
    low     a reading below last_l was seen and waits for confirmation
    since   when the count started (ISO datetime) if that was not midnight
    """

    date: str
    base_l: int
    last_l: int
    low: bool = False
    since: str | None = None

    @property
    def litres(self) -> int:
        return self.last_l - self.base_l

    def as_stored(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "base_l": self.base_l,
            "last_l": self.last_l,
            "low": self.low,
            "since": self.since,
        }

    @classmethod
    def from_stored(cls, data: Any) -> DayMeter | None:
        """Rebuild the meter from stored data, or None if the data is unusable."""
        if not isinstance(data, dict) or not isinstance(data.get("date"), str):
            return None
        if "base_l" not in data and isinstance(data.get("total_l"), int):
            # Written before last_l existed: only the counter value at the start of the day.
            return cls(data["date"], data["total_l"], data["total_l"])
        if not isinstance(data.get("base_l"), int) or not isinstance(data.get("last_l"), int):
            return None
        since = data.get("since")
        return cls(
            data["date"],
            data["base_l"],
            data["last_l"],
            bool(data.get("low")),
            since if isinstance(since, str) else None,
        )


def advance(
    meter: DayMeter | None, today: str, total_l: int, started: str | None = None
) -> DayMeter:
    """Return the meter after a counter reading taken on the local day `today`.

    `started` is the time of the reading; a count that begins without earlier
    state keeps it, because it did not begin at midnight.
    """
    if meter is None:
        return DayMeter(today, total_l, total_l, since=started)
    if meter.date != today:
        # Whatever was used since the last accepted reading belongs to the new day.
        meter = replace(meter, date=today, base_l=meter.last_l, since=None)
    if total_l >= meter.last_l:
        return replace(meter, last_l=total_l, low=False)
    if not meter.low:
        # A single lower reading may be a bad read. Wait for the next one.
        return replace(meter, low=True)
    # Lower twice in a row: the counter restarted. Keep what was counted today.
    return replace(meter, base_l=total_l - meter.litres, last_l=total_l, low=False)
