# PCSL Integration Example (using opencontext SDK)
import json
from opencontext import PCSLClient

# 1. Initialize the client for a specific user's PCSL server
USER_SERVER_URL = "http://localhost:8000"
client = PCSLClient(server_url=USER_SERVER_URL)

# 2. Authorize the application for specific namespaces
# In production, the user would approve this request
CLIENT_ID = "example-ai-app"
SCOPES = ["identity", "preferences", "skills"]
token = client.authorize(client_id=CLIENT_ID, scopes=SCOPES)

# 3. Fetch the personal context
context = client.get_context(token)

# 4. Inject into a system prompt for an LLM
base_prompt = "Help the user write a professional bio."
system_prompt = client.inject_into_prompt(token, base_prompt)

print("--- System Prompt with Context ---")
print(system_prompt)

# Example output structure:
# [USER CONTEXT]
# {
#   "identity": { "name": "Karan Singh", ... },
#   "preferences": { ... },
#   "skills": { ... }
# }
# [END CONTEXT]
#
# Help the user write a professional bio.
