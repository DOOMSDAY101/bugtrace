"""
Real-time status reporting system for Bugtrace.

This module provides beautiful CLI status updates during analysis.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.table import Table
from rich.text import Text
from typing import List, Optional
from contextlib import contextmanager

console = Console()


class StatusReporter:
    """
    Central system for reporting status during analysis.
    
    Usage:
        reporter = StatusReporter()
        
        with reporter.section("Scanning files"):
            reporter.info("Found 42 files")
            reporter.success("Loaded 156 chunks")
        
        with reporter.section("Analyzing", show_spinner=True):
            # Long-running task
            reporter.update("Processing...")
    """
    
    def __init__(self):
        self.console = Console()
        self._current_live = None
        self._current_table = None
    
    def header(self, title: str, query: str):
        """Display analysis header."""
        self.console.print()
        self.console.print(f"🔍 Analyzing bug: [bold cyan]{query}[/bold cyan]")
        self.console.print()
    
    @contextmanager
    # def section(self, title: str, show_spinner: bool = False):
    #     """
    #     Create a status section with optional spinner.
        
    #     Args:
    #         title: Section title (e.g., "Scanning files")
    #         show_spinner: Show spinning animation during section
        
    #     Example:
    #         with reporter.section("Loading files", show_spinner=True):
    #             # Do work
    #             reporter.info("Found 10 files")
    #     """
    #     # Create table for this section
    #     table = Table.grid(padding=(0, 1))
    #     table.add_column(style="bold")
        
    #     # Add header row
    #     icon = "⏳" if show_spinner else "📂"
    #     table.add_row(f"{icon} {title}...")
        
    #     self._current_table = table
        
    #     if show_spinner:
    #         # Use Live display with spinner
    #         with Live(table, console=self.console, refresh_per_second=10) as live:
    #             self._current_live = live
    #             try:
    #                 yield
    #             finally:
    #                 self._current_live = None
    #     else:
    #         # Static display
    #         self.console.print(Panel(table, border_style="blue", padding=(0, 1)))
    #         try:
    #             yield
    #         finally:
    #             self._current_table = None
    def section(self, title: str, show_spinner: bool = False):
        icon = "⏳" if show_spinner else "›"
        self.console.print(f"[dim]{icon} {title}...[/dim]")
        try:
            yield
        finally:
            pass


    def info(self, message: str):
        """Add info message to current section."""
        if self._current_table:
            self._current_table.add_row(f"  • {message}")
            if self._current_live:
                self._current_live.update(Panel(
                    self._current_table, 
                    border_style="blue", 
                    padding=(0, 1)
                ))
    
    def success(self, message: str):
        """Add success message to current section."""
        if self._current_table:
            self._current_table.add_row(f"  [green]✓[/green] {message}")
            if self._current_live:
                self._current_live.update(Panel(
                    self._current_table, 
                    border_style="green", 
                    padding=(0, 1)
                ))
        else:
            self.console.print(f"[green]✓[/green] {message}")
    
    def warning(self, message: str):
        """Add warning message to current section."""
        if self._current_table:
            self._current_table.add_row(f"  [yellow]⚠[/yellow] {message}")
            if self._current_live:
                self._current_live.update(Panel(
                    self._current_table, 
                    border_style="yellow", 
                    padding=(0, 1)
                ))
        else:
            self.console.print(f"[yellow]⚠[/yellow] {message}")
    
    def error(self, message: str):
        """Add error message to current section."""
        if self._current_table:
            self._current_table.add_row(f"  [red]✗[/red] {message}")
            if self._current_live:
                self._current_live.update(Panel(
                    self._current_table, 
                    border_style="red", 
                    padding=(0, 1)
                ))
        else:
            self.console.print(f"[red]✗[/red] {message}")
    
    def update(self, message: str):
        """Update current section message (for spinners)."""
        if self._current_table and self._current_live:
            # Update last row
            self._current_table.rows[-1] = (f"  ⏳ {message}",)
            self._current_live.update(Panel(
                self._current_table, 
                border_style="blue", 
                padding=(0, 1)
            ))
    
    def list_items(self, items: List[str], prefix: str = "•"):
        """Display list of items in current section."""
        for item in items:
            self.info(f"{prefix} {item}")
    
    def complete(self, message: str = "Analysis complete!"):
        """Display completion message."""
        self.console.print()
        self.console.print(Panel(
            f"[bold green]✨ {message}[/bold green]",
            border_style="green",
            padding=(0, 1)
        ))
        self.console.print()
    
    def stream_start(self, title: str):
        """Start streaming section (for LLM responses)."""
        self.console.print()
        self.console.print(Panel(
            f"[bold]💭 {title}[/bold]",
            border_style="cyan",
            padding=(0, 1)
        ))
        self.console.print()
    
    def stream_token(self, token: str):
        """Print streaming token (no newline)."""
        self.console.print(token, end="")
    
    def stream_end(self):
        """End streaming section."""
        self.console.print()  # Final newline


# Global instance
_reporter = StatusReporter()


def get_reporter() -> StatusReporter:
    """Get global status reporter instance."""
    return _reporter