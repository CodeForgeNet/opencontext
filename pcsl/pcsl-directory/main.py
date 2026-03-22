import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="PCSL Directory", version="1.0")
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")

class Registration(BaseModel):
    user_handle: str   # public username
    server_url: str    # their PCSL server
    public_scopes: List[str] # what they allow by default

def load_registry():
    if not os.path.exists(REGISTRY_PATH) or os.path.getsize(REGISTRY_PATH) == 0:
        return {}
    with open(REGISTRY_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_registry(data):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=2)

@app.get("/")
def read_root():
    return {"message": "PCSL Directory API. Use /register or /lookup/{handle}"}

@app.post("/register")
def register(reg: Registration):
    data = load_registry()
    data[reg.user_handle] = reg.dict()
    save_registry(data)
    return {"status": "registered", "handle": reg.user_handle}

@app.get("/lookup/{handle}")
def lookup(handle: str):
    data = load_registry()
    if handle not in data:
        raise HTTPException(status_code=404, detail="User handle not found in registry")
    return data[handle]

@app.get("/all")
def get_all():
    """Return all registered users (discovery)."""
    return load_registry()
