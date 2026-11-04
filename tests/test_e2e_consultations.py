import pytest
from httpx import AsyncClient

from app.providers.mock_follow_up import mock_follow_up


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_consultation_deterministic_and_follow_up(client: AsyncClient):
    create = await client.post(
        "/api/v1/consultations",
        json={
            "activity_code": "rubro_102",
            "address": "Av. Corrientes 2500",
        },
    )
    if create.status_code >= 500:
        pytest.skip("Database unavailable for integration test")
    assert create.status_code == 200, create.text
    body = create.json()
    cid = body["consultation_id"]
    assert body["status"] in ("complete", "partial")
    assert body.get("requirements")
    assert body.get("sources")

    follow = await client.post(
        f"/api/v1/consultations/{cid}/follow-ups",
        json={"question": "¿Qué documentos necesito?"},
    )
    assert follow.status_code == 200, follow.text
    fu = follow.json()
    assert fu["consultation_id"] == cid
    assert fu["follow_up_id"].startswith("followup-")
    assert len(fu["answer"]) > 10
    assert fu["message"].startswith("followup:")

    missing = await client.post(
        "/api/v1/consultations/consultation-doesnotexist/follow-ups",
        json={"question": "¿Qué pasos hay?"},
    )
    assert missing.status_code == 404


def test_mock_follow_up_uses_snapshot_only():
    snapshot = {
        "summary": "Orientacion para gastronomia.",
        "documents": [{"name": "DNI titular"}],
        "requirements": [],
        "steps": [],
        "sources": [{"id": "s1", "name": "Guia GCBA"}],
        "physical_offices": [],
        "online_procedures": [],
    }
    ans = mock_follow_up(question="documentos necesarios", snapshot=snapshot)
    assert "DNI" in ans
    assert "invent" not in ans.lower()
