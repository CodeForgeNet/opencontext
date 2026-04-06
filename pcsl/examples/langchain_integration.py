import os
import sys
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# Add the SDK to the path for development/examples
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pcsl-sdk-python")))
from pcsl_sdk.client import PCSLClient

load_dotenv()

def run_langchain_pcsl():
    """
    Example of integrating PCSL context into a LangChain system prompt.
    Demonstrates scope filtering and context injection with proper error handling.
    """
    try:
        # 1. Initialize PCSL Client
        server_url = os.getenv("PCSL_SERVER_URL", "http://localhost:8000")
        print(f"[*] Connecting to PCSL server at {server_url}")
        pcsl = PCSLClient(server_url=server_url)

        # 2. Authorize with proper scopes
        # Scopes: identity, preferences, skills
        print("[*] Requesting authorization with scopes: ['identity', 'preferences', 'skills']")
        token = pcsl.authorize(
            client_id="langchain-demo",
            scopes=["identity", "preferences", "skills"]
        )
        print("[+] Authorization successful")

        # 3. Fetch context
        print("[*] Fetching user context...")
        context = pcsl.get_context(token)
        print("[+] Context retrieved successfully")
        print(f"[DEBUG] Context keys: {list(context.keys())}")

        # 4. Build LangChain Chat Prompt with context
        system_template = """You are a helpful AI assistant. Use the user's context provided below to personalize your response.

[USER CONTEXT]
{user_context}
[END CONTEXT]

Respond in the user's preferred communication style if specified."""

        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = "{text}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])

        # 5. Initialize LangChain model and run chain
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[!] OPENAI_API_KEY not found. Skipping API call.")
            print("[*] But PCSL integration worked! Context would be injected into prompts.")
            return

        print("[*] Initializing ChatOpenAI...")
        chat = ChatOpenAI(temperature=0.7, model="gpt-4o")

        # Format context as readable string
        context_str = json.dumps(context, indent=2)

        # Format prompt and call chat model
        query = "Recommend a project for me to work on this weekend."
        chain = chat_prompt | chat

        print(f"[*] Querying LangChain model with user query: '{query}'")

        response = chain.invoke({
            "user_context": context_str,
            "text": query
        })

        print("\n--- AI RESPONSE ---")
        print(response.content)

    except ConnectionError as e:
        print(f"[ERROR] Failed to connect to PCSL server: {e}")
        print("[*] Ensure PCSL server is running at the configured URL")
        return
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    run_langchain_pcsl()
