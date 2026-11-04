"""Explicacion ciudadana deterministica a partir del contexto recuperado (sin LLM)."""

from __future__ import annotations

from typing import Any


def mock_explain(context: dict[str, Any]) -> dict[str, str | list[str]]:
    """Arma summary solo con hechos del contexto. No inventa requisitos."""
    activity = context.get("activity_name") or "la actividad consultada"
    address = context.get("normalized_address") or "la ubicacion consultada"
    neighborhood = context.get("neighborhood")
    commune = context.get("commune")
    place = address
    if neighborhood or commune:
        place = f"{address} ({neighborhood or 'barrio N/D'}, {commune or 'comuna N/D'})"

    reqs = context.get("requirements") or []
    steps = context.get("steps") or []
    docs = context.get("documents") or []
    offices_phys = context.get("physical_offices") or []
    offices_online = context.get("online_procedures") or []
    territorial = context.get("territorial_information") or []
    sources = context.get("sources") or []
    zoning = context.get("zoning") or {}
    missing = context.get("missing") or []
    warnings = context.get("warnings") or []

    parts: list[str] = [
        f"Orientacion ciudadana para {activity} en {place}."
    ]

    parcel = zoning.get("parcel") or {}
    if parcel.get("smp"):
        mixtura = zoning.get("mixtura") or "N/D"
        allowed = zoning.get("rubro_allowed")
        if allowed is True:
            rubro_txt = "parece compatible con la mixtura"
        elif allowed is False:
            rubro_txt = "puede no estar permitido en esa mixtura"
        else:
            rubro_txt = "sin verificacion de rubro"
        parts.append(
            f"Segun Ciudad 3D/epok, la parcela SMP {parcel['smp']} "
            f"(mixtura {mixtura}) {rubro_txt}."
        )

    if reqs:
        titles = ", ".join(r.get("title", "requisito") for r in reqs[:3])
        parts.append(
            f"Se recuperaron {len(reqs)} requisito(s) oficiales: {titles}"
            + ("…" if len(reqs) > 3 else ".")
        )
    else:
        parts.append(
            "No hay requisitos oficiales recuperados para este rubro en el catalogo "
            "curado; no se inventan tramites."
        )

    if steps:
        parts.append(f"Hay {len(steps)} paso(s) documentados en las fuentes citadas.")
    if docs:
        parts.append(f"Documentacion referida: {len(docs)} item(s).")

    n_off = len(offices_phys) + len(offices_online)
    if n_off:
        parts.append(
            f"Canales de atencion: {len(offices_phys)} presencial(es) y "
            f"{len(offices_online)} online."
        )
    else:
        parts.append("No hay oficinas o canales publicados vinculados a esta consulta.")

    if territorial:
        parts.append(
            f"Contexto territorial: {territorial[0].get('title', 'disponible')}."
        )

    if sources:
        src_names = ", ".join(s.get("name", s.get("id", "?")) for s in sources[:4])
        parts.append(f"Fuentes: {src_names}" + ("…" if len(sources) > 4 else "."))
    else:
        parts.append("Sin fuentes vinculadas: la orientacion es limitada.")

    notes: list[str] = []
    for m in missing:
        notes.append(f"Falta informacion: {m}.")
    for w in warnings:
        notes.append(f"Advertencia: {w}.")
    if notes:
        parts.append(" ".join(notes))

    parts.append("Validar siempre contra las URLs y organismos citados.")
    return {"summary": " ".join(parts), "missing_information_notes": notes}
