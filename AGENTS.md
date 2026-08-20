# Code Comment and Explanation Guidelines

This project should use normal, production-quality software engineering practices.

Use appropriate abstractions, design patterns, framework features, async programming, dependency injection, database patterns, and other engineering practices when they are appropriate for the project.

Whenever you create or modify code, make the code easier to understand through **clear comments, docstrings, and explanations**.

---

## 1. Write Comments for Important Logic

Add comments around important or non-obvious code.

Comments should explain:

- What the code is doing

For important code, also explan:
- Why the code is needed
- Where it fits into the application flow
- What would happen if this logic did not exist

Do not add unnecessary comments to obvious code.


---

## 2. Explain Framework-Specific Code

Add comments when using behavior that may not be obvious to someone who is still learning the framework.

This is especially important for:

- FastAPI dependency injection
- Middleware
- Request lifecycle
- Authentication
- Authorization
- JWT validation
- SQLAlchemy sessions
- SQLAlchemy relationships
- AsyncSession
- `async` / `await`
- Pydantic validation
- Alembic migrations
- Background tasks
- Exception handlers

Example:

```python
# FastAPI resolves this dependency before running the endpoint.
# get_current_user validates the access token and returns the
# authenticated user object that the endpoint can safely use.
current_user: CurrentUser = Depends(get_current_user)
```

---

## 3. Explain Important Python Syntax

When using Python syntax that may be difficult to understand,
add a short explanation when appropriate.

Examples include:

- decorators
- context managers
- generators
- comprehensions with complex conditions
- `yield`
- `*args` / `**kwargs`
- type unions
- dataclasses
- enums
- callbacks
- higher-order functions
- dependency injection patterns

Do not explain basic syntax such as simple variable assignments.

---

## 4. Add Useful Docstrings

Important functions, classes, and services should have docstrings.

The docstring should explain:

1. What the function/class does
2. Why it exists
3. Important inputs
4. What it returns
5. Important side effects, if any

Be concise and easy-understanding.

Example:

```python
async def create_ticket(
    request: TicketCreate,
    db: AsyncSession,
    current_user: CurrentUser,
) -> Ticket:
    """
    Create and persist a new IT support ticket.

    This function is part of the ticket creation workflow. It receives
    validated ticket information from the API layer, associates the ticket
    with the authenticated user, saves it to PostgreSQL, and returns the
    newly created database object.

    Args:
        request:
            Validated ticket information submitted by the user.

        db:
            SQLAlchemy async database session used to persist the ticket.

        current_user:
            Authenticated user making the request.

    Returns:
        The newly created Ticket object.
    """
```

---

## 5. Explain System Flow

When code participates in a larger workflow, add comments explaining where
the code sits in that workflow.

For example:

```python
# Request flow:
#
# HTTP Request
#     ↓
# Request ID Middleware
#     ↓
# Authentication
#     ↓
# FastAPI Endpoint
#     ↓
# Ticket Service
#     ↓
# PostgreSQL
#
# This middleware executes before authentication and the endpoint,
# allowing all downstream logs and audit events to share the same request_id.
```

Prefer this kind of explanation when understanding the surrounding architecture
is necessary to understand the code.

---

## 6. Explain Database Operations

SQLAlchemy and database operations should include comments when their behavior
is not immediately obvious.

Explain things such as:

- why a query is needed
- what records are being selected
- why `flush()` or `commit()` is used
- why `refresh()` is used
- relationship loading
- transactions
- rollback behavior
- indexes or constraints
- database-level security considerations

Example:

```python
db.add(ticket)

# flush() sends the INSERT to PostgreSQL without committing the transaction.
# This allows PostgreSQL to generate fields such as the ticket ID while
# keeping the operation inside the current transaction.
await db.flush()

# Reload database-generated values into the SQLAlchemy object.
await db.refresh(ticket)
```

---

## 7. Explain AI / Agent Logic

Add detailed comments around AI-specific behavior.

This includes:

- OpenAI API calls
- prompt construction
- tool definitions
- tool calling
- tool selection
- intent detection
- planner logic
- workflow routing
- RAG
- embeddings
- vector search
- retrieval
- reranking
- conversation context
- memory
- model routing
- fallback behavior
- structured outputs

Comments should explain both the technical behavior and the reason the component exists.

Example:

```python
# Retrieve enterprise knowledge before asking the LLM to generate an answer.
#
# The LLM itself does not know whether its internal knowledge matches
# our company's current IT policies. Retrieval provides the model with
# authoritative internal documents that it can use as evidence.

chunks = await knowledge_service.search(query)
```

---


---

## 8. Explain Error Handling

When handling errors, explain:

- what failure is being handled
- why this exception is caught here
- whether the error is logged
- whether the transaction is rolled back
- what the user/API receives

Example:

```python
try:
    await db.commit()

except SQLAlchemyError:
    # A failed transaction leaves the SQLAlchemy session in an invalid
    # transactional state. Roll it back before the session can be reused.
    await db.rollback()
    raise
```

---

## 9. Explain Middleware Clearly

For middleware, explain:

- when it executes
- what it adds or modifies
- which downstream components use the result

Example:

```python
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    Attach a unique request ID to every incoming HTTP request.

    The same request ID can later be included in application logs,
    tool-call logs, and audit events. This makes it possible to trace
    everything that happened during one API request.
    """

    request_id = str(uuid.uuid4())

    # request.state is FastAPI/Starlette's request-scoped storage.
    # Anything stored here remains available to downstream dependencies
    # and endpoint code while this specific request is being processed.
    request.state.request_id = request_id

    # Continue passing the request through the remaining middleware,
    # authentication dependencies, and eventually the endpoint.
    response = await call_next(request)

    return response
```

---

## 10. Comment Important Design Decisions

When the implementation uses a design pattern or architectural abstraction,
briefly explain why it is useful here.

Examples:

- Repository pattern
- Service layer
- Tool Registry
- Strategy pattern
- Dependency injection
- Factory
- Adapter
- Middleware
- Event-driven architecture

Do not avoid these patterns simply because they are advanced.

Instead, explain their purpose.

Example:

```python
# ToolRegistry separates tool discovery from tool implementation.
#
# The agent can look up tools by name without knowing which Python module
# contains each implementation. This also gives us one centralized place
# to control which tools are available to the agent.

class ToolRegistry:
    ...
```

---

## 11. Do Not Over-Comment

Comments should improve understanding, not create noise.

Avoid comments that simply translate Python into English.

Bad:

```python
# Loop through tickets
for ticket in tickets:
```

No comment is necessary here.

Add comments primarily for:

- architecture
- business logic
- security
- non-obvious behavior
- framework behavior
- important engineering decisions
- AI/agent behavior
- database behavior

---

## 12. Preserve Existing Useful Comments

When modifying existing code:

- Keep useful comments unless they are no longer accurate.
- Update comments when behavior changes.
- Remove comments that have become misleading.
- Do not delete educational comments merely to make the file shorter.

Comments must always match the current implementation.

---

# After Every Coding Task

After completing a task, provide an explanation using the following structure.

## What Changed

List the important files created or modified and briefly explain what changed.

Example:

```text
backend/app/middleware/request_id.py
- Added middleware that generates a request_id for every HTTP request.

backend/app/models/audit.py
- Added the AuditEvent SQLAlchemy model.

backend/app/services/audit_service.py
- Added the service responsible for writing audit events.
```

## Execution Flow

Explain the runtime flow of the new functionality.

Prefer diagrams such as:

```text
HTTP Request
     ↓
Request ID Middleware
     ↓
Authentication
     ↓
Endpoint
     ↓
Service
     ↓
Database
     ↓
HTTP Response
```

Then explain each step briefly.

## Important Code to Read

Identify the 3–5 most important files, functions, or classes that I should read first.

For each one, explain why it is important.

## Important Concepts

Explain any important programming or software engineering concepts introduced
by the implementation.

For example:

- middleware
- dependency injection
- database transaction
- async/await
- JWT validation
- tool calling
- vector search

Assume I may understand the business requirement but may not yet understand
the underlying programming concept.

## How to Test

Provide concrete steps to verify that the implementation works.

Include when relevant:

- terminal commands
- API requests
- curl commands
- expected HTTP responses
- database queries
- logs to inspect
- failure cases to test

Do not only say "run the tests."

Explain what successful behavior should look like.

---

# General Principle

Write production-quality code normally.

Do not reduce engineering quality or avoid appropriate abstractions because
the developer is learning.

Instead:

**Keep the code professional, and make the reasoning understandable through excellent comments and explanations.**