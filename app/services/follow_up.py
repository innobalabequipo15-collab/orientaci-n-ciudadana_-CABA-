"""Etapa 6 — preguntas dentro del mismo caso (solo contexto persistido)."""

from __future__ import annotations

import json
import logging
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Consultation, ConsultationFollowUp
from app.providers.llm import LLMClient, LLMUnavailableError
from app.providers.mock_follow_up import mock_follow_up
from app.schemas.follow_up import FollowUpResponse

logger = logging.getLogger(__name__)

FOLLOW_UP_PROMPT_VERSION = "followup-v1"

SYSTEM_PROMPT = """Sos un asistente de orientacion ciudadana para CABA.
Respondé SOLO con JSON valido (sin markdown):
{"answer": "texto en espanol argentino, 1 a 8 oraciones"}

Reglas:
- Usá UNICAMENTE el contexto JSON de la consulta ya recuperada.
- NO inventes requisitos, documentos, oficinas ni URLs.
- Si la pregunta no puede responderse con el contexto, decilo claramente.
"""

FOLLOW_UP_ALLOWED_STATUSES = frozenset({"complete", "partial"})


class FollowUpService:
    def __init__(self, settings: Settings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db
        self.llm = LLMClient(settings)

    async def create(self, consultation_id: str, question: str) -> FollowUpResponse:
        row = await self.db.get(Consultation, consultation_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada",
            )
        if row.status not in FOLLOW_UP_ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"La consulta está en estado '{row.status}' y no admite seguimiento. "
                    "Completá ubicación o actividad primero."
                ),
            )

        payload = row.payload or {}
        snapshot = payload.get("response_snapshot")
        if not isinstance(snapshot, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Esta consulta no tiene contexto persistido (consulta anterior al MVP). "
                    "Creá una consulta nueva."
                ),
            )

        answer, provider = await self._answer(question=question.strip(), snapshot=snapshot)
        follow_up_id = f"followup-{uuid4().hex[:12]}"
        self.db.add(
            ConsultationFollowUp(
                id=follow_up_id,
                consultation_id=consultation_id,
                question=question.strip(),
                answer=answer,
                provider=provider,
            )
        )
        await self.db.commit()

        return FollowUpResponse(
            follow_up_id=follow_up_id,
            consultation_id=consultation_id,
            question=question.strip(),
            answer=answer,
            message=f"followup:{provider}:{FOLLOW_UP_PROMPT_VERSION}",
        )

    async def _answer(
        self, *, question: str, snapshot: dict
    ) -> tuple[str, str]:
        provider = "llm" if self.llm.is_configured else "mock"
        if provider == "llm":
            try:
                raw = await self.llm.complete_json(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=(
                        f"Pregunta del ciudadano:\n{question}\n\n"
                        f"Contexto oficial (unico material permitido):\n"
                        f"{json.dumps(snapshot, ensure_ascii=False)}"
                    ),
                )
                answer = str(raw.get("answer") or "").strip()
                if answer:
                    return answer, provider
            except LLMUnavailableError as exc:
                logger.warning("Follow-up LLM unavailable, using mock: %s", exc)
                provider = "mock"

        return mock_follow_up(question=question, snapshot=snapshot), provider
