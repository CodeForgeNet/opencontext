import json
import requests
from typing import List, Optional, Any

_DEFAULT_TIMEOUT = 10  # seconds


class PCSLClient:
    """
    OpenContext (PCSL) SDK for AI application developers.
    Usage:
        client = PCSLClient(server_url="http://localhost:8000")
        token = client.authorize(client_id="my-app", scopes=["preferences", "skills"])
        context = client.get_context(token)
    """

    def __init__(self, server_url: str, timeout: int = _DEFAULT_TIMEOUT):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.spec = self._verify_pcsl()

    def _verify_pcsl(self) -> dict:
        try:
            r = requests.get(
                f"{self.server_url}/.well-known/pcsl.json", timeout=self.timeout
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise ConnectionError(f"No valid PCSL server found at {self.server_url}: {e}")

    def authorize(self, client_id: str, scopes: List[str], expires_in: int = 3600) -> str:
        """Request a scoped JWT token from the PCSL server."""
        r = requests.post(
            f"{self.server_url}/pcsl/authorize",
            json={"client_id": client_id, "scopes": scopes, "expires_in": expires_in},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()["access_token"]

    def get_context(self, token: str) -> dict:
        """Fetch the authorized personal context using the JWT token."""
        r = requests.get(
            f"{self.server_url}/pcsl/context",
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()["context"]

    def inject_into_prompt(self, token: str, base_prompt: str) -> str:
        """Fetch context and prepend it to a base system prompt."""
        context = self.get_context(token)
        ctx_str = json.dumps(context, indent=2)
        return f"<pcsl_context>\n{ctx_str}\n</pcsl_context>\n\n{base_prompt}"

    def suggest_update(self, token: str, namespace: str, key: str, value: Any) -> dict:
        """Suggest an update to the user's context. Requires write scopes."""
        r = requests.post(
            f"{self.server_url}/pcsl/update",
            headers={"Authorization": f"Bearer {token}"},
            json={"namespace": namespace, "key": key, "value": value},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def get_audit_log(self, token: str) -> List[dict]:
        """Fetch the access audit log for the current user."""
        r = requests.get(
            f"{self.server_url}/pcsl/audit",
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json().get("log", [])
