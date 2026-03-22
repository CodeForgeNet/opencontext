# PCSL - Personal Context Sovereignty Layer

<p align="center">
  <a href="https://pcsl.dev"><img src="https://img.shields.io/badge/PCSL-v1.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-green" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.9+-yellow" alt="Python"></a>
</p>

PCSL (Personal Context Sovereignty Layer) is an open protocol that lets you own your AI context and share it selectively with any AI tool — instead of re-explaining yourself every time.

**Without PCSL:** Paste your background into every new AI session.  
**With PCSL:** One local server. Every AI tool instantly knows you.

## 30-Second Demo

```bash
pip install pcsl
pcsl init
pcsl server start
pcsl context show
```

That's it. Your personal context is now running as a local API at `http://localhost:8000`. Any AI tool can request scoped access to it.

## What You Get

- `pcsl context show` — view your full context
- `pcsl context set identity name "Your Name"` — update any field
- `pcsl context get skills` — fetch scope-filtered context via JWT auth
- `pcsl token create my-tool identity,skills` — mint a scoped token for any app
- `pcsl token revoke my-tool` — cut off access instantly
- `pcsl audit` — see exactly who accessed what and when

## CLI Reference

| Command | Description |
|---------|-------------|
| `pcsl init` | Bootstrap `~/.pcsl/` — creates context.json + generates SECRET_KEY |
| `pcsl server start` | Start local API server on port 8000 (detached) |
| `pcsl server stop` | Stop the server |
| `pcsl server status` | Show PID, URL, version |
| `pcsl context show` | Pretty-print your full context.json |
| `pcsl context set <ns> <key> <val>` | Update a context field |
| `pcsl context get <ns>` | Fetch scope-filtered context via API |
| `pcsl token create <id> <scopes>` | Mint a scoped JWT for an external tool |
| `pcsl token revoke <id>` | Revoke a client's access |
| `pcsl audit` | View the full access log as a table |

## Your Context File

After `pcsl init`, edit `~/.pcsl/context.json`:

```json
{
  "pcsl_version": "1.0",
  "identity": {
    "name": "Your Name",
    "profession": "Your Role",
    "location": "City, Country"
  },
  "preferences": {
    "communication_style": "direct, no fluff",
    "tone": "professional"
  },
  "skills": {
    "languages": ["Python", "TypeScript"],
    "domains": ["RAG systems", "LLM optimization"]
  },
  "goals": {
    "short_term": ["ship X", "learn Y"],
    "long_term": ["build Z"]
  }
}
```

Any AI tool you authorize gets only the namespaces you explicitly grant.

## Integrate with Any AI Tool

Any app that speaks HTTP can request your context.

**Python (with SDK):**
```python
from pcsl_sdk import PCSLClient

pcsl = PCSLClient(server_url="http://localhost:8000")
token = pcsl.authorize(client_id="my-app", scopes=["preferences", "skills"])
context = pcsl.get_context(token)
system_prompt = pcsl.inject_into_prompt(token, "You are a helpful assistant.")
```

**Raw HTTP:**
```bash
# 1. Get a token
TOKEN=$(curl -s -X POST http://localhost:8000/pcsl/authorize \
  -H "Content-Type: application/json" \
  -d '{"client_id":"curl-test","scopes":["identity","skills"]}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Fetch your context
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/pcsl/context
```

## How It Works

1. `pcsl init` creates `~/.pcsl/context.json` (your data) and a `SECRET_KEY` (your auth)
2. `pcsl server start` runs a local FastAPI server — only accessible on your machine
3. An AI tool calls `/pcsl/authorize` with a `client_id` and requested `scopes`
4. The server returns a short-lived JWT scoped to exactly those namespaces
5. The tool fetches `/pcsl/context` with the JWT — gets only what it asked for
6. Every access is logged. You can revoke any client at any time.

Your data never leaves your machine unless you choose to expose the server publicly.

## Deploy to Cloud (Optional)

By default PCSL runs locally. To make your context available to cloud-based AI tools:

### Railway (One-Click)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/CodeForgeNet/opencontext)

After deploying:
1. Set these environment variables in Railway dashboard:
   - `SECRET_KEY` — run: `python -c "import secrets; print(secrets.token_hex(32))"`
   - `PCSL_ENCRYPTION_KEY` — run: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - `PCSL_SERVER_URL` — your Railway URL, e.g. `https://your-app.up.railway.app`
2. Add a Volume in Railway, mount at `/app/pcsl/pcsl_server/data` so your context persists across redeploys
3. Edit your context via `POST /pcsl/update` or by updating `context.json` before deploy

### Docker

```bash
git clone https://github.com/CodeForgeNet/opencontext.git
cd pcsl
cp .env.example .env
# Fill in SECRET_KEY and PCSL_ENCRYPTION_KEY in .env
docker-compose up -d
```

## Project Structure

```
PCSL/
├── pcsl/
│   ├── cli.py               # CLI entry point (pcsl command)
│   ├── pcsl_server/         # FastAPI server
│   │   ├── main.py          # API endpoints
│   │   ├── auth.py          # JWT authentication
│   │   └── data/            # User data storage (runtime)
│   ├── chunker.py           # Semantic context chunking
│   ├── mcp_server.py        # MCP protocol server
│   ├── spec/                # Protocol specification
│   ├── pcsl-sdk-python/     # Python SDK
│   ├── pcsl-sdk-js/         # JavaScript SDK
│   ├── pcsl-extension/      # Browser extension
│   └── examples/           # Integration examples
├── pyproject.toml           # Python package configuration
├── docker-compose.yml       # Docker deployment
└── LICENSE                  # Apache 2.0 License
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/pcsl.json` | GET | Discovery endpoint |
| `/pcsl/authorize` | POST | Request scoped access token |
| `/pcsl/context` | GET | Fetch authorized context |
| `/pcsl/context/smart` | GET | Semantic context retrieval |
| `/pcsl/update` | POST | Update context (requires write scope) |
| `/pcsl/audit` | GET | View access logs |
| `/pcsl/revoke` | POST | Revoke client access |

## Context Namespaces

Namespaces allow AI apps to request only the specific context they need. When authorizing, the app requests specific scopes—users approve what gets shared.

- `identity` - Basic user information (name, profession, location)
- `preferences` - AI interaction preferences (tone, communication style)
- `skills` - Technical skills and expertise
- `projects` - Current/past project details
- `goals` - Short and long-term objectives
- `decisions` - Key decisions and reasoning
- `health` - Health-related data (sensitive, off by default)
- `finances` - Financial context (sensitive, off by default)

## Documentation

- [Protocol Specification](pcsl/spec/SPEC.md)
- [Schema Reference](pcsl/spec/SCHEMA.md)
- [Security Best Practices](pcsl/spec/SECURITY.md)
- [Implementation Guide](PCSL_Implementation_Guide.md)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Known Issues

- **content.js raw JSON injection**: The browser extension currently injects raw JSON blob into textarea elements instead of properly simulating keyboard input. This may cause issues with some AI chat interfaces. Track progress at: https://github.com/CodeForgeNet/opencontext/issues

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---

Built by [Karan Singh](https://github.com/CodeForgeNet). PCSL v1.0 — Own your context.
