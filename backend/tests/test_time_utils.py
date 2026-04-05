from datetime import date

from app.services.time_utils import contains_range, ranges_overlap, session_is_active_on_date_range


def test_ranges_overlap_detects_partial_overlap() -> None:
    assert ranges_overlap(600, 660, 630, 690) is True


def test_ranges_overlap_treats_touching_edges_as_non_overlapping() -> None:
    assert ranges_overlap(600, 660, 660, 720) is False


def test_contains_range_requires_full_containment() -> None:
    assert contains_range(600, 720, 630, 690) is True
    assert contains_range(600, 720, 570, 690) is False


def test_session_is_active_on_date_range_honors_end_date() -> None:
    assert session_is_active_on_date_range(date(2026, 1, 1), date(2026, 3, 1), date(2026, 4, 1), None) is False
    assert session_is_active_on_date_range(date(2026, 1, 1), date(2026, 3, 1), None, date(2026, 2, 1)) is True
