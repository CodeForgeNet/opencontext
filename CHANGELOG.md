# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-03-23

### Added
- `pcsl` CLI with `init`, `server`, `context`, `token`, `audit` commands
- `~/.pcsl/` local environment bootstrapping via `pcsl init`
- Detached server management via `pcsl server start/stop/status`
- Scope-filtered context retrieval via `pcsl context get`
- JWT token minting and revocation via `pcsl token create/revoke`
- Access audit log via `pcsl audit`

### Changed
- `auth.py` now loads `~/.pcsl/.env` instead of repo-local `.env`
- `main.py` now writes audit logs and revocation lists to `~/.pcsl/data/`
- `get_user_context_path()` now prefers `~/.pcsl/context.json`
- README rewritten with CLI-first quickstart

## [1.0.0] - 2026-03-22

### Added

- Initial release of PCSL (Personal Context Sovereignty Layer)
- FastAPI-based PCSL server with JWT authentication
- Scoped token authorization for fine-grained access control
- RESTful API endpoints following the PCSL protocol specification
- Python SDK (`pcsl-sdk`) for easy integration
- JavaScript/TypeScript SDK for web and Node.js applications
- Browser extension for injecting context into Claude.ai and ChatGPT
- MCP (Model Context Protocol) server for AI tool integration
- Semantic context chunking using sentence-transformers
- PCSL Directory service for user discovery
- Docker and Docker Compose support for easy deployment
- Protocol specification documents (SPEC.md, SCHEMA.md, SECURITY.md)
- Example integrations for Claude, OpenAI, and LangChain

### Features

- User context storage with namespace-based organization
- Access audit logging for transparency
- Context update endpoint with scope validation
