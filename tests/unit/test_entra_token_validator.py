from types import SimpleNamespace
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth.config import EntraAuthConfig
from app.auth.token_validator import (
    EntraTokenValidator,
    InsufficientScopeError,
    InvalidTokenError,
)


@pytest.fixture
def entra_config() -> EntraAuthConfig:
    return EntraAuthConfig(
        tenant_id="tenant-id",
        api_client_id="api-client-id",
        required_scope="access_as_user",
    )


@pytest.fixture
def signing_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def make_token(private_key, **overrides) -> str:
    claims = {
        "iss": "https://login.microsoftonline.com/tenant-id/v2.0",
        "aud": "api-client-id",
        "tid": "tenant-id",
        "oid": "entra-object-id",
        "preferred_username": "user@example.com",
        "name": "Test User",
        "scp": "access_as_user User.Read",
        "exp": int(time.time()) + 300,
        "nbf": int(time.time()) - 10,
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")


async def make_validator(monkeypatch, entra_config, public_key) -> EntraTokenValidator:
    validator = EntraTokenValidator(entra_config)

    async def fake_signing_key(_token: str, _metadata):
        return SimpleNamespace(key=public_key)

    monkeypatch.setattr(validator, "_get_signing_key", fake_signing_key)

    async def fake_metadata(_metadata_url: str, expected_issuer: str):
        return {"issuer": expected_issuer, "jwks_uri": "https://example.test/keys"}

    monkeypatch.setattr(validator, "_get_metadata", fake_metadata)
    return validator


@pytest.mark.asyncio
async def test_validate_builds_current_user_from_validated_claims(
    monkeypatch, entra_config, signing_keys
):
    private_key, public_key = signing_keys
    validator = await make_validator(monkeypatch, entra_config, public_key)

    user = await validator.validate(make_token(private_key))

    assert user.entra_object_id == "entra-object-id"
    assert user.tenant_id == "tenant-id"
    assert user.email == "user@example.com"
    assert user.display_name == "Test User"
    assert user.scopes == ["access_as_user", "User.Read"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("iss", "https://login.microsoftonline.com/another-tenant/v2.0"),
        ("aud", "another-api-client-id"),
        ("tid", "another-tenant"),
        ("exp", int(time.time()) - 1),
        ("nbf", int(time.time()) + 300),
    ],
)
async def test_validate_rejects_invalid_security_claims(
    monkeypatch, entra_config, signing_keys, claim, value
):
    private_key, public_key = signing_keys
    validator = await make_validator(monkeypatch, entra_config, public_key)

    with pytest.raises(InvalidTokenError):
        await validator.validate(make_token(private_key, **{claim: value}))


@pytest.mark.asyncio
async def test_validate_rejects_a_token_without_required_scope(
    monkeypatch, entra_config, signing_keys
):
    private_key, public_key = signing_keys
    validator = await make_validator(monkeypatch, entra_config, public_key)

    with pytest.raises(InsufficientScopeError):
        await validator.validate(make_token(private_key, scp="User.Read"))


@pytest.mark.asyncio
async def test_validate_rejects_a_token_with_an_invalid_signature(
    monkeypatch, entra_config, signing_keys
):
    private_key, public_key = signing_keys
    other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    validator = await make_validator(monkeypatch, entra_config, public_key)

    with pytest.raises(InvalidTokenError) as error:
        await validator.validate(make_token(other_private_key))

    assert error.value.reason == "signature"


@pytest.mark.asyncio
async def test_validate_accepts_a_v1_token_with_the_tenant_v1_issuer(
    monkeypatch, entra_config, signing_keys
):
    private_key, public_key = signing_keys
    validator = await make_validator(monkeypatch, entra_config, public_key)

    user = await validator.validate(
        make_token(
            private_key,
            ver="1.0",
            iss="https://sts.windows.net/tenant-id/",
            aud="api://api-client-id",
        )
    )

    assert user.entra_object_id == "entra-object-id"


@pytest.mark.asyncio
async def test_validate_rejects_an_unrelated_api_identifier_uri(
    monkeypatch, entra_config, signing_keys
):
    private_key, public_key = signing_keys
    validator = await make_validator(monkeypatch, entra_config, public_key)

    with pytest.raises(InvalidTokenError):
        await validator.validate(make_token(private_key, aud="api://another-api-client-id"))
