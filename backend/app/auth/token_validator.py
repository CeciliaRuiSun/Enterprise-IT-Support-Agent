import asyncio
import logging
import time
from typing import Any

import httpx
import jwt
from jwt.exceptions import ExpiredSignatureError
from jwt.exceptions import ImmatureSignatureError
from jwt.exceptions import InvalidAudienceError
from jwt.exceptions import InvalidIssuerError
from jwt.exceptions import InvalidSignatureError
from jwt.exceptions import InvalidTokenError as JWTInvalidTokenError
from jwt.exceptions import MissingRequiredClaimError

from app.auth.config import EntraAuthConfig
from app.auth.models import CurrentUser


logger = logging.getLogger(__name__)


class InvalidTokenError(ValueError):
    """Raised when an access token fails validation."""

    def __init__(self, message: str, *, reason: str = "invalid") -> None:
        super().__init__(message)
        self.reason = reason


class InsufficientScopeError(ValueError):
    """Raised when a valid token lacks the required delegated scope."""


class AuthProviderUnavailableError(RuntimeError):
    """Raised when Entra metadata or signing keys cannot be reached."""


class EntraTokenValidator:
    """Validate Entra access tokens using the tenant's published OIDC keys."""

    _metadata_ttl_seconds = 3600

    def __init__(self, config: EntraAuthConfig) -> None:
        self.config = config
        self._metadata: dict[str, tuple[dict[str, Any], float]] = {}
        self._jwks: dict[str, Any] | None = None
        self._jwks_expires_at = 0.0
        self._metadata_lock = asyncio.Lock()
        self._jwks_lock = asyncio.Lock()

    async def _get_metadata(self, metadata_url: str, expected_issuer: str) -> dict[str, Any]:
        now = time.monotonic()
        cached = self._metadata.get(metadata_url)
        if cached is not None and now < cached[1]:
            return cached[0]

        async with self._metadata_lock:
            now = time.monotonic()
            cached = self._metadata.get(metadata_url)
            if cached is not None and now < cached[1]:
                return cached[0]

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(metadata_url)
                    response.raise_for_status()
                    metadata = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise AuthProviderUnavailableError(
                    "Unable to load Microsoft Entra OpenID Connect metadata"
                ) from exc

            if not isinstance(metadata, dict):
                raise AuthProviderUnavailableError(
                    "Microsoft Entra metadata has an invalid format"
                )

            issuer = metadata.get("issuer")
            jwks_uri = metadata.get("jwks_uri")
            if issuer != expected_issuer or not isinstance(jwks_uri, str) or not jwks_uri.strip():
                raise AuthProviderUnavailableError(
                    "Microsoft Entra metadata does not match the configured tenant"
                )

            self._metadata[metadata_url] = (
                metadata,
                time.monotonic() + self._metadata_ttl_seconds,
            )
            return metadata

    async def _load_jwks(
        self, metadata: dict[str, Any], *, force_refresh: bool = False
    ) -> dict[str, Any]:
        now = time.monotonic()
        if not force_refresh and self._jwks is not None and now < self._jwks_expires_at:
            return self._jwks

        async with self._jwks_lock:
            now = time.monotonic()
            if not force_refresh and self._jwks is not None and now < self._jwks_expires_at:
                return self._jwks

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(metadata["jwks_uri"])
                    response.raise_for_status()
                    jwks = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise AuthProviderUnavailableError(
                    "Unable to load Microsoft Entra signing keys"
                ) from exc

            if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
                raise AuthProviderUnavailableError(
                    "Microsoft Entra signing-key response has an invalid format"
                )

            self._jwks = jwks
            self._jwks_expires_at = time.monotonic() + self._metadata_ttl_seconds
            return jwks

    async def _get_signing_key(self, token: str, metadata: dict[str, Any]) -> Any:
        try:
            token_header = jwt.get_unverified_header(token)
            key_id = token_header.get("kid")
            if not isinstance(key_id, str) or not key_id:
                raise InvalidTokenError("Access token does not include a key id")

            jwks = await self._load_jwks(metadata)
            matching_key = next(
                (key for key in jwks["keys"] if isinstance(key, dict) and key.get("kid") == key_id),
                None,
            )
            if matching_key is None:
                # Microsoft can rotate signing keys between cache refreshes.
                jwks = await self._load_jwks(metadata, force_refresh=True)
                matching_key = next(
                    (key for key in jwks["keys"] if isinstance(key, dict) and key.get("kid") == key_id),
                    None,
                )
            if matching_key is None:
                raise InvalidTokenError("No Microsoft Entra signing key matches the token")

            return jwt.PyJWK.from_dict(matching_key)
        except InvalidTokenError:
            raise
        except (JWTInvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise InvalidTokenError("Microsoft Entra signing key is invalid") from exc

    async def validate(self, token: str) -> CurrentUser:
        if not token:
            raise InvalidTokenError("Access token is empty")

        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256":
                raise InvalidTokenError("Unsupported access token signing algorithm")

            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            token_version = unverified_claims.get("ver")
            if token_version == "1.0":
                metadata_url = self.config.v1_metadata_url
                expected_issuer = self.config.v1_issuer
            else:
                metadata_url = self.config.metadata_url
                expected_issuer = self.config.issuer

            metadata = await self._get_metadata(metadata_url, expected_issuer)
            signing_key = await self._get_signing_key(token, metadata)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.config.accepted_audiences,
                issuer=metadata["issuer"],
                options={
                    "require": ["exp", "iss", "aud", "tid", "scp"],
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                },
            )
        except InvalidTokenError:
            raise
        except ExpiredSignatureError as exc:
            logger.warning("Microsoft Entra token validation rejected expired token")
            raise InvalidTokenError("Access token is expired", reason="expired") from exc
        except ImmatureSignatureError as exc:
            logger.warning("Microsoft Entra token validation rejected not-yet-valid token")
            raise InvalidTokenError("Access token is not yet valid", reason="not_before") from exc
        except InvalidAudienceError as exc:
            logger.warning(
                "Microsoft Entra token validation rejected audience claim: expected=%s received=%r",
                self.config.api_client_id,
                unverified_claims.get("aud"),
            )
            raise InvalidTokenError("Access token audience is invalid", reason="audience") from exc
        except InvalidIssuerError as exc:
            logger.warning("Microsoft Entra token validation rejected issuer claim")
            raise InvalidTokenError("Access token issuer is invalid", reason="issuer") from exc
        except InvalidSignatureError as exc:
            logger.warning("Microsoft Entra token validation rejected signature")
            raise InvalidTokenError("Access token signature is invalid", reason="signature") from exc
        except MissingRequiredClaimError as exc:
            logger.warning("Microsoft Entra token validation rejected missing claim: %s", exc)
            raise InvalidTokenError("Access token is missing a required claim", reason="claim") from exc
        except (JWTInvalidTokenError, KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "Microsoft Entra token validation rejected token: %s: %s",
                type(exc).__name__,
                str(exc),
            )
            raise InvalidTokenError("Invalid Microsoft Entra access token", reason="invalid") from exc

        if claims.get("tid") != self.config.tenant_id:
            raise InvalidTokenError("Access token belongs to a different tenant")

        scope_claim = claims.get("scp")
        if not isinstance(scope_claim, str):
            raise InvalidTokenError("Access token scope claim is invalid")
        scopes = scope_claim.split()
        if self.config.required_scope not in scopes:
            raise InsufficientScopeError("Access token does not include the required scope")

        object_id = claims.get("oid")
        if not isinstance(object_id, str) or not object_id:
            raise InvalidTokenError("Access token does not include an object id")

        email = claims.get("preferred_username") or claims.get("email") or claims.get("upn")
        display_name = claims.get("name")
        if email is not None and not isinstance(email, str):
            email = None
        if display_name is not None and not isinstance(display_name, str):
            display_name = None

        return CurrentUser(
            entra_object_id=object_id,
            tenant_id=claims["tid"],
            email=email,
            display_name=display_name,
            scopes=scopes,
        )
