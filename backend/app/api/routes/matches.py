from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_access_scope, require_roles
from app.core.db import get_db
from app.models import User
from app.schemas.matching import MatchSuggestionRequest, MatchSuggestionResponse
from app.services.access import AccessScope, ensure_student_access, ensure_teacher_access
from app.services.matching import suggest_slots


router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/suggest", response_model=MatchSuggestionResponse)
def suggest_match_slots(
    payload: MatchSuggestionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "staff_scheduler", "viewer")),
    scope: AccessScope = Depends(get_access_scope),
) -> MatchSuggestionResponse:
    ensure_teacher_access(scope, payload.teacher_id)
    if payload.student_id is not None:
        ensure_student_access(db, scope, payload.student_id)
    suggestions, rejected_slots = suggest_slots(db, payload)
    return MatchSuggestionResponse(suggestions=suggestions, rejected_slots=rejected_slots)
