import requests
import json
import time
import sys
import os

from pcsl_sdk.client import PCSLClient

SERVER_URL = "http://localhost:8001"

def test_phase3_features():
    print("[*] Waiting for server to start...")
    time.sleep(2)
    
    # 1. Test Discovery Endpoint
    print("[*] Testing Discovery Endpoint...")
    resp = requests.get(f"{SERVER_URL}/.well-known/pcsl.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert "smart_context_endpoint" in spec
    print("[OK] Discovery endpoint contains smart_context_endpoint")

    # 2. Test Python SDK Implementation
    print("[*] Testing Python SDK...")
    client = PCSLClient(server_url=SERVER_URL)
    token = client.authorize(client_id="test-sdk", scopes=["identity", "skills", "preferences"])
    assert token is not None
    print("[OK] SDK Authorize successful")

    # 3. Test Smart Context Retrieval (Semantic Chunking)
    print("[*] Testing Smart Context Retrieval...")
    # Using the SDK method via custom requests for now to test the server endpoint directly
    headers = {"Authorization": f"Bearer {token}"}
    query = "What are Karan's technical skills?"
    resp = requests.get(f"{SERVER_URL}/pcsl/context/smart", params={"query": query}, headers=headers)
    assert resp.status_code == 200
    smart_ctx = resp.json()
    assert "context" in smart_ctx
    assert smart_ctx["mode"] == "semantic"
    
    # Check if we got relevant skills (Karan's context has Python, FastAPI, etc.)
    ctx_data = smart_ctx["context"]
    assert "skills" in ctx_data
    print(f"[OK] Smart context returned relevant namespaces: {list(ctx_data.keys())}")

    # 4. Test SDK Prompt Injection
    print("[*] Testing SDK Prompt Injection...")
    base_prompt = "Tell me about this user."
    injected = client.inject_into_prompt(token, base_prompt)
    assert "[USER CONTEXT]" in injected
    assert "skills" in injected
    assert base_prompt in injected
    print("[OK] SDK Prompt injection successful")

if __name__ == "__main__":
    try:
        test_phase3_features()
        print("\n[SUCCESS] All Phase 3 features verified!")
    except Exception as e:
        print(f"\n[FAILURE] Phase 3 verification failed: {e}")
        sys.exit(1)
