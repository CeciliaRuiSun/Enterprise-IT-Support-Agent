from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.workflows.ticket.state import TicketWorkflowState


@dataclass
class QuestionnaireField:
    name: str
    question: str
    required: bool = True


@dataclass
class Questionnaire:
    ticket_type: str
    fields: list[QuestionnaireField]


class TicketWorkflowEngine:
    def __init__(self, questionnaires_dir: Path | None = None) -> None:
        self.questionnaires_dir = questionnaires_dir or Path(__file__).resolve().parent / "questionnaires"

    def load_questionnaire(self, ticket_type: str) -> Questionnaire:
        path = self.questionnaires_dir / f"{ticket_type}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Questionnaire not found for ticket type '{ticket_type}'")
        payload = yaml.safe_load(path.read_text())
        fields = [QuestionnaireField(**field) for field in payload.get("fields", [])]
        return Questionnaire(ticket_type=payload["ticket_type"], fields=fields)

    def create_state(self, ticket_type: str, extracted_fields: dict[str, str] | None = None) -> TicketWorkflowState:
        return TicketWorkflowState(ticket_type=ticket_type, collected_fields=extracted_fields or {})

    def next_question(self, state: TicketWorkflowState) -> str | None:
        questionnaire = self.load_questionnaire(state.ticket_type)
        for field in questionnaire.fields:
            if field.required and not state.collected_fields.get(field.name):
                if field.name not in state.asked_fields:
                    state.asked_fields.append(field.name)
                return field.question
        return None

    def is_complete(self, state: TicketWorkflowState) -> bool:
        questionnaire = self.load_questionnaire(state.ticket_type)
        return all(not field.required or state.collected_fields.get(field.name) for field in questionnaire.fields)

    def build_summary(self, state: TicketWorkflowState) -> str:
        questionnaire = self.load_questionnaire(state.ticket_type)
        lines = [f"Ticket type: {questionnaire.ticket_type}"]
        for field in questionnaire.fields:
            value = state.collected_fields.get(field.name, "Not provided")
            lines.append(f"- {field.name}: {value}")
        summary = "\n".join(lines)
        state.summary = summary
        state.confirmation_pending = True
        return summary

