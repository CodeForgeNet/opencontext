import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv

# Add the SDK to the path for development/examples
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pcsl-sdk-python")))
from pcsl_sdk.client import PCSLClient

load_dotenv()

def run_assistant_pcsl():
    """
    Example of integrating PCSL context into an OpenAI Assistant thread.
    """
    # 1. Initialize PCSL Client
    server_url = os.getenv("PCSL_SERVER_URL", "http://localhost:8000")
    pcsl = PCSLClient(server_url=server_url)
    
    # 2. Authorize and fetch context
    token = pcsl.authorize(client_id="openai-assistant-demo", scopes=["preferences", "projects"])
    context = pcsl.get_context(token)
    
    # 3. Use with OpenAI Assistant
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[!] OPENAI_API_KEY not found. Skipping API call.")
        return

    client = OpenAI(api_key=api_key)
    
    # Create an assistant if you don't have one
    assistant = client.beta.assistants.create(
        name="PCSL Personal Assistant",
        instructions=f"You are a personal assistant. Use the user's context provided below to personalize your help.\n\n[USER CONTEXT]\n{json.dumps(context, indent=2)}\n[END CONTEXT]",
        model="gpt-4o"
    )
    
    # Create a thread for the session
    thread = client.beta.threads.create()
    
    # Add a message to the thread
    user_query = "What should I focus on for my career growth?"
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_query
    )
    
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    
    print(f"[*] Querying OpenAI Assistant with user query: '{user_query}'")
    
    # In a real app, you'd poll the run status
    import time
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(1)
        print(f"[*] Run status: {run.status}")

    # Retrieve and print messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    print("\n--- AI RESPONSE ---")
    for msg in messages.data:
        if msg.role == "assistant":
            for content_part in msg.content:
                if content_part.type == "text":
                    print(content_part.text.value)

if __name__ == "__main__":
    run_assistant_pcsl()
