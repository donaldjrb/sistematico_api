# tests/test_health.py
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

transport = ASGITransport(app=app)  # 👈  sin lifespan


@pytest.mark.asyncio
async def test_docs_available():
    async with AsyncClient(
        transport=transport,
        base_url="http://test",  # 👈  usa transport
    ) as ac:
        resp = await ac.get("/docs")
    assert resp.status_code == 200
