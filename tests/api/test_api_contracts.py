import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.common import User


async def fake_db():
    yield None


async def fake_user():
    return User(email="test@example.com", full_name="Test User", role="employee")


@pytest.fixture
async def api_client():
    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_user] = fake_user
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint(api_client):
    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_conversation_create_validates_message_content(api_client):
    response = await api_client.post("/api/v1/conversations", json={})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "message_content"]


@pytest.mark.asyncio
async def test_local_frontend_origin_is_allowed(api_client):
    response = await api_client.options(
        "/api/v1/conversations",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
