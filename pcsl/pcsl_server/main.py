# pcsl/pcsl_server/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging
import os
import json
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel

from pcsl.pcsl_server.auth import create_access_token, get_current_token_data

logger = logging.getLogger("pcsl-server")

app = FastAPI(title="PCSL Server (v1.0)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PCSL_HOME = Path.home() / ".pcsl"
DATA_DIR = PCSL_HOME / "data"

_LOCALHOST_HOSTS = {"127.0.0.1", "::1", "localhost"}
_revocation_cache: dict = {}  # user_id -> (frozenset[client_id], loaded_at)
_REVOCATION_CACHE_TTL = 30  # seconds
_MAX_VALUE_SIZE = 10 * 1024  # 10 KB (JSON-encoded)


def get_user_context_path(user_id: str = "local-user") -> str:
    home_ctx = PCSL_HOME / "context.json"
    if home_ctx.exists():
        return str(home_ctx)
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "data", "users", f"{user_id}.json")
    )


def get_context(user_id: str = "local-user") -> dict:
    path = get_user_context_path(user_id)
    if not os.path.exists(path):
        migration_source = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "context.json")
        )
        if os.path.exists(migration_source):
            logger.info("Migrating context from %s to %s", migration_source, path)
            with open(migration_source, "r") as f:
                data = json.load(f)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            _atomic_write(path, data)
            return data
        raise HTTPException(status_code=500, detail=f"Context not found for user {user_id}")
    with open(path, "r") as f:
        return json.load(f)


def save_context(ctx: dict, user_id: str = "local-user") -> None:
    updated = {**ctx, "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    path = get_user_context_path(user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _atomic_write(path, updated)


def _atomic_write(path: str, data: dict) -> None:
    dir_path = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", dir=dir_path, delete=False, suffix=".tmp") as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, path)


def log_access(user_id: str, client_id: str, scopes: list) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    log_path = DATA_DIR / f"{user_id}_access_log.json"
    log = []
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []

    log.append({
        "client_id": client_id,
        "scopes": scopes,
        "timestamp": str(datetime.now(timezone.utc)),
    })
    log = log[-50:]

    _atomic_write(str(log_path), log)


def get_revocation_list_path(user_id: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return str(DATA_DIR / f"{user_id}_revoked.json")


def is_token_revoked(user_id: str, client_id: str) -> bool:
    now = time.monotonic()
    cached = _revocation_cache.get(user_id)
    if cached is not None:
        revoked_set, loaded_at = cached
        if now - loaded_at < _REVOCATION_CACHE_TTL:
            return client_id in revoked_set

    path = get_revocation_list_path(user_id)
    if not os.path.exists(path):
        _revocation_cache[user_id] = (frozenset(), now)
        return False
    with open(path, "r") as f:
        revoked = frozenset(json.load(f))
    _revocation_cache[user_id] = (revoked, now)
    return client_id in revoked


def revoke_client(user_id: str, client_id: str) -> None:
    path = get_revocation_list_path(user_id)
    revoked = []
    if os.path.exists(path):
        with open(path, "r") as f:
            revoked = json.load(f)
    if client_id not in revoked:
        revoked.append(client_id)
    _atomic_write(path, revoked)
    _revocation_cache.pop(user_id, None)


class AuthRequest(BaseModel):
    client_id: str
    scopes: List[str]
    expires_in: Optional[int] = 3600


@app.get("/")
def read_root():
    return {"pcsl": "v1.0", "status": "online"}


@app.get("/.well-known/pcsl.json")
def get_pcsl_spec():
    return {
        "version": "1.0",
        "server_url": os.getenv("PCSL_SERVER_URL", "http://localhost:8000"),
        "auth_endpoint": "/pcsl/authorize",
        "context_endpoint": "/pcsl/context",
        "smart_context_endpoint": "/pcsl/context/smart",
        "spec_url": "https://pcsl.dev/spec/v1",
    }


@app.post("/pcsl/authorize")
def authorize(req: AuthRequest, request: Request):
    host = request.client.host if request.client else ""
    if host not in _LOCALHOST_HOSTS:
        raise HTTPException(status_code=403, detail="Authorization only accessible from localhost")

    if is_token_revoked("local-user", req.client_id):
        raise HTTPException(status_code=403, detail="Client has been revoked")

    access_token = create_access_token(
        data={"sub": "local-user", "scopes": req.scopes, "client_id": req.client_id},
        expires_delta=timedelta(seconds=req.expires_in or 3600),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/pcsl/context")
def read_context(token_data: dict = Depends(get_current_token_data)):
    user_id = token_data["user_id"]
    client_id = token_data.get("client_id", "unknown-client")

    if is_token_revoked(user_id, client_id):
        raise HTTPException(status_code=401, detail="Access revoked for this client")

    full_ctx = get_context(user_id)
    user_scopes = token_data["scopes"]

    log_access(user_id, client_id, user_scopes)

    filtered_ctx = {
        "pcsl_version": full_ctx.get("pcsl_version", "1.0"),
        "last_updated": full_ctx.get("last_updated"),
    }
    for scope in user_scopes:
        if scope in full_ctx:
            filtered_ctx[scope] = full_ctx[scope]

    return {"context": filtered_ctx}


@app.get("/pcsl/context/smart")
def read_smart_context(query: str, token_data: dict = Depends(get_current_token_data)):
    """Returns only context chunks most relevant to the query."""
    user_id = token_data["user_id"]
    client_id = token_data.get("client_id", "unknown-client")

    if is_token_revoked(user_id, client_id):
        raise HTTPException(status_code=401, detail="Access revoked for this client")

    from pcsl.chunker import get_relevant_context

    # Build authorized context directly — avoids double-logging via read_context
    full_ctx = get_context(user_id)
    user_scopes = token_data["scopes"]
    log_access(user_id, client_id, user_scopes)

    authorized_ctx = {
        "pcsl_version": full_ctx.get("pcsl_version", "1.0"),
        "last_updated": full_ctx.get("last_updated"),
    }
    for scope in user_scopes:
        if scope in full_ctx:
            authorized_ctx[scope] = full_ctx[scope]

    relevant_ctx = get_relevant_context(authorized_ctx, query)

    return {"context": relevant_ctx, "mode": "semantic", "query": query}


@app.get("/pcsl/audit")
def get_audit_log(token_data: dict = Depends(get_current_token_data)):
    user_id = token_data["user_id"]
    log_path = DATA_DIR / f"{user_id}_access_log.json"
    try:
        with open(log_path, "r") as f:
            return {"log": json.load(f)}
    except FileNotFoundError:
        return {"log": []}


@app.post("/pcsl/update")
def update_context(
    namespace: str = Body(...),
    key: str = Body(...),
    value: dict = Body(...),
    token_data: dict = Depends(get_current_token_data),
):
    if len(json.dumps(value)) > _MAX_VALUE_SIZE:
        raise HTTPException(status_code=413, detail="Value payload too large (max 10 KB)")

    user_id = token_data["user_id"]
    if namespace not in token_data["scopes"]:
        raise HTTPException(
            status_code=403, detail=f"Insufficient scope to update namespace: {namespace}"
        )

    ctx = get_context(user_id)
    updated_ns = {**ctx.get(namespace, {}), key: value}
    save_context({**ctx, namespace: updated_ns}, user_id)
    return {"status": "success", "updated_namespace": namespace}


@app.post("/pcsl/revoke")
def revoke_access(
    client_id: str = Body(..., embed=True),
    token_data: dict = Depends(get_current_token_data),
):
    user_id = token_data["user_id"]
    revoke_client(user_id, client_id)
    return {"status": "revoked", "client_id": client_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
