import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

from app.core.config import get_settings
from app.schemas.scheduling import OccurrenceRead


settings = get_settings()
calendar_timezone = ZoneInfo(settings.timezone_name)


def build_ics_calendar(name: str, occurrences: list[OccurrenceRead]) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Timetabling Assistant//EN")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", name)

    for occurrence in occurrences:
        event = Event()
        starts_at = datetime.combine(
            occurrence.effective_date,
            datetime.min.time(),
            tzinfo=calendar_timezone,
        ) + timedelta(minutes=occurrence.start_minute)
        ends_at = datetime.combine(
            occurrence.effective_date,
            datetime.min.time(),
            tzinfo=calendar_timezone,
        ) + timedelta(minutes=occurrence.end_minute)
        event.add("uid", f"session-{occurrence.session_id}-{occurrence.occurrence_date.isoformat()}@timetabling")
        event.add("summary", occurrence.subject or "Lesson")
        event.add("dtstart", starts_at)
        event.add("dtend", ends_at)
        event.add("description", "; ".join(occurrence.impact_reasons) or occurrence.occurrence_status)
        event.add("status", "CANCELLED" if occurrence.occurrence_status == "cancelled" else "CONFIRMED")
        event.add("dtstamp", datetime.now(timezone.utc))
        calendar.add_component(event)

    return calendar.to_ical()


def issue_feed_token() -> str:
    return secrets.token_urlsafe(32)


def hash_feed_token(token: str) -> str:
    return hmac.new(
        settings.resolved_calendar_token_secret.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
