from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

US_EASTERN = ZoneInfo("America/New_York")
INDIA = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")


def us_trading_session_bounds(dt: datetime) -> tuple[datetime, datetime]:
    local = dt.astimezone(US_EASTERN)
    start = datetime(local.year, local.month, local.day, 9, 30, tzinfo=US_EASTERN)
    end = datetime(local.year, local.month, local.day, 16, 0, tzinfo=US_EASTERN)
    return start, end


def is_within_session(ts: datetime, start: datetime, end: datetime) -> bool:
    return start <= ts <= end