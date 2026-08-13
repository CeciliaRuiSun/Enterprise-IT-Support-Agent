from dataclasses import dataclass

from app.core.config import get_settings


class AuthConfigurationError(RuntimeError):
    """Raised when the API is missing required Entra configuration."""


@dataclass(frozen=True)
class EntraAuthConfig:
    tenant_id: str
    api_client_id: str
    required_scope: str

    @property
    def metadata_url(self) -> str:
        return (
            f"https://login.microsoftonline.com/{self.tenant_id}"
            "/v2.0/.well-known/openid-configuration"
        )

    @property
    def v1_metadata_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/.well-known/openid-configuration"

    @property
    def issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"

    @property
    def v1_issuer(self) -> str:
        return f"https://sts.windows.net/{self.tenant_id}/"

    @property
    def accepted_audiences(self) -> tuple[str, str]:
        """The bare app ID and its standard Entra API identifier URI."""

        return self.api_client_id, f"api://{self.api_client_id}"


def get_entra_auth_config() -> EntraAuthConfig:
    settings = get_settings()
    missing = [
        name
        for name, value in (
            ("ENTRA_TENANT_ID", settings.entra_tenant_id),
            ("ENTRA_API_CLIENT_ID", settings.entra_api_client_id),
            ("ENTRA_REQUIRED_SCOPE", settings.entra_required_scope),
        )
        if not value or not value.strip()
    ]
    if missing:
        raise AuthConfigurationError(
            "Missing Entra authentication configuration: " + ", ".join(missing)
        )

    return EntraAuthConfig(
        tenant_id=settings.entra_tenant_id.strip(),
        api_client_id=settings.entra_api_client_id.strip(),
        required_scope=settings.entra_required_scope.strip(),
    )
