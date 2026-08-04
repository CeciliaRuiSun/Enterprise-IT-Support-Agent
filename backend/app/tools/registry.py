from __future__ import annotations

from app.tools.knowledge import SearchKnowledgeTool
from app.tools.ticket import CreateTicketTool


class ToolRegistry:
    def __init__(
        self,
        search_knowledge_tool: SearchKnowledgeTool,
        create_ticket_tool: CreateTicketTool,
    ) -> None:
        self.search_knowledge_tool = search_knowledge_tool
        self.create_ticket_tool = create_ticket_tool

