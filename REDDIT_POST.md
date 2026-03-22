**The problem:** Every time you start a new AI session, you're a stranger.
You paste your background, preferences, and tech stack into the system prompt.
Again. For the 50th time.

**What I built:** PCSL (Personal Context Sovereignty Layer) — a local server + CLI
that stores your personal context and lets any AI tool request scoped access to it.

---

**3 commands to get started:**

```bash
pip install pcsl
pcsl init        # creates ~/.pcsl/context.json + generates your secret key
pcsl server start  # starts local API on http://localhost:8000
```

Then edit `~/.pcsl/context.json` with your actual details and any AI tool
can request exactly the context it needs via JWT-scoped tokens:

```bash
# Mint a scoped token for a tool
pcsl token create my-vscode-plugin identity,skills

# See who accessed what
pcsl audit

# Revoke access instantly
pcsl token revoke my-vscode-plugin
```

---

**How it works:**

1. Your context lives at `~/.pcsl/context.json` — yours, local, no cloud
2. An AI tool calls `/pcsl/authorize` requesting specific scopes (e.g. `identity,skills`)
3. It gets a short-lived JWT — can only read what it asked for
4. Every access is logged. You can revoke any client at any time.

It's just HTTP so anything can integrate with it:

```bash
curl -X POST http://localhost:8000/pcsl/authorize \
  -d '{"client_id":"my-app","scopes":["identity","skills"]}' \
  -H "Content-Type: application/json"
```

---

**What's in the repo:**
- FastAPI server with JWT auth + scope filtering
- `pcsl` CLI (all commands shown above)
- Python SDK (`pip install pcsl-sdk`)
- Browser extension (Chrome) that injects your context into Claude.ai / ChatGPT
- MCP server stub for agent tool integration
- Formal protocol spec in `pcsl/spec/`

**GitHub:** https://github.com/CodeForgeNet/opencontext

---

Looking for feedback on:
1. Is the scope model (namespace-based) the right abstraction?
2. Would you actually use this? What's missing?
3. Anyone interested in building integrations for specific tools?

Happy to answer questions.
