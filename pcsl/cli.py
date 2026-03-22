# pcsl/cli.py
"""
PCSL CLI - Personal Context Sovereignty Layer Command Line Interface

Entry point for all PCSL commands. Provides:
- pcsl init: Initialize PCSL environment
- pcsl server: Start/stop/status of the PCSL server
- pcsl context: Show/set/get context values
- pcsl token: Create/revoke access tokens
- pcsl audit: View access logs
- pcsl status: Quick server status check
"""

import base64
import json
import os
import signal
import secrets
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print_json

from dotenv import load_dotenv

# Constants
PCSL_HOME = Path.home() / ".pcsl"
SERVER_URL = "http://localhost:8000"
PID_FILE = PCSL_HOME / "server.pid"
LOG_FILE = PCSL_HOME / "server.log"
CONTEXT_FILE = PCSL_HOME / "context.json"
ENV_FILE = PCSL_HOME / ".env"

# Known scopes (for validation warnings)
KNOWN_SCOPES = {"identity", "preferences", "skills", "projects", "goals", "decisions"}

# Create console for rich output
console = Console()

# =============================================================================
# Internal helpers
# =============================================================================

def _ensure_pcsl_home() -> None:
    """Ensure ~/.pcsl/ directory exists."""
    PCSL_HOME.mkdir(parents=True, exist_ok=True)


def _ensure_server_running() -> None:
    """Raise typer.Exit with error message if server not reachable."""
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=2)
        if response.status_code != 200:
            raise typer.Exit("Server returned unexpected status", code=1)
    except requests.ConnectionError:
        rprint(f"[red]Error: PCSL server is not running. Run `pcsl server start` first.[/red]")
        raise typer.Exit(code=1)


def _get_local_token(scopes: list[str]) -> str:
    """Mint a short-lived token for CLI-internal use."""
    _ensure_server_running()
    try:
        response = requests.post(
            f"{SERVER_URL}/pcsl/authorize",
            json={"client_id": "pcsl-cli", "scopes": scopes, "expires_in": 3600},
            timeout=5
        )
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error")
            rprint(f"[red]Error authorizing: {error_detail}[/red]")
            raise typer.Exit(code=1)
        return response.json()["access_token"]
    except requests.ConnectionError:
        rprint(f"[red]Error: Cannot connect to PCSL server at {SERVER_URL}[/red]")
        raise typer.Exit(code=1)


def _load_dotenv_from_pcsl_home() -> None:
    """Load ~/.pcsl/.env into os.environ before any server operation."""
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=True)


def _get_uvicorn_bin() -> Path:
    """Get the path to uvicorn from the current Python interpreter's venv."""
    uvicorn_bin = Path(sys.executable).parent / "uvicorn"
    # On Windows, it might be uvicorn.exe
    if not uvicorn_bin.exists():
        uvicorn_bin = Path(sys.executable).parent / "uvicorn.exe"
    if not uvicorn_bin.exists():
        rprint(f"[red]Error: uvicorn not found at {uvicorn_bin}[/red]")
        rprint("[yellow]Run `pip install -e .` first to install dependencies.[/yellow]")
        raise typer.Exit(code=1)
    return uvicorn_bin


def _decode_token_expiry(token: str) -> Optional[str]:
    """Decode token expiry timestamp without verification."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        exp_ts = payload.get("exp")
        if exp_ts:
            return datetime.fromtimestamp(exp_ts).strftime("%Y-%m-%d %H:%M:%S")
        return None
    except Exception:
        return None


# =============================================================================
# CLI App and Sub-apps
# =============================================================================

app = typer.Typer(
    name="pcsl",
    help="Personal Context Sovereignty Layer - CLI for managing your personal context",
    add_completion=False,
)

server_app = typer.Typer(help="Manage PCSL server (start/stop/status)")
context_app = typer.Typer(help="Manage PCSL context (show/set/get)")
token_app = typer.Typer(help="Manage access tokens (create/revoke)")

app.add_typer(server_app, name="server")
app.add_typer(context_app, name="context")
app.add_typer(token_app, name="token")


# =============================================================================
# Top-level commands: init, audit, status
# =============================================================================

@app.command()
def init():
    """
    Initialize PCSL environment.
    
    Creates ~/.pcsl/ directory with:
    - context.json: Copy of the default context template
    - .env: Generated SECRET_KEY for authentication
    
    Run this once before using any other PCSL commands.
    """
    _ensure_pcsl_home()
    
    # Handle context.json
    if CONTEXT_FILE.exists():
        rprint(f"[yellow]context.json already exists at {CONTEXT_FILE}, skipping.[/yellow]")
    else:
        # Find the template in the repo
        template_path = Path(__file__).parent.parent / "context.json"
        if template_path.exists():
            import shutil
            shutil.copy(template_path, CONTEXT_FILE)
            rprint(f"[green]context.json created at {CONTEXT_FILE}[/green]")
        else:
            rprint(f"[red]Error: Could not find context.json template at {template_path}[/red]")
            raise typer.Exit(code=1)
    
    # Handle .env
    if ENV_FILE.exists():
        rprint(f"[yellow].env already exists at {ENV_FILE}, skipping SECRET_KEY generation.[/yellow]")
    else:
        secret_key = secrets.token_hex(32)
        env_content = f"SECRET_KEY={secret_key}\nPCSL_MODE=local\n"
        ENV_FILE.write_text(env_content)
        rprint(f"[green].env created with SECRET_KEY[/green]")
    
    # Final panel
    panel = Panel(
        f"[bold]Context[/bold] : {CONTEXT_FILE}\n"
        f"[bold]Env[/bold]     : {ENV_FILE}\n\n"
        f"[bold]Next steps:[/bold]\n"
        f"1. Edit ~/.pcsl/context.json with your details\n"
        f"2. Run: pcsl server start\n"
        f"3. Run: pcsl context show",
        title="PCSL Initialized",
        border_style="green",
    )
    rprint(panel)


@app.command()
def audit(
    tail: int = typer.Option(None, "--tail", help="Show only last N entries"),
    client: str = typer.Option(None, "--client", help="Filter by client ID"),
):
    """
    View access audit log.
    
    Shows a table of all clients that have accessed your context,
    including their client_id, requested scopes, and timestamp.
    
    Examples:
      pcsl audit              # Show all entries
      pcsl audit --tail 10    # Show last 10 entries
      pcsl audit --client vscode-plugin  # Filter by client
    """
    _load_dotenv_from_pcsl_home()
    _ensure_server_running()
    token = _get_local_token(["identity"])
    
    try:
        response = requests.get(
            f"{SERVER_URL}/pcsl/audit",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error")
            rprint(f"[red]Error: {error_detail}[/red]")
            raise typer.Exit(code=1)
        
        log = response.json().get("log", [])
        
        # Apply --tail filter
        if tail is not None:
            log = log[-tail:]
        
        # Apply --client filter
        if client is not None:
            log = [e for e in log if e.get("client_id") == client]
        
        if not log:
            rprint("[dim]No access events recorded yet.[/dim]")
            raise typer.Exit(code=0)
        
        table = Table(title="PCSL Access Audit Log", show_lines=True)
        table.add_column("Time", style="dim", width=20)
        table.add_column("Client ID", style="cyan")
        table.add_column("Scopes", style="green")
        
        # Show newest first
        for entry in reversed(log):
            table.add_row(
                entry.get("timestamp", "unknown")[:19],  # trim microseconds
                entry.get("client_id", "unknown"),
                ", ".join(entry.get("scopes", []))
            )
        
        console.print(table)
        rprint(f"\n[dim]Total: {len(log)} events[/dim]")
        
    except requests.ConnectionError:
        rprint(f"[red]Error: Cannot connect to PCSL server at {SERVER_URL}[/red]")
        raise typer.Exit(code=1)


@app.command()
def status():
    """
    Check PCSL server status.
    
    Quick alias for 'pcsl server status' - shows whether the server
    is running and its current version.
    """
    _server_status()


# =============================================================================
# Server subcommands: start, stop, status
# =============================================================================

@server_app.command("start")
def server_start():
    """
    Start the PCSL server.
    
    Spawns uvicorn as a detached subprocess on port 8000.
    Creates a PID file for tracking the server process.
    """
    # Guard: Check ~/.pcsl/.env exists
    if not ENV_FILE.exists():
        rprint(f"[red]Error: {ENV_FILE} not found.[/red]")
        rprint("[yellow]Run `pcsl init` first to initialize PCSL.[/yellow]")
        raise typer.Exit(code=1)
    
    # Guard: Check ~/.pcsl/context.json exists
    if not CONTEXT_FILE.exists():
        rprint(f"[red]Error: {CONTEXT_FILE} not found.[/red]")
        rprint("[yellow]Run `pcsl init` first to initialize PCSL.[/yellow]")
        raise typer.Exit(code=1)
    
    # Guard: Check if server already running
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process is alive (signal 0 just checks existence)
            os.kill(pid, 0)
            rprint(f"[yellow]Server already running (PID {pid}) at http://localhost:8000[/yellow]")
            return
        except (ValueError, ProcessLookupError):
            # PID file stale, remove it
            PID_FILE.unlink()
    
    # Get uvicorn binary path
    uvicorn_bin = _get_uvicorn_bin()
    
    # Start server with logging
    env = os.environ.copy()
    env["DOTENV_PATH"] = str(ENV_FILE)
    
    # Open log file for stderr
    log_handle = open(LOG_FILE, "w")
    
    proc = subprocess.Popen(
        [str(uvicorn_bin), "pcsl.pcsl_server.main:app", 
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=log_handle,
        start_new_session=True,
        env=env,
    )
    
    # Write PID file
    PID_FILE.write_text(str(proc.pid))
    
    # Health check loop (max 5 attempts, 0.8s apart)
    server_started = False
    for attempt in range(5):
        time.sleep(0.8)
        try:
            response = requests.get(f"{SERVER_URL}/", timeout=2)
            if response.status_code == 200:
                server_started = True
                break
        except requests.ConnectionError:
            continue
    
    if not server_started:
        log_handle.close()
        rprint(f"[red]Server failed to start. Check {LOG_FILE} for details.[/red]")
        rprint("[yellow]Port 8000 may be in use by another process.[/yellow]")
        # Clean up PID file on failure
        if PID_FILE.exists():
            PID_FILE.unlink()
        raise typer.Exit(code=1)
    
    log_handle.close()
    
    # Success panel
    panel = Panel(
        f"[bold]URL[/bold]  : http://localhost:8000\n"
        f"[bold]PID[/bold]  : {proc.pid}\n"
        f"[bold]Log[/bold]  : {LOG_FILE}\n\n"
        f"[bold]Docs[/bold] : http://localhost:8000/docs",
        title="PCSL Server Started",
        border_style="green",
    )
    rprint(panel)


@server_app.command("stop")
def server_stop():
    """
    Stop the PCSL server.
    
    Reads the PID file and terminates the server process.
    Waits up to 3s for the process to terminate gracefully.
    """
    if not PID_FILE.exists():
        rprint("[yellow]Server is not running.[/yellow]")
        raise typer.Exit(code=0)
    
    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        rprint("[yellow]PID file corrupted - removing it.[/yellow]")
        PID_FILE.unlink()
        raise typer.Exit(code=0)
    
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        rprint("[yellow]Server process not found (already dead). Cleaning up.[/yellow]")
        PID_FILE.unlink()
        raise typer.Exit(code=0)
    except PermissionError:
        rprint(f"[red]Permission denied to stop PID {pid}[/red]")
        raise typer.Exit(code=1)
    
    # Wait up to 3s for process to die
    for _ in range(6):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)  # still alive?
        except ProcessLookupError:
            break  # dead, good
    else:
        # Process still alive after 3s, try SIGKILL
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    
    # Clean up PID file
    if PID_FILE.exists():
        PID_FILE.unlink()
    
    rprint("[green]Server stopped.[/green]")


@server_app.command("status")
def _server_status():
    """
    Check if PCSL server is running.
    
    Shows server status, version, PID, and URLs.
    """
    # Check PID file
    if not PID_FILE.exists():
        rprint("[yellow]Server not running.[/yellow]")
        raise typer.Exit(code=0)
    
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
    except (ValueError, ProcessLookupError):
        rprint(f"[red]Server crashed (stale PID {pid}). Run `pcsl server start`.[/red]")
        if PID_FILE.exists():
            PID_FILE.unlink()
        raise typer.Exit(code=1)
    
    # Ping server
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=2)
    except requests.ConnectionError:
        rprint(f"[red]Server process alive (PID {pid}) but not responding on port 8000.[/red]")
        raise typer.Exit(code=1)
    
    if response.status_code != 200:
        rprint(f"[red]Server returned status {response.status_code}[/red]")
        raise typer.Exit(code=1)
    
    data = response.json()
    
    # Render table
    table = Table(title="PCSL Server Status", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Status", "online")
    table.add_row("Version", data.get("pcsl", "unknown"))
    table.add_row("PID", str(pid))
    table.add_row("URL", "http://localhost:8000")
    table.add_row("Docs", "http://localhost:8000/docs")
    
    rprint(table)


# =============================================================================
# Context subcommands: show, set, get
# =============================================================================

@context_app.command("show")
def context_show():
    """
    Show local context.json content.
    
    Reads and pretty-prints the local context file.
    Does not require the server to be running.
    """
    if not CONTEXT_FILE.exists():
        rprint(f"[red]Error: Context file not found at {CONTEXT_FILE}[/red]")
        rprint("[yellow]Run 'pcsl init' first to create it.[/yellow]")
        raise typer.Exit(code=1)
    
    with open(CONTEXT_FILE, "r") as f:
        data = json.load(f)
    
    rprint("[bold]Local context:[/bold]")
    print_json(json.dumps(data, indent=2))


@context_app.command("set")
def context_set(
    namespace: str = typer.Argument(..., help="Namespace to update (e.g., identity, skills)"),
    key: str = typer.Argument(..., help="Key to set within the namespace"),
    value: str = typer.Argument(..., help="Value to set (JSON-parseable or raw string)"),
):
    """
    Set a context value locally.
    
    Updates the local context.json file with the given namespace/key/value.
    The value is first attempted to be parsed as JSON (for booleans, numbers, arrays).
    If that fails, it's stored as a raw string.
    
    Example: pcsl context set identity name "John Doe"
    Example: pcsl context set preferences dark_mode true
    """
    if not CONTEXT_FILE.exists():
        rprint(f"[red]Error: Context file not found at {CONTEXT_FILE}[/red]")
        rprint("[yellow]Run 'pcsl init' first to create it.[/yellow]")
        raise typer.Exit(code=1)
    
    # Load existing context
    with open(CONTEXT_FILE, "r") as f:
        ctx = json.load(f)
    
    # Try to parse value as JSON first
    parsed_value = value
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        # Keep as string if not valid JSON
        pass
    
    # Auto-create namespace if missing
    if namespace not in ctx:
        ctx[namespace] = {}
    
    ctx[namespace][key] = parsed_value
    
    # Save back
    with open(CONTEXT_FILE, "w") as f:
        json.dump(ctx, f, indent=2)
    
    rprint(f"[green]Updated {namespace}.{key} = {parsed_value}[/green]")


@context_app.command("get")
def context_get(
    namespace: str = typer.Argument(..., help="Namespace to retrieve (e.g., identity, skills)"),
):
    """
    Get context from server with filtering.
    
    Mints a token with the requested scope and fetches filtered
    context from the server. Requires the server to be running.
    
    Example: pcsl context get identity
    """
    _load_dotenv_from_pcsl_home()
    token = _get_local_token([namespace])
    
    try:
        response = requests.get(
            f"{SERVER_URL}/pcsl/context",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error")
            rprint(f"[red]Error: {error_detail}[/red]")
            raise typer.Exit(code=1)
        
        data = response.json()
        rprint(f"[bold]Context for scope '{namespace}':[/bold]")
        print_json(json.dumps(data.get("context", {}), indent=2))
        
    except requests.ConnectionError:
        rprint(f"[red]Error: Cannot connect to PCSL server at {SERVER_URL}[/red]")
        raise typer.Exit(code=1)


# =============================================================================
# Token subcommands: create, revoke
# =============================================================================

@token_app.command("create")
def token_create(
    client_id: str = typer.Argument(..., help="Client identifier (e.g., claude-desktop, my-app)"),
    scopes: str = typer.Argument(..., help="Comma-separated scopes (e.g., identity,skills)"),
    expires: int = typer.Option(3600, "--expires", help="Token expiry in seconds (default: 3600)"),
):
    """
    Create an access token for a client.
    
    Requests a new token from the server with the specified scopes.
    The token is printed in a panel for easy copying, and the raw token
    is printed separately for piping.
    
    Examples:
      pcsl token create my-claude-extension identity,skills
      pcsl token create vscode-plugin preferences
      pcsl token create langchain-app identity,skills,goals --expires 86400
    """
    _load_dotenv_from_pcsl_home()
    _ensure_server_running()
    
    # Parse scopes
    scope_list = [s.strip() for s in scopes.split(",")]
    
    # Validate scopes (warn but don't block)
    unknown = set(scope_list) - KNOWN_SCOPES
    if unknown:
        rprint(f"[yellow]Warning: unknown scopes: {', '.join(unknown)}. Proceeding anyway.[/yellow]")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/pcsl/authorize",
            json={"client_id": client_id, "scopes": scope_list, "expires_in": expires},
            timeout=5
        )
        if response.status_code == 403:
            rprint(f"[red]Client '{client_id}' has been revoked.[/red]")
            raise typer.Exit(code=1)
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error")
            rprint(f"[red]Error: {error_detail}[/red]")
            raise typer.Exit(code=1)
        
        token_data = response.json()
        access_token = token_data["access_token"]
        
        # Decode expiry for display
        exp_str = _decode_token_expiry(access_token) or "unknown"
        
        panel = Panel(
            f"[bold]Client ID[/bold]: {client_id}\n"
            f"[bold]Scopes[/bold]  : {', '.join(scope_list)}\n"
            f"[bold]Expires[/bold]  : {exp_str}\n\n"
            f"[bold]Usage:[/bold]\n"
            f"Authorization: Bearer <token>",
            title="Token Created",
            border_style="green",
        )
        rprint(panel)
        
        # Print raw token separately for piping
        print(access_token)
        
    except requests.ConnectionError:
        rprint(f"[red]Error: Cannot connect to PCSL server at {SERVER_URL}[/red]")
        raise typer.Exit(code=1)


@token_app.command("revoke")
def token_revoke(
    client_id: str = typer.Argument(..., help="Client identifier to revoke"),
):
    """
    Revoke access for a client.
    
    Revokes all tokens for the specified client_id. Any existing tokens
    for this client will be immediately rejected.
    
    Example: pcsl token revoke claude-desktop
    """
    _load_dotenv_from_pcsl_home()
    _ensure_server_running()
    
    # Confirmation prompt
    confirmed = typer.confirm(f"Revoke all access for '{client_id}'?")
    if not confirmed:
        rprint("[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=0)
    
    # Mint internal token for authentication
    token = _get_local_token(["identity"])
    
    try:
        response = requests.post(
            f"{SERVER_URL}/pcsl/revoke",
            headers={"Authorization": f"Bearer {token}"},
            json={"client_id": client_id},
            timeout=5
        )
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error")
            rprint(f"[red]Error: {error_detail}[/red]")
            raise typer.Exit(code=1)
        
        rprint(f"[green]Revoked[/green] — '{client_id}' can no longer access your context.")
        rprint("[dim]Any existing tokens for this client will be rejected.[/dim]")
        
    except requests.ConnectionError:
        rprint(f"[red]Error: Cannot connect to PCSL server at {SERVER_URL}[/red]")
        raise typer.Exit(code=1)


# =============================================================================
# Main entry point
# =============================================================================

if __name__ == "__main__":
    app()
