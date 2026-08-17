import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_every_response_has_a_unique_request_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        first = await client.get("/health")
        second = await client.get("/health")

    assert first.headers["X-Request-ID"]
    assert second.headers["X-Request-ID"]
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]

