"""Sanitiza URLs en respuestas de consulta."""

from __future__ import annotations

from app.core.url_sanitize import sanitize_http_url
from app.schemas.consultation import ConsultationResponse


def sanitize_consultation_response(response: ConsultationResponse) -> ConsultationResponse:
    data = response.model_dump()
    for src in data.get("sources") or []:
        if isinstance(src, dict):
            src["url"] = sanitize_http_url(src.get("url"))
    for key in ("physical_offices", "online_procedures"):
        for office in data.get(key) or []:
            if isinstance(office, dict):
                office["url"] = sanitize_http_url(office.get("url"))
    for key in ("documents",):
        for doc in data.get(key) or []:
            if isinstance(doc, dict):
                doc["url_fuente"] = sanitize_http_url(doc.get("url_fuente"))
    for req in data.get("requirements") or []:
        if not isinstance(req, dict):
            continue
        for doc in req.get("documents") or []:
            if isinstance(doc, dict):
                doc["url_fuente"] = sanitize_http_url(doc.get("url_fuente"))
        for step in req.get("steps") or []:
            if isinstance(step, dict):
                step["url_fuente"] = sanitize_http_url(step.get("url_fuente"))
    for step in data.get("steps") or []:
        if isinstance(step, dict):
            step["url_fuente"] = sanitize_http_url(step.get("url_fuente"))
    for layer in data.get("map_layers") or []:
        if isinstance(layer, dict):
            layer["url"] = sanitize_http_url(layer.get("url"))
    return ConsultationResponse.model_validate(data)
