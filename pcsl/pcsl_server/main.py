# pcsl/pcsl_server/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Body
from typing import List, Optional
import os
import json
from datetime import timedelta
from cryptography.fernet import Fernet
from pydantic import BaseModel

# Internal imports - using absolute imports from pcsl package
from pcsl.pcsl_server.auth import create_access_token, get_current_token_data

app = FastAPI(title="PCSL Server (v1.0)")

# Path to the shared context file. 
def get_user_context_path(user_id: str = "local-user"):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "users", f"{user_id}.json"))

def get_context(user_id: str = "local-user"):
    path = get_user_context_path(user_id)
    if not os.path.exists(path):
        # Fallback to migration source if exists, or error
        migration_source = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "context.json"))
        if os.path.exists(migration_source):
             print(f"[*] Migrating context from {migration_source} to {path}")
             with open(migration_source, "r") as f:
                 data = json.load(f)
             os.makedirs(os.path.dirname(path), exist_ok=True)
             with open(path, "w") as f:
                 json.dump(data, f, indent=2)
             return data
        raise HTTPException(status_code=500, detail=f"Context not found for user {user_id}")
    with open(path, "r") as f:
        return json.load(f)

def save_context(ctx, user_id: str = "local-user"):
    from datetime import datetime
    ctx["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    path = get_user_context_path(user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(ctx, f, indent=2)

def log_access(user_id: str, client_id: str, scopes: list):
    from datetime import datetime
    log_path = os.path.join(os.path.dirname(__file__), "data", "users", f"{user_id}_access_log.json")
    log = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []

    log.append({
        "client_id": client_id,
        "scopes": scopes,
        "timestamp": str(datetime.utcnow())
    })

    # Keep only last 50 logs to prevent bloat
    log = log[-50:]

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

def get_revocation_list_path(user_id: str) -> str:
    return os.path.join(os.path.dirname(__file__), "data", "users", f"{user_id}_revoked.json")

def is_token_revoked(user_id: str, client_id: str) -> bool:
    path = get_revocation_list_path(user_id)
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        revoked = json.load(f)
    return client_id in revoked

def revoke_client(user_id: str, client_id: str):
    path = get_revocation_list_path(user_id)
    revoked = []
    if os.path.exists(path):
        with open(path, "r") as f:
            revoked = json.load(f)
    if client_id not in revoked:
        revoked.append(client_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(revoked, f, indent=2)

class AuthRequest(BaseModel):
    client_id: str
    scopes: List[str]
    expires_in: Optional[int] = 3600

@app.get("/")
def read_root():
    return {"pcsl": "v1.0", "status": "online"}

@app.get("/.well-known/pcsl.json")
def get_pcsl_spec():
    # Return the metadata about this server
    return {
        "version": "1.0",
        "server_url": os.getenv("PCSL_SERVER_URL", "http://localhost:8000"),
        "auth_endpoint": "/pcsl/authorize",
        "context_endpoint": "/pcsl/context",
        "smart_context_endpoint": "/pcsl/context/smart",
        "spec_url": "https://pcsl.dev/spec/v1"
    }

@app.post("/pcsl/authorize")
def authorize(req: AuthRequest):
    # Check if this client has been revoked
    if is_token_revoked("local-user", req.client_id):
        raise HTTPException(status_code=403, detail="Client has been revoked")
    
    # For now, we auto-approve all local authorization requests.
    # In a real public server, this would have a UI approval screen.
    access_token = create_access_token(
        data={"sub": "local-user", "scopes": req.scopes, "client_id": req.client_id},
        expires_delta=timedelta(seconds=req.expires_in or 3600)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/pcsl/context")
def read_context(token_data: dict = Depends(get_current_token_data)):
    user_id = token_data["user_id"]
    client_id = token_data.get("client_id", "unknown-client")
    
    # Check if client has been revoked
    if is_token_revoked(user_id, client_id):
        raise HTTPException(status_code=401, detail="Access revoked for this client")
    
    full_ctx = get_context(user_id)
    user_scopes = token_data["scopes"]
    
    # Log the access
    log_access(user_id, client_id, user_scopes)
    
    # Simple scoper: only return the top-level keys requested in scopes.
    # Plus mandatory fields like pcsl_version.
    filtered_ctx = {
        "pcsl_version": full_ctx.get("pcsl_version", "1.0"),
        "last_updated": full_ctx.get("last_updated")
    }
    
    for scope in user_scopes:
        if scope in full_ctx:
            filtered_ctx[scope] = full_ctx[scope]
            
    return {"context": filtered_ctx}

@app.get("/pcsl/context/smart")
def read_smart_context(query: str, token_data: dict = Depends(get_current_token_data)):
    """
    Returns only the context chunks most relevant to the query.
    Requires the same scopes as the regular context endpoint.
    """
    user_id = token_data["user_id"]
    client_id = token_data.get("client_id", "unknown-client")
    
    # Check if client has been revoked
    if is_token_revoked(user_id, client_id):
        raise HTTPException(status_code=401, detail="Access revoked for this client")
    
    from pcsl.chunker import get_relevant_context
    
    # First get the full authorized context
    full_ctx_res = read_context(token_data)
    authorized_ctx = full_ctx_res["context"]
    
    # Filter it semantically
    relevant_ctx = get_relevant_context(authorized_ctx, query)
    
    return {
        "context": relevant_ctx,
        "mode": "semantic",
        "query": query
    }

@app.get("/pcsl/audit")
def get_audit_log(token_data: dict = Depends(get_current_token_data)):
    user_id = token_data["user_id"]
    log_path = os.path.join(os.path.dirname(__file__), "data", "users", f"{user_id}_access_log.json")
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
    token_data: dict = Depends(get_current_token_data)
):
    # Only allow updates if they have the scope.
    user_id = token_data["user_id"]
    if namespace not in token_data["scopes"]:
        raise HTTPException(status_code=403, detail=f"Insufficient scope to update namespace: {namespace}")
    
    ctx = get_context(user_id)
    if namespace not in ctx:
        ctx[namespace] = {}
    
    ctx[namespace][key] = value
    save_context(ctx, user_id)
    return {"status": "success", "updated_namespace": namespace}

@app.post("/pcsl/revoke")
def revoke_access(
    client_id: str = Body(..., embed=True),
    token_data: dict = Depends(get_current_token_data)
):
    user_id = token_data["user_id"]
    revoke_client(user_id, client_id)
    return {"status": "revoked", "client_id": client_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
