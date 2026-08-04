## User
- user_id
- email
- full_name

## Conversation
- conversation_id
- user_id
- status
- created_at

## Message
- message_id
- role
- content
- conversation_id
- time

## Knowledge Document
- document_id
- title
- created_at
- updated_at

## Toolcall
- action_id
- tool_name
- status
- latency

## Ticket
- ticket_id
- submitted_by
- request_type
- request_for
- business_justification
- description
- priority
- assigned_to
- status
- comments
- created_at
- updated_at

## DocumentChunk
- chunk_id
- document_id
- content
- chunk_index
- embedding
- page_number
- metadata
- created_at

## WorkflowRuns
- id
- conversation_id
- workflow_type
- status
- state JSONB
- created_at
- updated_at
