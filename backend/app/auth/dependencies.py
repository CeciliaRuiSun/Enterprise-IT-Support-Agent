from functools import lru_cache

from fastapi import Header, HTTPException, status

from app.auth.config import AuthConfigurationError, get_entra_auth_config
from app.auth.models import CurrentUser
from app.auth.token_validator import (
    AuthProviderUnavailableError,
    EntraTokenValidator,
    InsufficientScopeError,
    InvalidTokenError,
)


@lru_cache(maxsize=1)
def get_token_validator() -> EntraTokenValidator:
    return EntraTokenValidator(get_entra_auth_config())


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use the Bearer scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        validator = get_token_validator()
        return await validator.validate(token.strip())
    except InsufficientScopeError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
            headers={
                "WWW-Authenticate": (
                    'Bearer error="insufficient_scope", '
                    f'scope="{validator.config.required_scope}"'
                )
            },
        ) from exc
    except (InvalidTokenError,) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Microsoft Entra access token ({exc.reason})",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except (AuthConfigurationError, AuthProviderUnavailableError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
