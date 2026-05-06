import sys
import traceback
from rich.console import Console

console = Console()


def print_traceback(error: Exception, title: str = "Error occurred"):
    """
    Print a clean, readable traceback with file + line context.
    """

    console.print(f"\n[red]✗ {title}[/red]\n")

    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)

    for frame in tb:
        console.print(
            f"[red]File[/red] {frame.filename}, "
            f"[red]line[/red] {frame.lineno}, "
            f"[red]in[/red] {frame.name}"
        )
        if frame.line:
            console.print(f"  → {frame.line}")

    console.print(f"\n[bold red]Message:[/bold red] {error}")