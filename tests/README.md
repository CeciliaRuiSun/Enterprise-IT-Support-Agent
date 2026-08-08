# Regression Tests

The suite is split by responsibility:

- `unit/` tests small deterministic components.
- `integration/` tests service behavior across workflows and persistence boundaries.
- `api/` tests HTTP status codes, validation, and CORS contracts.
- `agent/` covers the supported user intents and ticket workflow states.

Run the full suite from the repository root:

```bash
./backend/.venv/bin/python -m pytest
```

The default suite does not call OpenAI or require PostgreSQL. Database-backed tests can be added separately with an explicit test database URL.
