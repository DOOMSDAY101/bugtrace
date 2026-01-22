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


# # @app.command()
# # def init():
# #     """
# #     Initialize Bugtrace configuration for this project.
# #     """
# #     from bugtrace.config.settings import create_default_config

# #     create_default_config()
# #     typer.echo("✅ bugtrace.yaml created! Edit it to customize settings.")


# # Generate ASCII art for BUGTRACE
# f = Figlet(font="big")  # you can try "standard", "slant", "banner", etc.
# BUGTRACE_LOGO = f.renderText("BUGTRACE")

# @app.callback(invoke_without_command=True)
# def main():
#     """
#     Bugtrace CLI
#     """
#     panel = Panel(
#         Align.center(BUGTRACE_LOGO),
#         border_style="bold green",
#         padding=(1, 4),
#         title="[bold green]Bugtrace[/bold green]",
#         subtitle="[cyan]AI-Powered Debugging[/cyan]",
#     )
#     console.print(panel)
#     console.print("[bold cyan]Welcome to Bugtrace![/bold cyan]")
#     console.print("Type `bugtrace --help` to see available commands.\n")

# @app.command()
# def init():
#     """
#     Initialize Bugtrace configuration for this project.
#     """
#     # For now, just pretend we created config
#     console.print("[bold green]✅ bugtrace.yaml created![/bold green]")
#     console.print("Edit it to customize settings.\n")
# if __name__ == "__main__":
#     app()


# bugtrace/cli/main.py
import os
from pathlib import Path
from rich.console import Console
import typer
from rich.panel import Panel
from rich.align import Align
from pyfiglet import Figlet
from rich.text import Text
from rich import box  # Add this import

console = Console() 

app = typer.Typer(help="Bugtrace - AI-powered debugging assistant")

def create_designer_logo():
    """
    Create a thick, designer-style BUGTRACE logo
    """
    # Try different fonts for thicker appearance
    f = Figlet(font="colossal")  # Very thick and bold
    logo_text = f.renderText("BUGTRACE")
    
    # Create gradient effect with Rich
    logo = Text()
    lines = logo_text.split('\n')
    
    # Gradient colors from cyan to green to yellow
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
        if line.strip():  # Only color non-empty lines
            color = colors[i % len(colors)]
            text.append(line + "\n", style=f"bold {color}")
        else:
            text.append(line + "\n")
    
    return text

@app.callback(invoke_without_command=True)
def main():
    """
    Bugtrace CLI
    """
    # Choose your logo style:
    
    # Option 1: Gradient designer logo (thicker font)
    # logo = create_designer_logo()
    
    # Option 2: Ultra thick block letters (RECOMMENDED - THICKEST)
    logo = create_block_logo()
    
    panel = Panel(
        Align.center(logo),
        border_style="bold bright_green",
        padding=(1, 4),
        title="[bold bright_yellow]⚡ BUGTRACE ⚡[/bold bright_yellow]",
        subtitle="[bold bright_cyan]AI-Powered Debugging Assistant[/bold bright_cyan]",
        box=box.HEAVY  # Changed from None to box.HEAVY for thick borders
    )
    
    console.print("\n")
    console.print(panel)
    console.print("\n")
    console.print("[bold bright_cyan]👋 Welcome to Bugtrace![/bold bright_cyan]")
    console.print("[dim]Type [bold]bugtrace --help[/bold] to see available commands.[/dim]\n")

@app.command()
def init():
    """
    Initialize Bugtrace configuration for this project.
    """
    console.print("[bold green]✅ bugtrace.yaml created![/bold green]")
    console.print("Edit it to customize settings.\n")

if __name__ == "__main__":
    app()