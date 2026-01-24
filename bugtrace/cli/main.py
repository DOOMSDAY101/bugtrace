# # bugtrace/cli/main.py
# import os
# from pathlib import Path
# from rich.console import Console
# import typer
# from rich.panel import Panel
# from rich.align import Align
# from pyfiglet import Figlet

# console = Console() 

# # from bugtrace.config.settings import load_settings
# # from bugtrace.agent.debugger_agent import DebuggerAgent

# app = typer.Typer(help="Bugtrace - AI-powered debugging assistant")

# # @app.command()
# # def analyze(
# #     bug_description: str = typer.Argument(..., help="Brief description of the bug"),
# #     path: str = typer.Option(".", "--path", "-p", help="Project root path"),
# #     logs: str = typer.Option("", "--logs", "-l", help="Optional log directory"),
# # ):
# #     """
# #     Analyze a bug in your project.
# #     """
# #     # Resolve paths
# #     project_path = Path(path).resolve()
# #     log_path = Path(logs).resolve() if logs else None

# #     # Load configuration (YAML + .env)
# #     settings = load_settings()

# #     # Override project/log paths if user provided
# #     settings.paths.project_root = str(project_path)
# #     if log_path:
# #         settings.paths.logs = [str(log_path)]

# #     # Optional: get API key from environment if not in config
# #     if not settings.llm.api_key:
# #         settings.llm.api_key = os.getenv("BUGTRACE_OPENAI_API_KEY")
# #         if not settings.llm.api_key:
# #             typer.echo("❌ No API key found. Set it in .env or config.", err=True)
# #             raise typer.Exit(code=1)

# #     # Initialize the agent
# #     agent = DebuggerAgent(settings)

# #     # Run the analysis
# #     typer.echo("🔍 Running Bugtrace...")
# #     report = agent.run(project_path, bug_description)

# #     # Print the report
# #     typer.echo("\n📊 Bugtrace Report")
# #     typer.echo("-------------------")
# #     typer.echo(report)


import os
from pathlib import Path
from rich.console import Console
import typer
from rich.panel import Panel
from rich.align import Align
from pyfiglet import Figlet
from rich.text import Text
from rich import box
from bugtrace.utils.fs import ensure_state_dir
from bugtrace.config.settings import create_default_config
from bugtrace.analyze.core import analyze




console = Console() 

app = typer.Typer(help="Bugtrace - AI-powered debugging assistant")

def create_designer_logo():
    """
    Create a thick, designer-style BUGTRACE logo
    """
    f = Figlet(font="colossal")  
    logo_text = f.renderText("BUGTRACE")
    
    logo = Text()
    lines = logo_text.split('\n')
    
    colors = ["cyan", "bright_cyan", "green", "bright_green", "yellow"]
    
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        logo.append(line + "\n", style=f"bold {color}")
    
    return logo

def create_block_logo():
    """
    Create custom thick block letters using Unicode
    """
    logo = """
██████╗ ██╗   ██╗ ██████╗ ████████╗██████╗  █████╗  ██████╗███████╗
██╔══██╗██║   ██║██╔════╝ ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
██████╔╝██║   ██║██║  ███╗   ██║   ██████╔╝███████║██║     █████╗  
██╔══██╗██║   ██║██║   ██║   ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
██████╔╝╚██████╔╝╚██████╔╝   ██║   ██║  ██║██║  ██║╚██████╗███████╗
╚═════╝  ╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
    """
    
    text = Text()
    lines = logo.split('\n')
    colors = ["bright_cyan", "cyan", "bright_green", "green", "bright_yellow", "yellow"]
    
    for i, line in enumerate(lines):
        if line.strip():  
            color = colors[i % len(colors)]
            text.append(line + "\n", style=f"bold {color}")
        else:
            text.append(line + "\n")
    
    return text

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Bugtrace CLI
    """
 
    # Show logo ONLY if:
    # - no subcommand (bugtrace)
    # - help is requested
    # - init command is used
    show_logo = (
        ctx.invoked_subcommand is None
        or ctx.invoked_subcommand == "init"
        or ctx.resilient_parsing  # this is True during --help
    )

    if not show_logo:
        return

    logo = create_block_logo()
    
    panel = Panel(
        Align.center(logo),
        border_style="bold bright_green",
        padding=(1, 4),
        title="[bold bright_yellow]⚡ BUGTRACE ⚡[/bold bright_yellow]",
        subtitle="[bold bright_cyan]AI-Powered Debugging Assistant[/bold bright_cyan]",
        box=box.HEAVY  
    )
    
    console.print("\n")
    console.print(panel)
    console.print("\n")
    console.print("[bold bright_cyan]👋 Welcome to Bugtrace![/bold bright_cyan]")
    console.print("[dim]Type [bold]bugtrace --help[/bold] to see available commands.[/dim]\n")

@app.command()
def init(
     path: Path = typer.Option(
        None,
        "--path",
        help="Path to the project root (defaults to current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
     llm: str = typer.Option(
        "ollama",
        "--llm",
        help="LLM provider to use (ollama, openai, etc.)",
    ),
    model: str = typer.Option(
        "llama3.2:3b",
        "--model",
        help="Model name to initialize with",
    ),
):
    """
    Initialize Bugtrace configuration for this project.
    """
    project_root = path or Path.cwd()

     # Check if already initialized
    if (project_root / ".bugtrace").exists():
        console.print(
            "[yellow]⚠ Bugtrace already initialized in this directory.[/yellow]"
        )
        return


    # 1. Create .bugtrace/
    state_dir = ensure_state_dir(project_root)

     # 2. Create bugtrace.yaml
    created = create_default_config(
        project_root=project_root,
        llm_provider=llm,
        model=model,
    )

    console.print("[bold green]✅ bugtrace.yaml created![/bold green]")
    console.print(f"[dim]Project root:[/dim] {project_root}")
    console.print(f"[dim]State directory:[/dim] {state_dir}")
    console.print("Edit it to customize settings.\n")
    if created:
        console.print("[dim]Created bugtrace.yaml[/dim]")
    else:
        console.print("[yellow]bugtrace.yaml already exists — skipped[/yellow]")

@app.command()
def scan(
    path: Path = typer.Option(
        None,
        "--path",
        help="Path to project root (defaults to current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    )
):
    """Scan project files and update manifest."""
    project_root = path or Path.cwd()
    analyze(project_root)

def run():
    app()