# Enterprise IT Support Agent

MVP scaffold for an enterprise-oriented IT support agent with:

- FastAPI backend
- PostgreSQL + SQLAlchemy + Alembic
- Knowledge search with pgvector-ready document chunks
- Conversation history
- Ticket workflow engine
- Next.js 15 chat UI

## Backend

```bash
docker compose up -d db
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

The database container exposes Postgres on `localhost:5432` with the default credentials from `backend/.env`.

## Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

## Testing

Run the regression suite from the repository root:

```bash
./backend/.venv/bin/python -m pytest
```

The suite covers agent intent cases, ticket workflows, API contracts, and OpenAI fallback behavior without requiring OpenAI credits or a running PostgreSQL container.

## Environment

- `backend/.env` should provide `DATABASE_URL` and optionally `OPENAI_API_KEY`
- The backend expects PostgreSQL to be running at `DATABASE_URL` before you use DB-backed endpoints
- `frontend/.env` should provide `NEXT_PUBLIC_API_BASE_URL=/backend-api` and
  `BACKEND_API_BASE_URL=http://127.0.0.1:8000/api/v1`

## Knowledge ingestion

Upload a PDF, DOCX, or TXT file through `POST /api/v1/knowledge/documents` to add searchable chunks.
