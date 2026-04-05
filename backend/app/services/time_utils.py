from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class WeeklyWindow:
    weekday: int
    start_minute: int
    end_minute: int


def ranges_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def contains_range(outer_start: int, outer_end: int, inner_start: int, inner_end: int) -> bool:
    return outer_start <= inner_start and inner_end <= outer_end


def intersects_window(first: WeeklyWindow, second: WeeklyWindow) -> WeeklyWindow | None:
    if first.weekday != second.weekday:
        return None
    start = max(first.start_minute, second.start_minute)
    end = min(first.end_minute, second.end_minute)
    if start >= end:
        return None
    return WeeklyWindow(weekday=first.weekday, start_minute=start, end_minute=end)


def session_is_active_on_date_range(
    session_start: date,
    session_end: date | None,
    request_start: date | None,
    request_end: date | None,
) -> bool:
    effective_start = request_start or session_start
    if session_end is not None and effective_start > session_end:
        return False
    if request_end is not None and request_end < session_start:
        return False
    return True


def daterange(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)
