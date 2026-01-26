from pathlib import Path
from bugtrace.utils.fs import walk_project, update_manifest, ensure_state_dir
from bugtrace.config.settings import load_user_config
from bugtrace.utils.state import StateManager  


from rich.console import Console

console = Console()


def analyze(project_root: Path = None):
    project_root = project_root or Path.cwd()

    # Ensure .bugtrace exists
    state_dir = ensure_state_dir(project_root)

    state_manager = StateManager(state_dir)

    # Load user config from bugtrace.yaml
    config = load_user_config(project_root)
    
    try:
        from bugtrace.config.settings import validate_config
        validate_config(config)
        console.print("[green]✓ Configuration valid[/green]")
    except ValueError as e:
        console.print(f"[red]✗ Invalid configuration: {e}[/red]")
        raise

    # Get ignore patterns from YAML
    ignore = config.get("paths", {}).get("ignore", [])

    # Walk project files
    console.print("[dim]Scanning project files...[/dim]")
    all_files = walk_project(project_root, ignore=ignore)

    # Hash & update manifest
    console.print("[dim]Updating manifest...[/dim]")
    stats = update_manifest(state_dir, all_files)

    # Print summary
    console.print(f"\n[bold green]✔ Project scanned:[/bold green] {len(all_files)} files tracked")
    
    # if stats['new'] > 0:
    #     console.print(f"   [green]• New:[/green] {stats['new']}")
    # if stats['changed'] > 0:
    #     console.print(f"   [yellow]• Changed:[/yellow] {stats['changed']}")
    # if stats['unchanged'] > 0:
    #     console.print(f"   [dim]• Unchanged:[/dim] {stats['unchanged']}")
    # if stats['removed'] > 0:
    #     console.print(f"   [red]• Removed:[/red] {stats['removed']} (deleted or now ignored)")
    
    # console.print()

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
