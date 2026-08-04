from pydantic import BaseModel, Field


class IntentExtraction(BaseModel):
    intent: str = Field(default="general_support")
    ticket_type: str | None = None
    confidence: float = 0.0
    extracted_fields: dict = Field(default_factory=dict)


class AgentTurnResult(BaseModel):
    content: str
    citations: list[dict] = Field(default_factory=list)
    tool_calls: list[dict] = Field(default_factory=list)
    active_workflow_type: str | None = None
    active_workflow_status: str | None = None

