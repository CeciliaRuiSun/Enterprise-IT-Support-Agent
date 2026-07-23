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


# ADR-003: 
Knowledge Retrieval as a standalone subsystem
Workflow engine as a standalone subsystem

# ADR-004: Reason → Act → Observe → Reason