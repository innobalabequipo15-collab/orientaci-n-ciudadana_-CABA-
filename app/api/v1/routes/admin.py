"""Admin login + analytics endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_key
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.admin import (
    AdminConsultationList,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminStatsSummary,
    AdminUserOut,
)
from app.services.admin_stats import AdminStatsService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    body: AdminLoginRequest,
    settings: Settings = Depends(get_settings),
) -> AdminLoginResponse:
    email = body.email.strip().lower()
    password = body.password
    if (
        email != settings.admin_email.strip().lower()
        or password != settings.admin_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales admin invalidas",
        )
    local = email.split("@")[0] or "Admin"
    return AdminLoginResponse(
        token=settings.admin_api_key,
        user=AdminUserOut(
            email=settings.admin_email,
            name=local.capitalize(),
            last_name="Admin",
            role_id=99,
            position="Administrador",
        ),
    )


@router.get(
    "/stats/summary",
    response_model=AdminStatsSummary,
    dependencies=[Depends(require_admin_key)],
)
async def admin_stats_summary(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsSummary:
    return await AdminStatsService(db).summary(from_date=from_date, to_date=to_date)


@router.get(
    "/consultations",
    response_model=AdminConsultationList,
    dependencies=[Depends(require_admin_key)],
)
async def admin_list_consultations(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> AdminConsultationList:
    return await AdminStatsService(db).list_consultations(
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )
