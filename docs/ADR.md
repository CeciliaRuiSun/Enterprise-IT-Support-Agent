**Version:** 1.0  
**Author:** Rui Sun  
**Status:** Draft  
**Last Updated:** 2026-Jul-13

---

# ADR-001: V1 Hybrid IT Support Agent

Agent is Orchestrator
**With:**

Knowledge Assistant
IT Troubleshooting Agent

**Support:**

Multi-turn conversation
Context-aware troubleshooting
Knowledge retrieval
Ticket creation
Human escalation

# ADR-002: Agent Decision Architecture

```
              Agent Orchestrator
                     |
        +------------+-------------+
        |                          |
        v                          v
   LLM Reasoning             Workflow Engine

```

Knowledge Retrieval as a standalone subsystem
Workflow engine as a standalone subsystem

# ADR-003: Create ticket workflow
```
User message

    ↓

LLM identifies if user wants to submit ticket

    ↓

LLM identify ticket type

    ├── software_request

    ├── hardware_request

    └── incident_ticket

    ↓

Load corresponding questionnaire configuration

    ↓

LLM extract information from user's message and user's personal data

    ↓

workflow engine check what information is missing

    ↓

workflow asks for missing information

    ↓

all information collected

    ↓

show ticket summary to user

    ↓

waiting for user's confirmation

    ↓

call create_ticket tool
```

# ADR-004: Authentication
Use Microsoft Entra tenant. Agent authenticate via Microsoft Entra ID. Then validate token.
```
Employee
    │
    │ Click "Sign in with Microsoft"
    ▼
Next.js
    │
    │ Redirect
    ▼
Microsoft Entra ID
    │
    │ Login
    │
    │ Returns authorization result
    ▼
Next.js / MSAL
    │
    │ obtains Access Token
    ▼
POST /api/v1/conversations
Authorization: Bearer eyJ...
    │
    ▼
FastAPI
    │
    │ Validate JWT
    ▼
CurrentUser
{
    "entra_user_id": "...",
    "email": "cecilia@yourtenant.onmicrosoft.com",
    "name": "Cecilia Sun",
    "roles": ["employee"]
}
    │
    ▼
AgentContext
    │
    ▼
IT Agent
```

# ADR-005: Audit Logging
Who did what, when, to what resource, and what happened?

```
                    ┌─────────────┐
                    │   Employee  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    └──────┬──────┘
                           │
                       Request ID
                           │
                           ▼
                  ┌──────────────────┐
                  │ Authentication   │
                  │   CurrentUser    │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │     Agent        │
                  │                  │
                  │ Intent Detection │
                  │ Planner          │
                  │ Workflow Engine  │
                  └───────┬──────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Knowledge       Tools        Tickets
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │  AuditLogger   │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │  audit_events  │
                  └────────────────┘
```



# ADR-006: Evaluation & Observability

```
User Request
    ↓
FastAPI Middleware
    ├── request_id
    └── trace_id
          ↓
      Agent Run
          ↓
 ┌─────────────────────────────┐
 │ Intent Detection            │
 │ Knowledge Retrieval         │
 │ LLM Generation              │
 │ Tool Selection              │
 │ Tool Execution              │
 │ Workflow                    │
 │ Response Generation         │
 └─────────────────────────────┘
          ↓
     Observability
      /          \
 Traces/Metrics   Logs
          ↓
       Evaluation
          ↓
   Eval Score / Regression

```