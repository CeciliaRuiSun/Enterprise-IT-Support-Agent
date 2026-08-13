# Enterprise IT Support Agent

An enterprise-oriented IT support agent with:

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

The database container exposes Postgres on `localhost:5432` with the default credentials from `backend/.env`. After migrations run, the backend automatically indexes supported files from the repository's `Knowledge Base/` folder.

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
- Backend Entra API protection requires `ENTRA_TENANT_ID`,
  `ENTRA_API_CLIENT_ID=5658b4fd-f2e0-4488-8673-1e806af6243f`, and
  `ENTRA_REQUIRED_SCOPE=access_as_user`
- The backend validates both tenant-specific Entra v1.0 and v2.0 access tokens.
  For v1.0 tokens, it accepts the API client ID and the standard
  `api://<API_CLIENT_ID>` identifier URI for this same configured API.
  Prefer setting the API app registration manifest property
  `requestedAccessTokenVersion` to `2`, then sign out and sign in again.
- The backend expects PostgreSQL to be running at `DATABASE_URL` before you use DB-backed endpoints
- `frontend/.env` should provide `NEXT_PUBLIC_API_BASE_URL=/backend-api` and
  `BACKEND_API_BASE_URL=http://127.0.0.1:8000/api/v1`
- Entra sign-in also requires `NEXT_PUBLIC_ENTRA_TENANT_ID`,
  `NEXT_PUBLIC_ENTRA_WEB_CLIENT_ID`, and
  `NEXT_PUBLIC_ENTRA_API_CLIENT_ID=5658b4fd-f2e0-4488-8673-1e806af6243f`
- Register `http://localhost:3000/` as the SPA redirect URI for the web app registration.

## Knowledge ingestion

Supported files in `Knowledge Base/` (`.docx`, `.pdf`, `.txt`, and `.md`) are indexed automatically when the backend starts. Existing files are skipped on later starts.

To sync the folder manually:

```bash
cd backend
./.venv/bin/python scripts/seed_knowledge_base.py
```

You can also upload a PDF, DOCX, or TXT file through `POST /api/v1/knowledge/documents` to add searchable chunks.
