from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.intent import classify_intent
from app.models.common import Conversation, MessageRole, WorkflowRun, WorkflowStatus
from app.schemas.agent import AgentTurnResult
from app.schemas.ticket import TicketCreateRequest
from app.services.knowledge_service import KnowledgeService
from app.services.ticket_service import TicketService
from app.workflows.ticket.engine import TicketWorkflowEngine
from app.workflows.ticket.state import TicketWorkflowState


@dataclass
class WorkflowResponse:
    content: str
    citations: list[dict]
    tool_calls: list[dict]


class WorkflowService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.engine = TicketWorkflowEngine()
        self.ticket_service = TicketService(db)
        self.knowledge_service = KnowledgeService(db)

    async def get_active_workflow(self, conversation_id) -> WorkflowRun | None:
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.conversation_id == conversation_id)
            .where(WorkflowRun.status.in_([WorkflowStatus.active, WorkflowStatus.waiting_input, WorkflowStatus.waiting_confirmation]))
            .order_by(WorkflowRun.created_at.desc())
        )
        return (await self.db.scalars(stmt)).first()

    async def _persist_state(self, workflow_run: WorkflowRun, state: TicketWorkflowState, status: WorkflowStatus) -> None:
        workflow_run.state = {
            "ticket_type": state.ticket_type,
            "collected_fields": state.collected_fields,
            "asked_fields": state.asked_fields,
            "confirmation_pending": state.confirmation_pending,
            "summary": state.summary,
        }
        workflow_run.status = status
        await self.db.flush()

    async def start_workflow(
        self, conversation: Conversation, ticket_type: str, extracted_fields: dict[str, str]
    ) -> WorkflowResponse:
        state = self.engine.create_state(ticket_type, extracted_fields)
        workflow_run = WorkflowRun(
            conversation_id=conversation.id,
            workflow_type="ticket",
            status=WorkflowStatus.active,
            state={
                "ticket_type": state.ticket_type,
                "collected_fields": state.collected_fields,
                "asked_fields": state.asked_fields,
                "confirmation_pending": state.confirmation_pending,
                "summary": state.summary,
            },
        )
        self.db.add(workflow_run)

        prompt = self.engine.next_question(state)
        if prompt:
            await self._persist_state(workflow_run, state, WorkflowStatus.waiting_input)
            conversation.active_workflow_type = "ticket"
            conversation.active_workflow_status = WorkflowStatus.waiting_input.value
            return WorkflowResponse(
                content=f"I can help create a {ticket_type.replace('_', ' ')}. {prompt}",
                citations=[],
                tool_calls=[{"tool": "workflow_start", "workflow_type": "ticket", "ticket_type": ticket_type}],
            )

        summary = self.engine.build_summary(state)
        await self._persist_state(workflow_run, state, WorkflowStatus.waiting_confirmation)
        conversation.active_workflow_type = "ticket"
        conversation.active_workflow_status = WorkflowStatus.waiting_confirmation.value
        return WorkflowResponse(
            content=f"Here is the ticket summary:\n{summary}\n\nReply 'confirm' to submit or 'cancel' to stop.",
            citations=[],
            tool_calls=[{"tool": "workflow_start", "workflow_type": "ticket", "ticket_type": ticket_type}],
        )

    async def continue_workflow(self, conversation: Conversation, user_message: str) -> WorkflowResponse:
        workflow = await self.get_active_workflow(conversation.id)
        if not workflow:
            return WorkflowResponse(content="", citations=[], tool_calls=[])

        state_data = workflow.state or {}
        state = TicketWorkflowState(
            ticket_type=state_data.get("ticket_type", "incident_ticket"),
            collected_fields=dict(state_data.get("collected_fields") or {}),
            asked_fields=list(state_data.get("asked_fields") or []),
            confirmation_pending=bool(state_data.get("confirmation_pending", False)),
            summary=state_data.get("summary"),
        )

        lowered = user_message.strip().lower()
        if lowered in {"cancel", "stop", "never mind", "nevermind"}:
            workflow.status = WorkflowStatus.canceled
            conversation.active_workflow_type = None
            conversation.active_workflow_status = None
            await self.db.flush()
            return WorkflowResponse(
                content="I canceled the current workflow. Let me know if you'd like to start a new request.",
                citations=[],
                tool_calls=[{"tool": "workflow_cancel", "workflow_type": workflow.workflow_type}],
            )

        questionnaire = self.engine.load_questionnaire(state.ticket_type)
        missing_fields = [field for field in questionnaire.fields if field.required and not state.collected_fields.get(field.name)]

        if state.confirmation_pending:
            if lowered in {"confirm", "yes", "submit", "send"}:
                payload = TicketCreateRequest(
                    request_type=state.ticket_type,
                    request_for=state.collected_fields.get("requested_for"),
                    business_justification=state.collected_fields.get("business_justification"),
                    description=state.collected_fields.get("issue_summary") or state.summary,
                    priority=state.collected_fields.get("urgency", "medium"),
                )
                ticket = await self.ticket_service.create_ticket(payload, submitted_by=None)
                workflow.status = WorkflowStatus.completed
                conversation.active_workflow_type = None
                conversation.active_workflow_status = None
                await self.db.flush()
                return WorkflowResponse(
                    content=f"Your ticket has been created successfully. Ticket ID: {ticket.id}",
                    citations=[],
                    tool_calls=[{"tool": "create_ticket", "ticket_id": str(ticket.id)}],
                )
            if lowered in {"cancel", "no"}:
                workflow.status = WorkflowStatus.canceled
                conversation.active_workflow_type = None
                conversation.active_workflow_status = None
                await self.db.flush()
                return WorkflowResponse(
                    content="I canceled the ticket submission. If you want, I can revise the details and try again.",
                    citations=[],
                    tool_calls=[{"tool": "workflow_cancel", "workflow_type": workflow.workflow_type}],
                )
            return WorkflowResponse(
                content="Please reply with 'confirm' to submit the ticket or 'cancel' to stop.",
                citations=[],
                tool_calls=[],
            )

        if state.asked_fields:
            current_field = state.asked_fields[-1]
            if user_message.strip():
                state.collected_fields[current_field] = user_message.strip()

        if self.engine.is_complete(state):
            summary = self.engine.build_summary(state)
            await self._persist_state(workflow, state, WorkflowStatus.waiting_confirmation)
            conversation.active_workflow_type = "ticket"
            conversation.active_workflow_status = WorkflowStatus.waiting_confirmation.value
            return WorkflowResponse(
                content=f"Here is the ticket summary:\n{summary}\n\nReply 'confirm' to submit or 'cancel' to stop.",
                citations=[],
                tool_calls=[{"tool": "ticket_summary", "workflow_type": "ticket"}],
            )

        next_question = self.engine.next_question(state)
        await self._persist_state(workflow, state, WorkflowStatus.waiting_input)
        conversation.active_workflow_type = "ticket"
        conversation.active_workflow_status = WorkflowStatus.waiting_input.value
        return WorkflowResponse(
            content=next_question or "Could you share one more detail so I can finish the request?",
            citations=[],
            tool_calls=[{"tool": "collect_workflow_field", "workflow_type": "ticket"}],
        )

    async def respond(self, conversation: Conversation, user_message: str) -> AgentTurnResult:
        active = await self.get_active_workflow(conversation.id)
        intent = classify_intent(user_message)

        if active:
            active_state = active.state or {}
            active_ticket_type = active_state.get("ticket_type")
            if intent.intent == "create_ticket" and intent.ticket_type and intent.ticket_type != active_ticket_type:
                return AgentTurnResult(
                    content=(
                        "You already have an active ticket workflow. "
                        "Would you like me to cancel it first so I can start the new request?"
                    ),
                    citations=[],
                    tool_calls=[{"tool": "workflow_conflict", "active_workflow": active.workflow_type}],
                    active_workflow_type=conversation.active_workflow_type,
                    active_workflow_status=conversation.active_workflow_status,
                )

            response = await self.continue_workflow(conversation, user_message)
            return AgentTurnResult(
                content=response.content,
                citations=response.citations,
                tool_calls=response.tool_calls,
                active_workflow_type=conversation.active_workflow_type,
                active_workflow_status=conversation.active_workflow_status,
            )

        if intent.intent == "create_ticket":
            response = await self.start_workflow(conversation, intent.ticket_type or "incident_ticket", intent.extracted_fields)
            return AgentTurnResult(
                content=response.content,
                citations=response.citations,
                tool_calls=response.tool_calls,
                active_workflow_type=conversation.active_workflow_type,
                active_workflow_status=conversation.active_workflow_status,
            )

        if intent.intent == "search_knowledge":
            knowledge_result = await self.knowledge_service.search(intent.extracted_fields.get("query", user_message))
            if not knowledge_result.chunks:
                return AgentTurnResult(
                    content="I couldn't find a matching document yet. Try rephrasing the issue or ask for a ticket.",
                    citations=[],
                    tool_calls=[{"tool": "search_knowledge", "query": user_message, "result_count": 0}],
                )
            citations = []
            lines = ["I found the following relevant references:"]
            for idx, chunk in enumerate(knowledge_result.chunks, start=1):
                source_name = chunk.title
                citation = {
                    "source": source_name,
                    "chunk_id": str(chunk.chunk_id),
                    "page_number": chunk.page_number,
                    "score": chunk.score,
                }
                citations.append(citation)
                lines.append(f"{idx}. {source_name}: {chunk.content[:240].strip()}")
            lines.append("\nIf you want, I can turn this into a ticket request next.")
            return AgentTurnResult(
                content="\n".join(lines),
                citations=citations,
                tool_calls=[{"tool": "search_knowledge", "query": user_message, "result_count": len(citations)}],
            )

        return AgentTurnResult(
            content=(
                "I can help with knowledge-base questions, ticket requests, and guided troubleshooting. "
                "If you'd like, ask me about VPN, printers, software access, or submit a support request."
            ),
            citations=[],
            tool_calls=[],
        )
