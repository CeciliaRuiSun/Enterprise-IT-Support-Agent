from pydantic import BaseModel, ConfigDict


class CurrentUser(BaseModel):
    """Stable identity information derived from a validated Entra token."""

    model_config = ConfigDict(frozen=True)

    entra_object_id: str
    tenant_id: str
    email: str | None = None
    display_name: str | None = None
    scopes: list[str]
