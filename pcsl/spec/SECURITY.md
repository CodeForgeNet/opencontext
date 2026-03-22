# PCSL Security Specification

PCSL prioritizes user context sovereignty and security. This document details the threat model and mandatory security practices.

## Threat Model

### Adversary: Malicious AI Application
**Goal**: Steal full personal context instead of only the requested scopes.
**Mitigation**: Mandatory scoped JWTs. The PCSL server MUST NOT return namespaces outside the scopes granted by the token.

### Adversary: Eavesdropper
**Goal**: Intercept context in transit.
**Mitigation**: All PCSL discovery and context endpoints MUST be served over HTTPS.

### Adversary: Host Compromise
**Goal**: Gain access to local context storage.
**Mitigation**: Mandatory encryption-at-rest (AES-256). Context SHOULD be stored in encrypted form when not in use.

## Security Requirements

### 1. Token Lifecycle
- Access tokens SHOULD be short-lived (e.g., 3600 seconds).
- Long-lived refresh tokens MAY be implemented for trusted clients.
- Scoped tokens MUST explicitly list the allowed namespaces in the `scopes` claim.

### 2. Encryption at Rest
- Local implementations MUST use AES-256-CBC or similar.
- Keys SHOULD NOT be stored in the same directory as the encrypted context.
- Servers MUST use environment variables for secret keys.

### 3. Auditing
- Every successful context retrieval MUST be logged on the PCSL server.
- The log entry MUST contain: `timestamp`, `client_id`, `scopes_accessed`, and `result_status`.
- Users SHOULD have an `/audit` endpoint to review access history.

### 4. User Consent
- Authorizing a new `client_id` SHOULD require interactive user approval.
- The authorization UI MUST clearly display the requested scopes.

## Best Practices
- **Rotate Secrets**: Regularly update the `PCSL_SECRET`.
- **Minimal Scopes**: AI apps SHOULD only request the minimal set of namespaces needed for their current task.
- **Client Revocation**: Users MUST be able to revoke a specific `client_id`'s access immediately.
