import requests
import time

SERVER_URL = "http://localhost:8000"

def test_flow():
    print(f"[*] Testing server at {SERVER_URL}...")
    
    # 1. Authorize
    auth_data = {
        "client_id": "test-client",
        "scopes": ["identity", "preferences"],
        "expires_in": 3600
    }
    resp = requests.post(f"{SERVER_URL}/pcsl/authorize", json=auth_data)
    if resp.status_code != 200:
        print(f"[-] Authorization failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    print("[+] Received token.")
    
    # 2. Get Context
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{SERVER_URL}/pcsl/context", headers=headers)
    if resp.status_code != 200:
        print(f"[-] Get Context failed: {resp.text}")
        return
    
    context = resp.json()["context"]
    print("[+] Received context.")
    print(f"    - Name: {context.get('identity', {}).get('name')}")
    print(f"    - Prefs: {context.get('preferences')}")
    
    # Check that 'skills' is NOT there (we didn't ask for that scope)
    if "skills" in context:
        print("[-] FAILED: Context scoper leaked 'skills' namespace!")
    else:
        print("[+] SUCCESS: Context correctly scoped.")

if __name__ == "__main__":
    test_flow()
