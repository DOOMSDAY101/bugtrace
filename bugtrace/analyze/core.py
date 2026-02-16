from pathlib import Path
from bugtrace.utils.fs import walk_project, update_manifest, ensure_state_dir
from bugtrace.config.settings import load_user_config
from bugtrace.utils.state import StateManager  


from rich.console import Console

console = Console()


def scan_project(project_root: Path = None, verbose: bool = True):
    if project_root is None:
        project_root = Path.cwd()
    elif isinstance(project_root, str):
        project_root = Path(project_root).resolve()
    elif isinstance(project_root, Path):
            project_root = project_root.resolve()
    # Ensure .bugtrace exists
    state_dir = ensure_state_dir(project_root)

    state_manager = StateManager(state_dir)

    # Load user config from bugtrace.yaml
    config = load_user_config(project_root)
    
    try:
        from bugtrace.config.settings import validate_config
        validate_config(config)
        if verbose:
            console.print("[green]✓ Configuration valid[/green]")
    except ValueError as e:
        console.print(f"[red]✗ Invalid configuration: {e}[/red]")
        raise

    # Get ignore patterns from YAML
    ignore = config.get("paths", {}).get("ignore", [])

    # Walk project files
    if verbose:
        console.print("[dim]Scanning project files...[/dim]")
    all_files = walk_project(project_root, ignore=ignore)

    # Hash & update manifest
    if verbose:
        console.print("[dim]Updating manifest...[/dim]")
    stats = update_manifest(state_dir, all_files)

    # Print summary
    if verbose:
        console.print(f"\n[bold green]✔ Project scanned:[/bold green] {len(all_files)} files tracked")

    if verbose:
        console.print(
            "\n".join(
                [
                    f"[green]• New:[/green] {stats['new']}",
                    f"[yellow]• Changed:[/yellow] {stats['changed']}",
                    f"[dim]• Unchanged:[/dim] {stats['unchanged']}",
                    f"[red]• Removed:[/red] {stats['removed']} (deleted or now ignored)",
                ]
            )
        )
    # ✅ Update scan timestamp in state
    state_manager.update_scan_time()
