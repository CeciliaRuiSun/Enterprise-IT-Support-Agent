from pathlib import Path

import pytest

from app.services.document_ingestion import DocumentIngestionService
from app.models.common import KnowledgeDocument


class NoEmbedding:
    def embed_query(self, text: str):
        return None


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return list(self.values)


class FakeSession:
    def __init__(self):
        self.source_paths = set()
        self.items = []

    async def scalars(self, statement):
        return ScalarResult(self.source_paths)

    def add(self, item):
        self.items.append(item)
        if isinstance(item, KnowledgeDocument):
            self.source_paths.add(item.source_path)

    async def flush(self):
        return None


def test_repository_knowledge_base_contains_supported_documents():
    files = DocumentIngestionService.knowledge_base_files()

    assert {path.name for path in files} == {
        "Enterprise_Printer_Troubleshooting_Guide.docx",
        "Enterprise_VPN_Connection_Guide.docx",
        "ServiceNow_User_Guide_Submitting_and_Tracking_Tickets.docx",
    }


@pytest.mark.asyncio
async def test_knowledge_base_sync_indexes_files_once():
    session = FakeSession()
    service = DocumentIngestionService(session, embedding_service=NoEmbedding())

    first_sync = await service.sync_knowledge_base()
    second_sync = await service.sync_knowledge_base()

    assert len(first_sync) == 3
    assert second_sync == []
    assert {document.source_path for document in first_sync} == session.source_paths


def test_docx_knowledge_base_file_is_parsed_into_searchable_text():
    service = DocumentIngestionService(FakeSession(), embedding_service=NoEmbedding())
    path = Path("Knowledge Base/Enterprise_VPN_Connection_Guide.docx")

    parsed = service.parse_document(path.read_bytes(), path.name)

    assert parsed.file_type == "docx"
    assert parsed.title == "Enterprise_VPN_Connection_Guide"
    assert "VPN" in parsed.text
