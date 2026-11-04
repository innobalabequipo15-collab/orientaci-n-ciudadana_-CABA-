"""Respuestas de seguimiento solo desde el snapshot recuperado (sin LLM)."""

from __future__ import annotations

from typing import Any


def mock_follow_up(*, question: str, snapshot: dict[str, Any]) -> str:
    q = question.lower()
    summary = snapshot.get("summary") or ""
    reqs = snapshot.get("requirements") or []
    steps = snapshot.get("steps") or []
    docs = snapshot.get("documents") or []
    sources = snapshot.get("sources") or []
    offices = (snapshot.get("physical_offices") or []) + (
        snapshot.get("online_procedures") or []
    )

    if any(w in q for w in ("document", "documento", "papeles", "papel")):
        if docs:
            names = ", ".join(d.get("name", "?") for d in docs[:6])
            return (
                f"Según las fuentes de esta consulta, la documentación referida incluye: {names}. "
                "Validá detalle y vigencia en las URLs citadas en la orientación original."
            )
        if reqs and reqs[0].get("documents"):
            inner = reqs[0]["documents"]
            names = ", ".join(d.get("name", "?") for d in inner[:6])
            return f"En los requisitos recuperados figura: {names}."
        return (
            "No hay documentación adicional recuperada en este caso. "
            "Revisá las fuentes oficiales listadas en la consulta inicial."
        )

    if any(w in q for w in ("paso", "pasos", "tramite", "trámite", "como hago", "cómo hago")):
        if steps:
            lines = [f"{s.get('order', '?')}. {s.get('title', 'Paso')}" for s in steps[:8]]
            return "Pasos documentados en las fuentes:\n" + "\n".join(lines)
        return "No hay pasos adicionales en el contexto guardado; usá el resumen de la consulta inicial."

    if any(w in q for w in ("oficina", "donde", "dónde", "atencion", "atención", "presencial")):
        if offices:
            lines = [
                f"• {o.get('name', '?')} — {o.get('address') or o.get('url') or 'sin dirección'}"
                for o in offices[:5]
            ]
            return "Canales de atención recuperados:\n" + "\n".join(lines)
        return "No hay oficinas o canales publicados en el contexto de esta consulta."

    if any(w in q for w in ("requisito", "necesito", "habilit")):
        if reqs:
            titles = ", ".join(r.get("title", "?") for r in reqs[:5])
            return f"Requisitos oficiales recuperados: {titles}."
        return "No hay requisitos adicionales en el contexto; no se inventan trámites."

    if sources:
        src = ", ".join(s.get("name", s.get("id", "?")) for s in sources[:4])
        intro = summary[:400] + ("…" if len(summary) > 400 else "") if summary else ""
        return (
            f"{intro}\n\nFuentes de esta consulta: {src}. "
            "Si tu pregunta es más específica, mencioná documentos, pasos u oficinas."
        ).strip()

    return (
        summary
        or "Solo puedo responder con el contexto de la consulta original. "
        "Reformulá preguntando por documentos, pasos u oficinas."
    )
