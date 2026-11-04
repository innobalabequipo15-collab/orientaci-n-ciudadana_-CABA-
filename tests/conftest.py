import os

import pytest
from httpx import ASGITransport, AsyncClient

# Tests: mock geocoder, sin rate limit
os.environ.setdefault("GEOCODER_PROVIDER", "mock")
os.environ.setdefault("EPOK_PROVIDER", "mock")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("APP_ENV", "test")

from app.core.config import clear_settings_cache

clear_settings_cache()

from app.main import app  # noqa: E402


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
