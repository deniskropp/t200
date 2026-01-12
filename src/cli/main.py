import typer
import asyncio
from typing import Optional
from rich.console import Console
from rich.table import Table
from src.shared.constants import SYSTEM_NAME, SYSTEM_VERSION, SYSTEM_MODE
from src.shared.models import AgentRole

app = typer.Typer(help=SYSTEM_NAME)
console = Console()

@app.command()
def info():
    """Display system information."""
    console.print(f"[bold blue]{SYSTEM_NAME}[/bold blue]")
    console.print(f"Version: [green]{SYSTEM_VERSION}[/green]")
    console.print(f"Mode: [yellow]{SYSTEM_MODE}[/yellow]")

@app.command()
def init():
    """Initialize the OCS environment."""
    console.print("[bold green]Initializing Orion Collective System...[/bold green]")
    # TODO: Add initialization logic here (e.g. database setup)
    console.print("✓ Environment ready.")

@app.command()
def list_agents():
    """List available agent roles."""
    table = Table(title="Available Agents")
    table.add_column("Role", style="cyan")
    table.add_column("Description", style="white")

    for role in AgentRole:
        table.add_row(role.value, f"Agent role for {role.name}")
    
    console.print(table)

@app.command()
def run_agent(role: AgentRole):
    """Start an agent loop (placeholder)."""
    console.print(f"[bold]Starting agent:[/bold] {role.value}")
    # Placeholder for running the async agent loop
    # asyncio.run(agent.run())
    console.print("[red]Not implemented yet.[/red]")

if __name__ == "__main__":
    app()
