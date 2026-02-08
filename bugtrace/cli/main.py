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
import shutil





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
def clean(
    path: Path = typer.Option(
        None,
        "--path",
        help="Path to the project root (defaults to current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
):
    """
    Remove all Bugtrace files from this project.
    """
    project_root = path or Path.cwd()

    bugtrace_dir = project_root / ".bugtrace"
    bugtrace_yaml = project_root / "bugtrace.yaml"

    removed_anything = False

    # Remove .bugtrace directory
    if bugtrace_dir.exists():
        shutil.rmtree(bugtrace_dir)
        console.print("[green]🗑 Removed .bugtrace directory[/green]")
        removed_anything = True
    else:
        console.print("[dim].bugtrace directory not found[/dim]")

    # Remove bugtrace.yaml
    if bugtrace_yaml.exists():
        bugtrace_yaml.unlink()
        console.print("[green]🗑 Removed bugtrace.yaml[/green]")
        removed_anything = True
    else:
        console.print("[dim]bugtrace.yaml not found[/dim]")

    if not removed_anything:
        console.print(
            "[yellow]⚠ No Bugtrace files found in this directory.[/yellow]"
        )
    else:
        console.print(
            f"\n[bold green]✅ Bugtrace cleaned from:[/bold green] {project_root}"
        )

        
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
    from bugtrace.analyze.core import scan_project
    project_root = path or Path.cwd()
    scan_project(project_root)

@app.command()
def index(
    path: str = typer.Option(".", "--path", "-p", help="Project root path"),
    force: bool = typer.Option(False, "--force", "-f", help="Force full re-index"),
):
    """
    Build RAG embeddings from tracked files.
    Intelligently indexes only new/changed files unless --force is used.
    """
    from bugtrace.rag.indexer import index_project
    
    project_root = Path(path).resolve()
    
    try:
        index_project(project_root, force=force)
    except Exception as e:
        console.print(f"\n[bold red]❌ Indexing failed:[/bold red] {e}")
        raise typer.Exit(code=1)
    

@app.command()
def status(
    path: str = typer.Option(".", "--path", "-p", help="Project root path"),
):
    """
    Show current project indexing status.
    Checks for file changes without modifying anything.
    """
    from bugtrace.utils.state import StateManager
    from bugtrace.utils.fs import ensure_state_dir, load_manifest, walk_project, hash_file
    from bugtrace.config.settings import load_user_config, validate_config
    from rich.table import Table
    
    project_root = Path(path).resolve()
    state_dir = ensure_state_dir(project_root)
    state_manager = StateManager(state_dir)
    
    console.print(f"\n[bold]Bugtrace Status[/bold]")
    console.print(f"[dim]Project:[/dim] {project_root}\n")
    
    # Create status table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Item", style="cyan")
    table.add_column("Status")
    
    # Load config to get ignore patterns
    config = load_user_config(project_root)
    ignore = config.get("paths", {}).get("ignore", [])
    
    # Check actual files on disk (without modifying manifest)
    current_files = walk_project(project_root, ignore=ignore)
    current_file_count = len(current_files)
    
    # Load manifest
    manifest = load_manifest(state_dir)
    
    # Calculate actual changes by comparing disk vs manifest
    if manifest and current_files:
        new_files = []
        changed_files = []
        unchanged_files = []
        
        current_file_paths = {str(f) for f in current_files}
        manifest_paths = set(manifest.keys())
        
        # Check each current file
        for file_path in current_files:
            file_str = str(file_path)
            current_hash = hash_file(file_path)
            
            if file_str not in manifest:
                new_files.append(file_str)
            elif manifest[file_str] != current_hash:
                changed_files.append(file_str)
            else:
                unchanged_files.append(file_str)
        
        # Check for removed files
        removed_files = [f for f in manifest_paths if f not in current_file_paths]
        
        # Display file tracking status
        total_changes = len(new_files) + len(changed_files) + len(removed_files)
        
        if total_changes > 0:
            status_parts = []
            if new_files:
                status_parts.append(f"{len(new_files)} new")
            if changed_files:
                status_parts.append(f"{len(changed_files)} changed")
            if removed_files:
                status_parts.append(f"{len(removed_files)} removed")
            
            table.add_row(
                "File tracking",
                f"[yellow]Out of sync ({', '.join(status_parts)})[/yellow]"
            )
            table.add_row("", f"[dim]Run 'bugtrace scan' to update[/dim]")
        else:
            table.add_row("File tracking", "[green]Up to date[/green]")
        
        table.add_row("Tracked files", f"[cyan]{len(manifest)} files[/cyan]")
        last_scan = state_manager.state.get("last_scan")
        if last_scan:
            table.add_row("Last scan", f"[dim]{last_scan}[/dim]")
    else:
        table.add_row("File tracking", "[yellow]Not scanned[/yellow]")
        table.add_row("", f"[dim]Run 'bugtrace scan' to initialize[/dim]")
    
    # Check index status
    indexed_files = state_manager.state.get("indexed_files", {})
    if indexed_files:
        table.add_row("Indexed files", f"[green]{len(indexed_files)} files[/green]")
        last_index = state_manager.state.get("last_index")
        if last_index:
            table.add_row("Last index", f"[dim]{last_index}[/dim]")
        
        # Check if index is stale (based on manifest)
        if manifest:
            files_to_index = state_manager.get_files_to_index(manifest)
            
            if files_to_index:
                table.add_row(
                    "Index status",
                    f"[yellow]Stale ({len(files_to_index)} files need re-indexing)[/yellow]"
                )
                table.add_row("", f"[dim]Run 'bugtrace index' to update[/dim]")
            else:
                # But also check if there are untracked file changes
                if total_changes > 0:
                    table.add_row(
                        "Index status",
                        f"[yellow]Needs update (file changes not scanned yet)[/yellow]"
                    )
                    table.add_row("", f"[dim]Run 'bugtrace index' (auto-scans & indexes)[/dim]")
                else:
                    table.add_row("Index status", "[green]Up to date[/green]")
        else:
            table.add_row("Index status", "[yellow]No manifest to compare[/yellow]")
    else:
        table.add_row("Indexed files", "[yellow]Not indexed[/yellow]")
        table.add_row("", f"[dim]Run 'bugtrace index' to build embeddings[/dim]")
    
    # Check config validity
    try:
        validate_config(config)
        table.add_row("Configuration", "[green]Valid[/green]")
    except Exception as e:
        table.add_row("Configuration", f"[red]Invalid: {str(e)[:50]}...[/red]")
    
    console.print(table)
    console.print()


@app.command()
def analyze(
    bug_description: str = typer.Argument(..., help="Description of the bug"),
    path: str = typer.Option(".", "--path", "-p", help="Project root path"),
    top_k: int = typer.Option(6, "--top-k", "-k", help="Number of results to show"),
):
    """
    Analyze a bug by finding relevant code chunks.
    """
    from bugtrace.analyze.bug_analyzer import analyze_bug
    from pathlib import Path
    
    project_root = Path(path).resolve()
    
    try:
        analyze_bug(project_root, bug_description, top_k)
    except Exception as e:
        console.print(f"\n[bold red]❌ Analysis failed:[/bold red] {e}")
        raise typer.Exit(code=1)

def run():
    app()