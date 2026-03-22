import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Add the SDK to the path for development/examples
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pcsl-sdk-python")))
from pcsl_sdk.client import PCSLClient

load_dotenv()

def run_personalized_ai():
    """
    Simple example of integrating PCSL into a standard OpenAI chat completion.
    """
    # 1. Initialize PCSL Client (pointing to your local or hosted PCSL server)
    server_url = os.getenv("PCSL_SERVER_URL", "http://localhost:8000")
    pcsl = PCSLClient(server_url=server_url)
    
    # 2. Authorize and get a token for specific scopes
    # In a real app, you might already have this token stored
    client_id = "generic-ai-assistant"
    scopes = ["identity", "preferences", "skills"]
    
    print(f"[*] Authorizing with PCSL server at {server_url}...")
    token = pcsl.authorize(client_id=client_id, scopes=scopes)
    
    # 3. Fetch context and inject into the prompt
    base_prompt = "You are a helpful AI assistant. Answer the user's question based on their context if provided."
    injected_prompt = pcsl.inject_into_prompt(token, base_prompt)
    
    print("[*] Injected System Prompt Prepared.")
    
    # 4. Use with OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[!] OPENAI_API_KEY not found. Skipping API call.")
        print(f"--- SYSTEM PROMPT ---\n{injected_prompt}\n--- END ---")
        return

    client = OpenAI(api_key=api_key)
    
    user_query = "What should I focus on for my career growth?"
    
    print(f"[*] Querying OpenAI with user message: '{user_query}'")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": injected_prompt},
            {"role": "user", "content": user_query}
        ]
    )
    
    print("\n--- AI RESPONSE ---")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    run_personalized_ai()
