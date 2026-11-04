"""Etapa 5 — explicacion ciudadana solo con contexto recuperado."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.providers.llm import LLMClient, LLMUnavailableError
from app.providers.mock_explainer import mock_explain
from app.schemas.consultation import (
    DocumentItem,
    OfficeItem,
    RequirementItem,
    SourceItem,
    StepItem,
    TerritorialItem,
)
from app.schemas.zoning import ZoningOut

logger = logging.getLogger(__name__)

EXPLAIN_PROMPT_VERSION = "explain-v1"

SYSTEM_PROMPT = """Sos un redactor de orientacion ciudadana para CABA (Buenos Aires).
Debes devolver SOLO un JSON valido (sin markdown) con este esquema:
{
  "summary": "texto en espanol argentino, claro, 2 a 6 oraciones",
  "missing_information_notes": ["string"]
}

Reglas estrictas:
- Usa UNICAMENTE los hechos del contexto JSON que te pasan.
- NO inventes requisitos, documentos, pasos, oficinas, normas ni URLs.
- Si requirements esta vacio, di explicitamente que no hay requisitos recuperados.
- Podes mencionar titulos que ya figuren en requirements/steps/documents/offices.
- Si falta informacion (missing/warnings), indicalo en summary o missing_information_notes.
- No agregues consejos legales definitivos; orienta a validar con las fuentes citadas.
"""


@dataclass
class ExplanationResult:
    summary: str
    missing_information_notes: list[str]
    provider: str
    prompt_version: str = EXPLAIN_PROMPT_VERSION


class ExplanationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = LLMClient(settings)

    async def explain(
        self,
        *,
        activity_name: str,
        activity_code: str,
        normalized_address: str | None,
        commune: str | None,
        neighborhood: str | None,
        requirements: list[RequirementItem],
        steps: list[StepItem],
        documents: list[DocumentItem],
        territorial_information: list[TerritorialItem],
        online_procedures: list[OfficeItem],
        physical_offices: list[OfficeItem],
        sources: list[SourceItem],
        zoning: ZoningOut | None,
        missing: list[str],
        warnings: list[str],
    ) -> ExplanationResult:
        context = self._build_context(
            activity_name=activity_name,
            activity_code=activity_code,
            normalized_address=normalized_address,
            commune=commune,
            neighborhood=neighborhood,
            requirements=requirements,
            steps=steps,
            documents=documents,
            territorial_information=territorial_information,
            online_procedures=online_procedures,
            physical_offices=physical_offices,
            sources=sources,
            zoning=zoning,
            missing=missing,
            warnings=warnings,
        )

        provider = "llm" if self.llm.is_configured else "mock"
        if provider == "llm":
            try:
                raw = await self._explain_with_llm(context)
            except LLMUnavailableError as exc:
                logger.warning("Explain LLM unavailable, using mock: %s", exc)
                raw = mock_explain(context)
                provider = "mock"
        else:
            raw = mock_explain(context)

        return self._validate(raw=raw, context=context, provider=provider)

    def _build_context(
        self,
        *,
        activity_name: str,
        activity_code: str,
        normalized_address: str | None,
        commune: str | None,
        neighborhood: str | None,
        requirements: list[RequirementItem],
        steps: list[StepItem],
        documents: list[DocumentItem],
        territorial_information: list[TerritorialItem],
        online_procedures: list[OfficeItem],
        physical_offices: list[OfficeItem],
        sources: list[SourceItem],
        zoning: ZoningOut | None,
        missing: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        zoning_payload: dict[str, Any] = {}
        if zoning is not None:
            zoning_payload = {
                "status": zoning.status,
                "mixtura": zoning.mixtura,
                "rubro_allowed": zoning.rubro_allowed,
                "message": zoning.message,
                "parcel": (
                    {
                        "smp": zoning.parcel.smp,
                        "direccion": zoning.parcel.direccion,
                    }
                    if zoning.parcel
                    else None
                ),
            }

        return {
            "activity_name": activity_name,
            "activity_code": activity_code,
            "normalized_address": normalized_address,
            "commune": commune,
            "neighborhood": neighborhood,
            "requirements": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "status": r.status,
                    "source_ids": list(r.source_ids),
                }
                for r in requirements
            ],
            "steps": [
                {
                    "order": s.order,
                    "title": s.title,
                    "description": s.description,
                    "source_ids": list(s.source_ids),
                }
                for s in steps
            ],
            "documents": [
                {
                    "name": d.name,
                    "details": d.details,
                    "source_ids": list(d.source_ids),
                }
                for d in documents
            ],
            "territorial_information": [
                {
                    "title": t.title,
                    "description": t.description,
                    "source_ids": list(t.source_ids),
                }
                for t in territorial_information
            ],
            "online_procedures": [
                {"id": o.id, "name": o.name, "url": o.url, "source_ids": list(o.source_ids)}
                for o in online_procedures
            ],
            "physical_offices": [
                {
                    "id": o.id,
                    "name": o.name,
                    "address": o.address,
                    "source_ids": list(o.source_ids),
                }
                for o in physical_offices
            ],
            "sources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "organization": s.organization,
                    "url": s.url,
                    "validity_status": s.validity_status,
                }
                for s in sources
            ],
            "zoning": zoning_payload,
            "missing": list(missing),
            "warnings": list(warnings),
        }

    async def _explain_with_llm(self, context: dict[str, Any]) -> dict[str, Any]:
        user_prompt = (
            "Contexto oficial recuperado (unico material permitido):\n"
            f"{json.dumps(context, ensure_ascii=False)}"
        )
        return await self.llm.complete_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    def _validate(
        self,
        *,
        raw: dict[str, Any],
        context: dict[str, Any],
        provider: str,
    ) -> ExplanationResult:
        summary = (raw.get("summary") or "").strip()
        notes_raw = raw.get("missing_information_notes") or []
        notes = [str(n).strip() for n in notes_raw if str(n).strip()]

        has_sources = bool(context.get("sources"))
        has_requirements = bool(context.get("requirements"))

        # Sin fuentes ni requisitos: no aceptar narrativa inventada
        if not has_sources and not has_requirements:
            fallback = mock_explain(context)
            summary = str(fallback["summary"])
            notes = list(fallback.get("missing_information_notes") or [])
            provider = "mock_forced"
        elif not summary:
            fallback = mock_explain(context)
            summary = str(fallback["summary"])
            notes = list(fallback.get("missing_information_notes") or notes)
            if provider == "llm":
                provider = "mock_fallback_empty"

        # Si el LLM inventa tramites tipicos sin requirements, forzar mock
        if not has_requirements and _looks_invented(summary):
            fallback = mock_explain(context)
            summary = str(fallback["summary"])
            notes = list(fallback.get("missing_information_notes") or notes)
            provider = "mock_forced_no_requirements"

        return ExplanationResult(
            summary=summary,
            missing_information_notes=notes,
            provider=provider,
        )


def _looks_invented(summary: str) -> bool:
    """Heuristica liviana: frases tipicas de tramites inventados."""
    lower = summary.lower()
    markers = (
        "debes presentar",
        "deberas presentar",
        "tenes que presentar",
        "habilitacion comercial obligatoria",
        "pago de tasas inventadas",
    )
    return any(m in lower for m in markers)
