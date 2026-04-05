from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_access_scope
from app.core.db import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.access import AccessScope
from app.services.dashboard import build_dashboard


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> DashboardSummary:
    return build_dashboard(db, scope)
