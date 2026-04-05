from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Session as SessionModel
from app.models import Student, Teacher
from app.schemas.matching import MatchSuggestion, MatchSuggestionRequest, RejectedSlot
from app.schemas.student import StudentBlockedTimeCreate, StudentPreferenceCreate
from app.services.time_utils import (
    WeeklyWindow,
    contains_range,
    intersects_window,
    ranges_overlap,
    session_is_active_on_date_range,
)


@dataclass(frozen=True)
class RankedCandidate:
    weekday: int
    start_minute: int
    end_minute: int
    score: int
    reasons: list[str]
    score_breakdown: dict[str, int]


def load_student_constraints(
    db: Session,
    student_id: int | None,
    request_preferences: list[StudentPreferenceCreate],
    request_blocked_times: list[StudentBlockedTimeCreate],
) -> tuple[list[StudentPreferenceCreate], list[StudentBlockedTimeCreate], Student | None]:
    student = db.get(Student, student_id) if student_id is not None else None
    if student_id is not None and student is None:
        return request_preferences, request_blocked_times, None

    preferences = request_preferences or [
        StudentPreferenceCreate.model_validate(
            {
                "weekday": preference.weekday,
                "start_minute": preference.start_minute,
                "end_minute": preference.end_minute,
                "priority": preference.priority,
            }
        )
        for preference in (student.preferences if student is not None else [])
    ]
    blocked_times = request_blocked_times or [
        StudentBlockedTimeCreate.model_validate(
            {
                "weekday": blocked.weekday,
                "start_minute": blocked.start_minute,
                "end_minute": blocked.end_minute,
                "reason": blocked.reason,
            }
        )
        for blocked in (student.blocked_times if student is not None else [])
    ]
    return preferences, blocked_times, student


def fetch_relevant_sessions(
    db: Session,
    teacher_id: int,
    student_id: int | None,
    request_start: date | None,
    request_end: date | None,
) -> tuple[list[SessionModel], list[SessionModel]]:
    teacher_sessions = list(
        db.scalars(select(SessionModel).where(SessionModel.teacher_id == teacher_id, SessionModel.status == "active"))
    )
    student_sessions: list[SessionModel] = []
    if student_id is not None:
        student_sessions = list(
            db.scalars(select(SessionModel).where(SessionModel.student_id == student_id, SessionModel.status == "active"))
        )

    teacher_sessions = [
        session
        for session in teacher_sessions
        if session_is_active_on_date_range(session.start_date, session.end_date, request_start, request_end)
    ]
    student_sessions = [
        session
        for session in student_sessions
        if session_is_active_on_date_range(session.start_date, session.end_date, request_start, request_end)
    ]
    return teacher_sessions, student_sessions


def score_candidate(
    candidate: WeeklyWindow,
    preference: StudentPreferenceCreate,
    teacher_sessions_by_day: dict[int, list[SessionModel]],
    student_sessions_by_day: dict[int, list[SessionModel]],
) -> RankedCandidate:
    reasons: list[str] = []
    score_breakdown: dict[str, int] = {}
    score = max(0, 100 - ((preference.priority - 1) * 10))
    score_breakdown["preference_fit"] = score
    reasons.append(f"preference priority {preference.priority}")

    adjacent_teacher = any(
        session.end_minute == candidate.start_minute or session.start_minute == candidate.end_minute
        for session in teacher_sessions_by_day[candidate.weekday]
    )
    score_breakdown["teacher_compactness"] = 15 if adjacent_teacher else 0
    if adjacent_teacher:
        score += 15
        reasons.append("adjacent to existing teacher session")

    adjacent_student = any(
        session.end_minute == candidate.start_minute or session.start_minute == candidate.end_minute
        for session in student_sessions_by_day[candidate.weekday]
    )
    score_breakdown["student_compactness"] = 10 if adjacent_student else 0
    if adjacent_student:
        score += 10
        reasons.append("adjacent to existing student session")

    earlier_bonus = max(0, 40 - (candidate.start_minute // 30))
    score_breakdown["earlier_slot_bonus"] = earlier_bonus
    score += earlier_bonus
    reasons.append("earlier slot bonus")

    return RankedCandidate(
        weekday=candidate.weekday,
        start_minute=candidate.start_minute,
        end_minute=candidate.end_minute,
        score=score,
        reasons=reasons,
        score_breakdown=score_breakdown,
    )


def suggest_slots(db: Session, request: MatchSuggestionRequest) -> tuple[list[MatchSuggestion], list[RejectedSlot]]:
    teacher = db.get(Teacher, request.teacher_id)
    if teacher is None or not teacher.active:
        return [], []

    preferences, blocked_times, student = load_student_constraints(
        db=db,
        student_id=request.student_id,
        request_preferences=request.student_preferences,
        request_blocked_times=request.student_blocked_times,
    )
    if request.student_id is not None and student is None:
        return [], []
    if not preferences:
        return [], []

    availability = [WeeklyWindow(slot.weekday, slot.start_minute, slot.end_minute) for slot in teacher.availability_slots]
    preference_windows = [WeeklyWindow(pref.weekday, pref.start_minute, pref.end_minute) for pref in preferences]
    blocked_windows = [WeeklyWindow(item.weekday, item.start_minute, item.end_minute) for item in blocked_times]

    teacher_sessions, student_sessions = fetch_relevant_sessions(
        db=db,
        teacher_id=request.teacher_id,
        student_id=request.student_id,
        request_start=request.start_date,
        request_end=request.end_date,
    )
    teacher_sessions_by_day = defaultdict(list)
    student_sessions_by_day = defaultdict(list)
    for session in teacher_sessions:
        teacher_sessions_by_day[session.weekday].append(session)
    for session in student_sessions:
        student_sessions_by_day[session.weekday].append(session)

    ranked: dict[tuple[int, int, int], RankedCandidate] = {}
    rejected_slots: list[RejectedSlot] = []

    for preference, preference_window in zip(preferences, preference_windows):
        for available_window in availability:
            intersection = intersects_window(available_window, preference_window)
            if intersection is None:
                continue

            latest_start = intersection.end_minute - request.duration_minutes
            current_start = intersection.start_minute
            while current_start <= latest_start:
                current_end = current_start + request.duration_minutes
                candidate = WeeklyWindow(intersection.weekday, current_start, current_end)

                if not contains_range(intersection.start_minute, intersection.end_minute, current_start, current_end):
                    current_start += request.increment_minutes
                    continue

                rejection_reasons: list[str] = []
                if any(
                    item.weekday == candidate.weekday
                    and ranges_overlap(candidate.start_minute, candidate.end_minute, item.start_minute, item.end_minute)
                    for item in blocked_windows
                ):
                    rejection_reasons.append("Blocked by student unavailability")

                if any(
                    session.weekday == candidate.weekday
                    and ranges_overlap(candidate.start_minute, candidate.end_minute, session.start_minute, session.end_minute)
                    for session in teacher_sessions_by_day[candidate.weekday]
                ):
                    rejection_reasons.append("Conflicts with another teacher session")

                if any(
                    session.weekday == candidate.weekday
                    and ranges_overlap(candidate.start_minute, candidate.end_minute, session.start_minute, session.end_minute)
                    for session in student_sessions_by_day[candidate.weekday]
                ):
                    rejection_reasons.append("Conflicts with another student session")

                if rejection_reasons:
                    if request.include_rejections and len(rejected_slots) < request.max_rejections:
                        rejected_slots.append(
                            RejectedSlot(
                                weekday=candidate.weekday,
                                start_minute=candidate.start_minute,
                                end_minute=candidate.end_minute,
                                reasons=rejection_reasons,
                            )
                        )
                    current_start += request.increment_minutes
                    continue

                scored = score_candidate(candidate, preference, teacher_sessions_by_day, student_sessions_by_day)
                key = (scored.weekday, scored.start_minute, scored.end_minute)
                existing = ranked.get(key)
                if existing is None or scored.score > existing.score:
                    ranked[key] = scored

                current_start += request.increment_minutes

    suggestions = [
        MatchSuggestion(
            weekday=item.weekday,
            start_minute=item.start_minute,
            end_minute=item.end_minute,
            score=item.score,
            reasons=item.reasons,
            score_breakdown=item.score_breakdown,
        )
        for item in sorted(ranked.values(), key=lambda item: (-item.score, item.weekday, item.start_minute))
    ]
    return suggestions, rejected_slots
