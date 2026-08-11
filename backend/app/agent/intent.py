from __future__ import annotations

import re

from app.services.llm import LLMService
from app.schemas.agent import IntentExtraction


TICKET_KEYWORDS = {
    "software_request": ["install", "software", "license", "app", "application"],
    "hardware_request": ["laptop", "monitor", "keyboard", "mouse", "headset", "dock", "hardware"],
    "incident_ticket": ["broken", "not working", "issue", "incident", "down", "cannot", "can't", "error"],
}
TICKET_ID_PATTERN = re.compile(
    r"\b(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}|(?:INC|REQ)-\d{6})\b",
    re.IGNORECASE,
)


def _extract_fields(message: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    lowered = message.lower()

    if match := re.search(r"(?:need|want|request)\s+(.+?)(?:\.|,|$)", lowered):
        fields["request_summary"] = match.group(1).strip()

    if "software" in lowered:
        fields["software_name"] = message.strip()
    if any(word in lowered for word in ("laptop", "monitor", "keyboard", "mouse", "dock")):
        fields["requested_item"] = message.strip()
    if any(word in lowered for word in ("broken", "down", "error", "incident", "cannot", "can't")):
        fields["issue_summary"] = message.strip()

    return fields


def classify_intent(message: str) -> IntentExtraction:
    lowered = message.lower()
    ticket_id_match = TICKET_ID_PATTERN.search(message)
    if ticket_id_match and any(
        phrase in lowered
        for phrase in ("ticket status", "check my ticket", "check ticket", "track my ticket", "track ticket")
    ):
        return IntentExtraction(
            intent="ticket_status",
            ticket_id=ticket_id_match.group(0),
            confidence=0.99,
            extracted_fields={"ticket_id": ticket_id_match.group(0)},
        )

    llm_service = LLMService()
    if llm_service.client:
        prompt = f"""
You are an IT support triage classifier.
Return strict JSON with keys: intent, ticket_type, confidence, extracted_fields.
Allowed intent values: create_ticket, ticket_status, search_knowledge, general_support.
Allowed ticket_type values: software_request, hardware_request, incident_ticket, or null.
User message: {message}
"""
        llm_result = llm_service.responses_json(prompt)
        if llm_result.payload:
            payload = llm_result.payload
            return IntentExtraction(
                intent=payload.get("intent", "general_support"),
                ticket_type=payload.get("ticket_type"),
                confidence=float(payload.get("confidence", 0.0) or 0.0),
                extracted_fields=dict(payload.get("extracted_fields") or {}),
            )

    ticket_type = None
    best_score = 0.0

    for candidate, keywords in TICKET_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_score = score
            ticket_type = candidate

    knowledge_question_starters = (
        "how do i",
        "how to",
        "where can i",
        "what is",
        "which steps",
        "steps to",
        "instructions for",
        "guide for",
    )
    if any(lowered.startswith(starter) for starter in knowledge_question_starters):
        return IntentExtraction(
            intent="search_knowledge",
            confidence=0.78,
            extracted_fields={"query": message.strip()},
        )

    ticket_trigger_words = ("ticket", "request", "submit", "create a ticket", "raise a ticket")
    wants_ticket = any(word in lowered for word in ticket_trigger_words) or best_score > 0

    if wants_ticket:
        return IntentExtraction(
            intent="create_ticket",
            ticket_type=ticket_type or "incident_ticket",
            confidence=min(0.95, 0.45 + 0.12 * best_score),
            extracted_fields=_extract_fields(message),
        )

    if any(word in lowered for word in ("vpn", "password", "printer", "wifi", "network", "kb", "knowledge")):
        return IntentExtraction(
            intent="search_knowledge",
            confidence=0.81,
            extracted_fields={"query": message.strip()},
        )

    return IntentExtraction(intent="general_support", confidence=0.5, extracted_fields={})
