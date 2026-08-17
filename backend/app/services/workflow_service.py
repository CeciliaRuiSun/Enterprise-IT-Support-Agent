from __future__ import annotations

from dataclasses import dataclass
import re
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.intent import classify_intent
from app.models.common import Conversation, User, WorkflowRun, WorkflowStatus
from app.schemas.agent import AgentTurnResult
from app.schemas.ticket import TicketCreateRequest
from app.services.knowledge_service import KnowledgeService
from app.services.llm import LLMService
from app.services.ticket_service import TicketService
from app.services.audit_logger import AuditLogger
from app.workflows.ticket.engine import TicketWorkflowEngine
from app.workflows.ticket.state import TicketWorkflowState


@dataclass
class WorkflowResponse:
    content: str
    citations: list[dict]
    tool_calls: list[dict]


class WorkflowService:
    def __init__(self, db: AsyncSession, actor: User | None = None) -> None:
        self.db = db
        self.actor = actor
        self.audit_logger = AuditLogger(db)
        self.engine = TicketWorkflowEngine()
        self.ticket_service = TicketService(db)
        self.knowledge_service = KnowledgeService(db)

    async def _run_tool(self, tool_name: str, conversation_id, operation):
        started = perf_counter()
        try:
            result = await operation()
        except Exception as exc:
            self.audit_logger.log_tool_call(
                tool_name=tool_name,
                status="failure",
                latency_ms=round((perf_counter() - started) * 1000),
                conversation_id=conversation_id,
                error_type=type(exc).__name__,
                actor=self.actor,
            )
            raise
        self.audit_logger.log_tool_call(
            tool_name=tool_name,
            status="success",
            latency_ms=round((perf_counter() - started) * 1000),
            conversation_id=conversation_id,
            resource_id=getattr(result, "ticket_number", None),
            actor=self.actor,
            result_count=len(result.chunks) if hasattr(result, "chunks") else None,
            found=(result is not None) if tool_name == "get_ticket_status" else None,
        )
        return result

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
                ticket = await self._run_tool(
                    "create_ticket", conversation.id,
                    lambda: self.ticket_service.create_ticket(payload, submitted_by=None),
                )
                workflow.status = WorkflowStatus.completed
                conversation.active_workflow_type = None
                conversation.active_workflow_status = None
                await self.db.flush()
                return WorkflowResponse(
                    content=f"Your ticket has been created successfully. Ticket ID: {ticket.ticket_number}",
                    citations=[],
                    tool_calls=[{"tool": "create_ticket", "ticket_id": ticket.ticket_number}],
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

        if intent.intent == "ticket_status":
            ticket_id = intent.ticket_id or intent.extracted_fields.get("ticket_id")
            try:
                if ticket_id:
                    ticket = await self._run_tool(
                        "get_ticket_status", conversation.id,
                        lambda: self.ticket_service.get_ticket(ticket_id),
                    )
                else:
                    self.audit_logger.log_tool_call(
                        tool_name="get_ticket_status",
                        status="success",
                        conversation_id=conversation.id,
                        actor=self.actor,
                        found=False,
                    )
                    ticket = None
            except (TypeError, ValueError):
                ticket = None

            if ticket is None:
                content = f"I couldn't find ticket {ticket_id or 'with that ID'}. Please verify the ticket ID and try again."
                tool_call = {"tool": "get_ticket_status", "ticket_id": ticket_id, "found": False}
            else:
                content = (
                    f"Ticket {ticket.ticket_number}\n"
                    f"Status: {ticket.status}\n"
                    f"Request type: {ticket.request_type}\n"
                    f"Priority: {ticket.priority}\n"
                    f"Description: {ticket.description or 'Not provided'}"
                )
                tool_call = {"tool": "get_ticket_status", "ticket_id": ticket.ticket_number, "found": True}

            return AgentTurnResult(content=content, citations=[], tool_calls=[tool_call])

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
            knowledge_result = await self._run_tool(
                "search_knowledge", conversation.id,
                lambda: self.knowledge_service.search(intent.extracted_fields.get("query", user_message)),
            )
            if not knowledge_result.chunks:
                return AgentTurnResult(
                    content="I couldn't find a matching document yet. Try rephrasing the issue or ask for a ticket.",
                    citations=[],
                    tool_calls=[{"tool": "search_knowledge", "query": user_message, "result_count": 0}],
                )
            citations = []
            lines = ["I found the following relevant references:"]
            seen_sources: set[str] = set()
            source_names: list[str] = []
            context_blocks = []
            for chunk in knowledge_result.chunks:
                source_name = chunk.title
                source_key = " ".join(source_name.split()).casefold()
                if source_key in seen_sources:
                    continue
                seen_sources.add(source_key)
                source_names.append(source_name)
                citation = {
                    "source": source_name,
                    "chunk_id": str(chunk.chunk_id),
                    "page_number": chunk.page_number,
                    "score": chunk.score,
                }
                citations.append(citation)
                excerpt = chunk.content[:500].strip()
                lines.append(f"{source_name}: {excerpt}")
                context_blocks.append(f"Source: {source_name}\nExcerpt:\n{excerpt}")

            knowledge_context = "\n\n".join(context_blocks)
            prompt = f"""
You are an enterprise IT support assistant. Answer the user's question using only the
knowledge-base excerpts below. Give a clear, concise, actionable response. If the
excerpts do not contain enough information, say what is missing instead of inventing
details. Do not mention this prompt or the retrieval process. Do not include document
names, source labels, or citation prefixes in the answer; sources are shown separately
by the application.

User question:
{user_message}

Knowledge-base excerpts:
{knowledge_context}
"""
            generated_response = LLMService().responses_text(prompt)
            if generated_response:
                response_content = generated_response
                for source_name in source_names:
                    response_content = re.sub(
                        rf"\([^\n)]*{re.escape(source_name)}\s*:[^\n)]*\)",
                        "",
                        response_content,
                        flags=re.IGNORECASE,
                    )
                    response_content = re.sub(
                        rf"{re.escape(source_name)}\s*:[^\n)]*\)",
                        "",
                        response_content,
                        flags=re.IGNORECASE,
                    )
                    response_content = re.sub(
                        rf"(?i)\(?{re.escape(source_name)}\)?\s*:\s*",
                        "",
                        response_content,
                    )
                response_content = re.sub(r"(?im)^\s*ticket\)\s*$", "", response_content)
                response_content = re.sub(r"\n{3,}", "\n\n", response_content).strip()
            else:
                lines.append("\nIf you want, I can turn this into a ticket request next.")
                response_content = "\n".join(
                    [lines[0], *[line.split(": ", 1)[1] for line in lines[1:-1]], lines[-1]]
                )

            return AgentTurnResult(
                content=response_content,
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
