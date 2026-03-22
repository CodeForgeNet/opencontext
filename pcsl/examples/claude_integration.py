import os
import sys
import json
import anthropic
from dotenv import load_dotenv

from pcsl_sdk.client import PCSLClient

load_dotenv()

def run_personalized_claude():
    """
    Example of integrating PCSL into an Anthropic Claude message.
    """
    # 1. Initialize PCSL Client
    server_url = os.getenv("PCSL_SERVER_URL", "http://localhost:8000")
    pcsl = PCSLClient(server_url=server_url)
    
    # 2. Authorize and fetch context
    client_id = "claude-ai-assistant"
    scopes = ["identity", "preferences", "skills"]
    
    print(f"[*] Authorizing with PCSL server at {server_url}...")
    token = pcsl.authorize(client_id=client_id, scopes=scopes)
    
    # 3. Fetch context and prepare system prompt
    # Note: Anthropic uses a top-level 'system' parameter
    context = pcsl.get_context(token)
    ctx_str = json.dumps(context, indent=2)
    
    base_instructions = "You are a helpful AI assistant. Use the user's personal context to provide tailored responses."
    system_prompt = f"{base_instructions}\n\n[USER CONTEXT]\n{ctx_str}\n[END CONTEXT]"
    
    print("[*] Injected System Prompt Prepared for Claude.")
    
    # 4. Use with Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[!] ANTHROPIC_API_KEY not found. Skipping API call.")
        print(f"--- SYSTEM PROMPT ---\n{system_prompt}\n--- END ---")
        return

    client = anthropic.Anthropic(api_key=api_key)
    
    user_query = "What technical skills should I highlight in my portfolio?"
    
    print(f"[*] Querying Claude with user message: '{user_query}'")
    
    response = client.messages.create(
        model="claude-3.5-sonnet-20241022",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_query}
        ]
    )
    
    print("\n--- CLAUDE RESPONSE ---")
    print(response.content[0].text)

if __name__ == "__main__":
    run_personalized_claude()
