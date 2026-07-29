# API Design

## Overview

This document specifies the REST APIs provided by the IT Support Agent. The APIs cover authentication, conversation management, knowledge base operations, ticket management, and administrative functions.

### Base URL

```
/api/v1
```

### Authentication

All protected endpoints are secured using Bearer Token authentication.

```
Authorization: Bearer <access_token>
```

---

# Authentication APIs

## Login

### Endpoint

```
POST /auth/login
```

### Description

Authenticate a user and issue an access token.

### Request

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

### Response

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 3600
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 200  | Success             |
| 401  | Invalid credentials |


---

# Conversation

## Create conversation

### Endpoint

```
POST /conversations
```

### Description

Create a new conversation and send user the first message

### Request

```json
{
  "message_content": "..."
}
```

### Response

```json
{
  "conversation_id":"...",
  "message_id":"...",
  "role":"assistant"
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 201  | Resource created    |
| 401  | Invalid credentials |


---

## Check conversation

### Endpoint

```
GET /conversations/{conversation_id}
```

### Description

Get one conversation history.

### Response

```json
{
  "conversation_id":"...",
  "messages": [
{ "message_id":"...",
  "role":"...",
  "content":"...",
  "created_at":"..."

}, {"message_id":"...",
  "role":"...",
  "content":"...",
  "created_at":"..."

}
]
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 200  | Success             |
| 401  | Invalid credentials |
| 404  | Not found           |


---
## Get all conversation history for current user

### Endpoint

```
GET /conversations
```

### Description

Get a list of all conversations.

### Response

```json
{
  "conversations":[]
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 200  | Success             |
| 401  | Invalid credentials |
| 404  | Not found           |


---

## Send message

### Endpoint

```
POST /conversations/{conversation_id}/messages
```

### Description

Send a user message to AI agent.

### Request

```json
{
  "role": "user,
  "message_content": "..."
}
```

### Response

```json
{
  "message_id":"...",
  "role":"assistant",
  "content": "...",
  "citation": {...},
  "tool_calls":[...],
  "conversation_id":"...",
  "created_at":"..."
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 200  | Success             |
| 401  | Invalid credentials |
| 404  | Not found           |


---

# Knowledge

## Knowledge retrieval

### Endpoint

```
GET /knowledge/search?q=vpn
```

### Description

Retrieve knowledge from knowledge base

### Response

```json
{
  "results":[
    {
      "document_id":"...",
      "title":"...",
      "content":"...",
      "score":0.93
    }
  ]
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 200  | Success             |
| 401  | Invalid credentials |
| 404  | Not found           |


---

# Ticket

## Create ticket

### Endpoint

```
POST /tickets
```

### Description

Create a new IT support ticket

### Request

```json
{
  "request_type": "...",
  "request_for": "...",
  "business_justification": "...",
  "description": "...",
  "priority": "...",
  "created_at": "..."
}
```

### Response

```json
{
  "ticket_id": {...},
  "status": {...}
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 201  | Resource Created    |
| 400  | Bad request         |
| 401  | Invalid credentials |
| 403  | Forbidden           |


---

## Update ticket

### Endpoint

```
PATCH /tickets/{ticket_id}
```

### Description

User updates ticket

### Request

```json
{
  "ticket_id": "...",
  "update_column": "...",
  "new_content": "..."
}
```

### Response

```json
{
  "ticket_id": {...},
  "update_column": "...",
  "status": {...}
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 200  | Success             |
| 401  | Invalid credentials |
| 403  | Forbidden           |
| 404  | Not found           |


---

## Check ticket

### Endpoint

```
GET /tickets/{ticket_id}
```

### Description

User look up a ticket

### Response

```json
{
  "request_type": "...",
  "request_for": "...",
  "business_justification": "...",
  "description": "...",
  "priority": "...",
  "created_at": "...",
  "assigned_to": "...",
  "updated_at": "...",
  "comments": "..."
}
```

### Status Codes


| Code | Description         |
| ---- | ------------------- |
| 200  | Success             |
| 401  | Invalid credentials |
| 404  | Not found           |


---

# Common Status Codes


| Code | Meaning               |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Resource Created      |
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Resource Not Found    |
| 409  | Conflict              |
| 429  | Too Many Requests     |
| 500  | Internal Server Error |


---

# API Versioning

Now：

```
/api/v1
```

Future：

```
/api/v2
```

---

# Security

- JWT Authentication
- HTTPS Only
- Role-Based Access Control (RBAC)
- API Rate Limiting
- Request Logging
- Audit Logging

---

# Future APIs

- Streaming Chat (`/chat/stream`)
- Feedback API
- Tool Execution API
- Conversation Summary API
- Memory API
- Notification API

