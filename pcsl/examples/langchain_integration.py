import os
import sys
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
    """
    # 1. Initialize PCSL Client
    server_url = os.getenv("PCSL_SERVER_URL", "http://localhost:8000")
    pcsl = PCSLClient(server_url=server_url)
    
    # 2. Authorize and fetch context
    # Note: In a real LangChain tool or chain, you'd pass the token or client URL via config
    token = pcsl.authorize(client_id="langchain-demo", scopes=["preferences", "goals"])
    context = pcsl.get_context(token)
    
    # 3. Build LangChain Chat Prompt
    # We can inject the context string directly into the system message template
    system_template = """You are a helpful AI assistant. Use the user's context provided below to personalize your response.
    
    [USER CONTEXT]
    {user_context}
    [END CONTEXT]
    
    Respond in the user's preferred communication style if specified.
    """
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = "{text}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    
    # 4. Initialize LangChain model and run chain
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[!] OPENAI_API_KEY not found. Skipping API call.")
        return

    chat = ChatOpenAI(temperature=0.7, model="gpt-4o")
    
    # Format prompt and call chat model
    query = "Recommend a project for me to work on this weekend."
    chain = chat_prompt | chat
    
    print(f"[*] Querying LangChain model with user query: '{query}'")
    
    response = chain.invoke({
        "user_context": context,
        "text": query
    })
    
    print("\n--- AI RESPONSE ---")
    print(response.content)

if __name__ == "__main__":
    run_langchain_pcsl()
