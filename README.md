# PCSL - Personal Context Sovereignty Layer

<p align="center">
  <a href="https://pcsl.dev"><img src="https://img.shields.io/badge/PCSL-v1.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-green" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.9+-yellow" alt="Python"></a>
</p>

PCSL (Personal Context Sovereignty Layer) is an open protocol that allows users to own, store, and selectively share personal context with AI systems. Instead of re-explaining your background, preferences, and goals to every AI tool you use, PCSL lets you maintain a personal context that AI applications can request access to—with your permission.

**Without PCSL:** You explain your background to every AI tool from scratch.  
**With PCSL:** You deploy once, share your server URL, any AI tool instantly knows you.

## Core Principles

- **User Ownership**: Your context lives on your infrastructure, not in some third-party database
- **Scoped Access**: AI apps get only what they need (e.g., `preferences`, `skills`)
- **Auditable**: Every access is logged and transparent to you
- **Portable**: Any AI system can integrate with standard REST endpoints
- **Offline-first**: Works without a mandatory cloud server

## Features

- **RESTful API Server** - FastAPI-based server with JWT authentication
- **Scoped Token Authorization** - Fine-grained access control to specific context namespaces
- **Semantic Context Retrieval** - AI-powered context chunking to return only relevant information
- **Python SDK** - Easy integration for Python developers (`pip install pcsl-sdk`)
- **JavaScript/TypeScript SDK** - For web and Node.js applications
- **Browser Extension** - Inject your context into Claude.ai and ChatGPT automatically
- **MCP Server** - Model Context Protocol server for AI tool integration
- **Docker Support** - Easy deployment with Docker Compose

## Deploy Your Own PCSL Server

Each person runs their own PCSL instance. Your context lives on your infrastructure.

### One-Click Deploy (Railway)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/karan/pcsl)

After deploying:
1. Set these environment variables in Railway dashboard:
   - `SECRET_KEY` — run: `python -c "import secrets; print(secrets.token_hex(32))"`
   - `PCSL_ENCRYPTION_KEY` — run: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - `PCSL_SERVER_URL` — your Railway URL, e.g. `https://your-app.up.railway.app`
2. Add a Volume in Railway, mount at `/app/pcsl/pcsl_server/data` so your context persists across redeploys
3. Edit your context via `POST /pcsl/update` or by updating `context.json` before deploy

### Manual Deploy (Docker)

```bash
git clone https://github.com/karan/pcsl.git
cd pcsl
cp .env.example .env
# Fill in SECRET_KEY and PCSL_ENCRYPTION_KEY in .env
docker-compose up -d
```

Your server runs at `http://your-server-ip:8000`

## Quick Start

> **Note:** This section is for contributors and developers who want to run PCSL locally. If you just want to deploy and use PCSL, see **Deploy Your Own** above.

### Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/karan/pcsl.git
cd pcsl

# Install dependencies
pip install -e .

# Or with AI features (for semantic chunking)
pip install -e ".[ai]"

# Install the Python SDK (for integration examples)
pip install -e pcsl/pcsl-sdk-python

# Set up environment variables
cp .env.example .env

# Generate required keys (run these and copy the output to .env)
python -c "import secrets; print(secrets.token_hex(32))"       # → SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # → PCSL_ENCRYPTION_KEY
```

### Running the Server

```bash
# Start the PCSL server
uvicorn pcsl.pcsl_server.main:app --reload

# Or with Docker
docker-compose up -d
```

The server will start at `http://localhost:8000`

### Using the SDK

```python
from pcsl_sdk import PCSLClient

# Initialize with your PCSL server URL
pcsl = PCSLClient(server_url="http://localhost:8000")

# Authorize and fetch context
token = pcsl.authorize(client_id="my-app", scopes=["preferences", "skills"])
context = pcsl.get_context(token)

# Inject into your system prompt
system_prompt = pcsl.inject_into_prompt(token, "You are a helpful assistant.")
```

### Browser Extension

To install the browser extension:

1. Open Chrome → `chrome://extensions/` → Enable **Developer Mode**
2. Click **Load unpacked** → select the `pcsl/pcsl-extension/` folder
3. Click the extension icon → enter your PCSL server URL → Save

## Project Structure

```
PCSL/
├── context.json              # Sample user context
├── pyproject.toml            # Python package configuration
├── docker-compose.yml        # Docker deployment
├── LICENSE                   # Apache 2.0 License
├── pcsl/
│   ├── spec/                 # Protocol specifications
│   │   ├── SPEC.md          # Protocol definition
│   │   ├── SCHEMA.md        # JSON-LD schema
│   │   └── SECURITY.md      # Security best practices
│   ├── pcsl_server/         # FastAPI server
│   │   ├── main.py          # API endpoints
│   │   ├── auth.py          # JWT authentication
│   │   └── data/            # User data storage
│   ├── pcsl-sdk-python/     # Python SDK
│   ├── pcsl-sdk-js/         # JavaScript SDK
│   ├── pcsl-extension/      # Browser extension
│   ├── pcsl-directory/      # User directory service
│   ├── examples/            # Integration examples
│   ├── chunker.py           # Semantic context chunking
│   └── mcp_server.py        # MCP protocol server
└── tests/                   # Test suite
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

```python
# Example: only request what your app needs
token = pcsl.authorize(client_id="my-app", scopes=["skills", "preferences"])
```

## Documentation

- [Protocol Specification](pcsl/spec/SPEC.md)
- [Schema Reference](pcsl/spec/SCHEMA.md)
- [Security Best Practices](pcsl/spec/SECURITY.md)
- [Implementation Guide](PCSL_Implementation_Guide.md)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Known Issues

- **content.js raw JSON injection**: The browser extension currently injects raw JSON blob into textarea elements instead of properly simulating keyboard input. This may cause issues with some AI chat interfaces. Track progress at: https://github.com/karan/pcsl/issues

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---

Built by [Karan Singh](https://github.com/karan). PCSL v1.0 — Own your context.
