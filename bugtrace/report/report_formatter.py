"""
Report Formatter.

Formats and displays beautiful analysis reports.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from typing import Dict, Any


class ReportFormatter:
    """
    Formats analysis results into beautiful reports.
    
    Usage:
        formatter = ReportFormatter()
        formatter.display_report(result)
    """
    
    def __init__(self):
        self.console = Console()
    
    def display_report(self, result: Dict[str, Any]):
        """
        Display complete analysis report.
        
        Args:
            result: Analysis result from Orchestrator
        """
        self.console.print()
        
        # Header
        self._display_header(result)
        
        # Main response
        self._display_response(result)
        
        context = result.get("context", {})
        if context:
            self._display_file_locations(context)
        
        # Metadata
        self._display_metadata(result)
        
        self.console.print()
    
    def _display_header(self, result: Dict[str, Any]):
        """Display report header."""
        query = result.get("query", "Unknown query")
        
        self.console.print(Panel(
            f"[bold cyan]🐛 Bug Analysis Report[/bold cyan]\n\n"
            f"[bold]Query:[/bold] {query}",
            border_style="cyan",
            padding=(1, 2)
        ))
        self.console.print()
    
    def _display_response(self, result: Dict[str, Any]):
        """Display LLM response."""
        response = result.get("response", "No response")
        
        # Try to render as Markdown
        try:
            md = Markdown(response)
            self.console.print(Panel(
                md,
                title="[bold]Analysis[/bold]",
                border_style="green",
                padding=(1, 2)
            ))
        except Exception:
            # Fallback to plain text
            self.console.print(Panel(
                response,
                title="[bold]Analysis[/bold]",
                border_style="green",
                padding=(1, 2)
            ))
    
    def _display_metadata(self, result: Dict[str, Any]):
        """Display analysis metadata."""
        metadata = result.get("metadata", {})
        
        if not metadata:
            return
        
        lines = []
        
        if "model" in metadata:
            lines.append(f"[bold]Model:[/bold] {metadata['model']}")
        
        if "chunks_analyzed" in metadata:
            lines.append(f"[bold]Chunks Analyzed:[/bold] {metadata['chunks_analyzed']}")
        
        if "files_analyzed" in metadata:
            lines.append(f"[bold]Files Analyzed:[/bold] {metadata['files_analyzed']}")
        
        if "mode" in metadata:
            lines.append(f"[bold]Mode:[/bold] {metadata['mode']}")
        
        if lines:
            self.console.print(Panel(
                "\n".join(lines),
                title="[bold]Analysis Info[/bold]",
                border_style="blue",
                padding=(0, 2)
            ))
    
    def display_code_snippet(
        self,
        code: str,
        language: str = "python",
        title: str = None
    ):
        """
        Display syntax-highlighted code snippet.
        
        Args:
            code: Code to display
            language: Programming language
            title: Optional title
        """
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=True
        )
        
        if title:
            self.console.print(Panel(
                syntax,
                title=f"[bold]{title}[/bold]",
                border_style="cyan"
            ))
        else:
            self.console.print(syntax)
    
    def display_error(self, error: str):
        """Display error message."""
        self.console.print()
        self.console.print(Panel(
            f"[bold red]❌ Error[/bold red]\n\n{error}",
            border_style="red",
            padding=(1, 2)
        ))
        self.console.print()
    
    def display_warning(self, warning: str):
        """Display warning message."""
        self.console.print()
        self.console.print(Panel(
            f"[bold yellow]⚠️  Warning[/bold yellow]\n\n{warning}",
            border_style="yellow",
            padding=(1, 2)
        ))
        self.console.print()
    
    def display_files_analyzed(self, context: Dict[str, Any]):
        """
        Display list of files that were analyzed.
        
        Args:
            context: Context from ContextBuilder
        """
        snippets = context.get("code_snippets", [])
        
        if not snippets:
            return
        
        # Group by file
        files = {}
        for snippet in snippets:
            file = snippet.get("file", "unknown")
            if file not in files:
                files[file] = []
            
            if "function" in snippet:
                files[file].append(snippet["function"])
        
        # Display
        lines = []
        for file, functions in sorted(files.items()):
            lines.append(f"[bold]{file}[/bold]")
            for func in functions:
                lines.append(f"  • {func}()")
        
        self.console.print(Panel(
            "\n".join(lines),
            title="[bold]Files Analyzed[/bold]",
            border_style="cyan",
            padding=(1, 2)
        ))

    def _display_file_locations(self, context: Dict[str, Any]):
        snippets = context.get("code_snippets", [])
        if not snippets:
            return

        lines = []
        seen = set()

        for s in snippets:
            file = s.get("file")
            lines_range = s.get("lines")

            if not file:
                continue

            key = (file, lines_range)
            if key in seen:
                continue
            seen.add(key)

            if lines_range:
                # Clickable in most terminals
                lines.append(f"📄 [bold]{file}:{lines_range}[/bold]")
            else:
                lines.append(f"📄 [bold]{file}[/bold]")

        self.console.print(Panel(
            "\n".join(lines),
            title="[bold]Files & Relevant Lines[/bold]",
            border_style="magenta",
            padding=(1, 2)
        ))

    
    def export_markdown(self, result: Dict[str, Any], output_path: Path):
        """
        Export report as Markdown file.
        
        Args:
            result: Analysis result
            output_path: Path to save Markdown file
        """
        lines = []
        
        # Header
        lines.append("# 🐛 Bug Analysis Report")
        lines.append("")
        lines.append(f"**Query:** {result.get('query', 'Unknown')}")
        lines.append("")
        
        # Metadata
        metadata = result.get("metadata", {})
        if metadata:
            lines.append("## Analysis Info")
            lines.append("")
            for key, value in metadata.items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            lines.append("")
        
        # Response
        lines.append("## Analysis")
        lines.append("")
        lines.append(result.get("response", "No response"))
        lines.append("")
        
        # Files analyzed
        context = result.get("context", {})
        if context.get("code_snippets"):
            lines.append("## Files Analyzed")
            lines.append("")
            files = set()
            for snippet in context["code_snippets"]:
                files.add(snippet.get("file", "unknown"))
            
            for file in sorted(files):
                lines.append(f"- `{file}`")
            lines.append("")
        
        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        