from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.consultation import ConsultationRequest, ConsultationResponse
from app.schemas.follow_up import FollowUpRequest, FollowUpResponse
from app.services.consultation import ConsultationService
from app.services.follow_up import FollowUpService

router = APIRouter(prefix="/consultations", tags=["consultations"])


@router.post("", response_model=ConsultationResponse)
async def create_consultation(
    body: ConsultationRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ConsultationResponse:
    service = ConsultationService(settings=settings, db=db)
    return await service.create(body)


@router.post("/{consultation_id}/follow-ups", response_model=FollowUpResponse)
async def create_follow_up(
    consultation_id: str,
    body: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> FollowUpResponse:
    return await FollowUpService(settings=settings, db=db).create(
        consultation_id, body.question
    )
