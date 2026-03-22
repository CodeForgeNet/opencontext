import os
import json
import logging
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pcsl-mcp")

# Initialize FastMCP server
mcp = FastMCP("pcsl")

# Path to the user data directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "pcsl_server", "data", "users"))

def get_user_file(user_id: str) -> str:
    return os.path.join(DATA_DIR, f"{user_id}.json")

def load_user_context(user_id: str) -> Dict[str, Any]:
    file_path = get_user_file(user_id)
    if not os.path.exists(file_path):
        # Fallback for demo/migration
        root_ctx = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "context.json"))
        if os.path.exists(root_ctx):
            with open(root_ctx, "r") as f:
                return json.load(f)
        return {}
    with open(file_path, "r") as f:
        return json.load(f)

def save_user_context(user_id: str, context: Dict[str, Any]):
    file_path = get_user_file(user_id)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    from datetime import datetime
    context["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(file_path, "w") as f:
        json.dump(context, f, indent=2)

# --- Resources ---

@mcp.resource("pcsl://{user_id}/all")
def get_full_context(user_id: str) -> str:
    """Fetch the entire personal context for a user."""
    ctx = load_user_context(user_id)
    return json.dumps(ctx, indent=2)

@mcp.resource("pcsl://{user_id}/{namespace}")
def get_namespace_context(user_id: str, namespace: str) -> str:
    """Fetch a specific namespace (e.g., identity, preferences, skills) from the user's context."""
    ctx = load_user_context(user_id)
    namespace_data = ctx.get(namespace, {})
    return json.dumps(namespace_data, indent=2)

# --- Tools ---

@mcp.tool()
def update_context_item(
    namespace: str,
    key: str,
    value: Any,
    user_id: str = "local-user"
) -> str:
    """
    Update or add a specific item in the user's personal context.
    
    Args:
        namespace: The category (e.g., 'preferences', 'skills', 'goals').
        key: The specific field to update.
        value: The new value (can be string, list, or object).
        user_id: The ID of the user (defaults to 'local-user').
    """
    try:
        ctx = load_user_context(user_id)
        if namespace not in ctx:
            ctx[namespace] = {}
        
        ctx[namespace][key] = value
        save_user_context(user_id, ctx)
        return f"Successfully updated {namespace}.{key} for {user_id}."
    except Exception as e:
        return f"Error updating context: {str(e)}"

@mcp.tool()
def add_decision(
    context: str,
    reasoning: str,
    user_id: str = "local-user"
) -> str:
    """
    Record a new architectural or project decision in the user's context.
    
    Args:
        context: What was the situation or problem?
        reasoning: Why was this specific choice made?
        user_id: The ID of the user (defaults to 'local-user').
    """
    try:
        ctx = load_user_context(user_id)
        if "decisions" not in ctx or not isinstance(ctx["decisions"], list):
            ctx["decisions"] = []
        
        from datetime import datetime
        ctx["decisions"].append({
            "date": datetime.now().strftime("%Y-%m"),
            "context": context,
            "reasoning": reasoning
        })
        save_user_context(user_id, ctx)
        return f"Decision recorded in {user_id}'s context."
    except Exception as e:
        return f"Error recording decision: {str(e)}"

if __name__ == "__main__":
    mcp.run()
