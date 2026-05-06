#!/usr/bin/env python
"""Calculate dates of next PyCologne meetings."""

from collections.abc import Iterator
from datetime import datetime

from dateutil.rrule import MONTHLY, WE, rrule

__all__ = ("meeting_dates",)


def meeting_dates(count: int = 12) -> Iterator[datetime]:
    """Return iterator yielding datetime instances for next meeting dates.

    Yields *count* items (defaults to twelve).
    """
    return iter(rrule(MONTHLY, byweekday=WE(+2), byhour=19, byminute=0, bysecond=0, count=count))
