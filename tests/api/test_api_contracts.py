import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.auth.dependencies import get_current_user as get_entra_current_user
from app.auth.models import CurrentUser
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


@pytest.mark.asyncio
async def test_me_requires_a_bearer_token(api_client):
    response = await api_client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing bearer token"}
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_me_returns_the_authenticated_entra_user(api_client):
    async def fake_entra_user() -> CurrentUser:
        return CurrentUser(
            entra_object_id="entra-object-id",
            tenant_id="tenant-id",
            email="user@example.com",
            display_name="Test User",
            scopes=["access_as_user"],
        )

    app.dependency_overrides[get_entra_current_user] = fake_entra_user
    response = await api_client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json() == {
        "entra_object_id": "entra-object-id",
        "tenant_id": "tenant-id",
        "email": "user@example.com",
        "display_name": "Test User",
        "scopes": ["access_as_user"],
    }
