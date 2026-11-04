import httpx
import pytest

from app.providers.geocoder import UsigGeocoder, _clean_address


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Ramallo al 2194 en Núñez", "Ramallo 2194"),
        ("Ramallo 2194, Núñez, CABA", "Ramallo 2194"),
        ("Ramallo 2194 (Núñez)", "Ramallo 2194"),
        ("Ramallo 2194 - Núñez", "Ramallo 2194"),
        ("Av. Corrientes al 2500, Palermo", "Av. Corrientes 2500"),
        ("9 de Julio al 1234 en Núñez", "9 de Julio 1234"),
        ("Avenida 9 de Julio 1234", "Avenida 9 de Julio 1234"),
        ("Ramallo 2194 CABA", "Ramallo 2194"),
        ("  Ramallo   2194  ", "Ramallo 2194"),
    ],
)
def test_clean_address(raw: str, expected: str) -> None:
    assert _clean_address(raw) == expected


CABA_HIT = {
    "altura": 2194,
    "cod_partido": "caba",
    "coordenadas": {"srid": 4326, "x": "-58.470345", "y": "-34.541914"},
    "direccion": "RAMALLO 2194, CABA",
    "nombre_calle": "RAMALLO",
    "nombre_localidad": "CABA",
    "nombre_partido": "CABA",
    "nombre_comuna": "Comuna 13",
    "nombre_barrio": "Núñez",
    "tipo": "calle_altura",
}


def _usig_response(request: httpx.Request) -> httpx.Response:
    direccion = request.url.params.get("direccion")
    if direccion == "Ramallo 2194":
        return httpx.Response(200, json={"direccionesNormalizadas": [CABA_HIT]})
    return httpx.Response(
        200,
        json={
            "direccionesNormalizadas": [],
            "errorMessage": f"Calle inexistente: {direccion}",
        },
    )


@pytest.mark.asyncio
async def test_usig_geocoder_cleans_free_text_address() -> None:
    calls: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.params.get("direccion"))
        return _usig_response(request)

    geocoder = UsigGeocoder(
        base_url="https://servicios.usig.buenosaires.gob.ar",
        ws_base_url="https://ws.usig.buenosaires.gob.ar",
        transport=httpx.MockTransport(handler),
    )

    result = await geocoder.geocode("Ramallo al 2194 en Núñez")

    assert result.status == "confirmed"
    assert calls == ["Ramallo 2194"]
    assert result.hits[0].neighborhood == "Núñez"
    assert result.hits[0].commune == "Comuna 13"
    assert result.hits[0].latitude == pytest.approx(-34.541914)
    assert result.hits[0].longitude == pytest.approx(-58.470345)


@pytest.mark.asyncio
async def test_usig_geocoder_returns_not_found_when_no_matches() -> None:
    geocoder = UsigGeocoder(
        base_url="https://servicios.usig.buenosaires.gob.ar",
        ws_base_url="https://ws.usig.buenosaires.gob.ar",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"direccionesNormalizadas": []})
        ),
    )

    result = await geocoder.geocode("Calle Inexistente 9999")

    assert result.status == "not_found"
    assert result.hits == []
