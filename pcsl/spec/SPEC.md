# PCSL Protocol Specification v1.0

## Overview
PCSL (Personal Context Sovereignty Layer) is an open protocol that allows
users to own, store, and selectively share personal context with AI systems.

## Discovery
A PCSL-enabled user exposes a discovery JSON at:
`GET /.well-known/pcsl.json`

### Response Format:
```json
{
  "pcsl_version": "1.0",
  "endpoints": {
    "authorize": "/pcsl/authorize",
    "context": "/pcsl/context",
    "update": "/pcsl/update",
    "revoke": "/pcsl/revoke",
    "audit": "/pcsl/audit"
  }
}
```

## Authorization
`POST /pcsl/authorize`

### Request:
- `client_id` (str): Unique identifier for the AI application.
- `scopes` (List[str]): Requested namespaces (e.g., `["preferences", "skills"]`).
- `expires_in` (int): Requested token lifetime in seconds.

### Response:
- `access_token` (str): JWT Bearer token.
- `token_type` (str): "bearer".

## Context Retrieval
`GET /pcsl/context`
Header: `Authorization: Bearer <token>`

### Response:
- `context` (dict): The requested personal context namespaces.
- `scopes_granted` (List[str]): Confirmed access scopes.

## Context Update (Optional)
`POST /pcsl/update`
Header: `Authorization: Bearer <token>`

### Request:
- `namespace` (str): Target namespace.
- `key` (str): Target key.
- `value` (any): New value.

## Revocation
`POST /pcsl/revoke?client_id=<id>`
Header: `Authorization: Bearer <token>`

## Standard Namespaces
- `identity`: Basic user information.
- `preferences`: User-specific AI interaction preferences.
- `skills`: User's professional or technical expertise.
- `projects`: Current or past project details.
- `goals`: Short and long-term objectives.
- `decisions`: Log of key decisions and their reasoning.
- `health`: (Sensitive) Health-related data.
- `finances`: (Sensitive) Financial context.

## Token Specification
JWT signed with HS256 or RS256. Payload must contain:
- `sub`: User identifier.
- `client_id`: Application identifier.
- `scopes`: List of authorized namespaces.
- `exp`: Expiration timestamp.
