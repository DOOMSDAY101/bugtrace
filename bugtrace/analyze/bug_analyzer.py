from pathlib import Path
from typing import Dict
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from bugtrace.utils.fs import ensure_state_dir
from bugtrace.rag.embeddings import get_embedder
from bugtrace.rag.vector_store import VectorStore
from bugtrace.config.settings import load_user_config
from bugtrace.rag.indexer import index_project 
from bugtrace.llm.ollama import OllamaLLM
from bugtrace.llm.base import LLMConfig

from bugtrace.agent.orchestrator import Orchestrator
from bugtrace.report.report_formatter import ReportFormatter

console = Console()


def analyze_bug(project_root: Path, bug_description: str, top_k: int = 6, show_code: bool = False, mode: str = "debug",
    stream: bool = True,
    export_markdown: str | None = None,):
    """
    Analyze a bug using RAG + LLM.
    Auto-scans and indexes if needed.
    
    Args:
        project_root: Project root directory
        bug_description: User's bug description
        top_k: Number of code chunks to retrieve
        show_code: If True, displays retrieved code chunks before analysis
    """
    valid_modes = {"debug", "explain", "review", "security"}
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}"
        )
    console.print(f"\n[bold cyan]🔍 Analyzing:[/bold cyan] {bug_description}\n")
    
     # Single source of truth
    index_project(project_root)

    # Load config and setup
    config = load_user_config(project_root)
    state_dir = ensure_state_dir(project_root)
    index_dir = state_dir / "index"
    
    # Initialize embedder and vector store
    console.print("[dim]Loading vector database...[/dim]")
    embedder = get_embedder(config)
    vector_store = VectorStore(index_dir, project_root, embedder)
    
    # Search for relevant code
    console.print("[dim]Searching for relevant code...[/dim]\n")
    results = vector_store.search(bug_description, top_k=top_k)
    
    if not results:
        console.print("[yellow]No relevant code found. Try rephrasing your query.[/yellow]")
        return
    
    # Display results
    console.print(f"[bold green]Found {len(results)} relevant code chunks:[/bold green]\n")
    
    # Optional - Show retrieved code
    if show_code:
        console.print("[bold]Retrieved Code Chunks:[/bold]\n")
        for i, result in enumerate(results, 1):
            display_result(result, i, len(results))
        console.print("\n" + "=" * 100 + "\n")

     # Initialize LLM Agent
    from bugtrace.llm import get_llm

    console.print("[dim]Initializing AI analysis...[/dim]")
    try:
        llm = get_llm(config)
        console.print(
           f"[dim]Using {llm.config.provider} model: {llm.get_model_name()} "
            f"(temp={llm.temperature})[/dim]\n"
        )
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize LLM:[/red] {e}")
        console.print("[yellow]Make sure Ollama is running and the model is pulled.[/yellow]")
        return
    
    orchestrator = Orchestrator(
        llm=llm,
        stream=stream,
        mode=mode,
    )

    # Step 7: Run LLM analysis
    try:
        result = orchestrator.analyze(
            query=bug_description,
            search_results=results,
            max_chunks=top_k,
        )
    except Exception as e:
        console.print(f"[red]✗ Analysis failed:[/red] {e}")
        return

    # Display results
    formatter = ReportFormatter()
    formatter.display_report(result)

    # Markdown export (side-effect)
    
    if export_markdown:
        formatter.export_markdown(result, export_markdown)
        console.print(
            f"\n[green]📄 Report exported to:[/green] {export_markdown}"
        )

def display_result(result: Dict, index: int, total: int):
    """Display a single search result with rich formatting."""
    metadata = result['metadata']
    text = result['text']
    score = result.get('score', 0)
    
    # Get file path (full path, not just filename)
    file_path = metadata.get('file', 'Unknown')
    
    # Get line numbers (convert from string if needed)
    line_start = metadata.get('line_start')
    line_end = metadata.get('line_end')
    
    # Convert to int if they're strings
    if line_start and isinstance(line_start, str):
        try:
            line_start = int(line_start)
        except:
            line_start = None
    
    if line_end and isinstance(line_end, str):
        try:
            line_end = int(line_end)
        except:
            line_end = None
    
    # Build header
    header_parts = [f"📄 {file_path}"]
    
    if line_start and line_end:
        header_parts.append(f"(Lines {line_start}-{line_end})")
    
    # Similarity score
    similarity = 1 - score if score <= 1 else 0
    header_parts.append(f"Similarity: {similarity:.2f}")
    
    file_info = " ".join(header_parts)
    
    # Display header
    console.print("━" * 100)
    console.print(f"[bold cyan]{file_info}[/bold cyan]")
    console.print("━" * 100)
    
    # Syntax highlighting
    file_type = metadata.get('file_type', 'python')
    syntax_map = {
        'py': 'python', 'js': 'javascript', 'jsx': 'javascript',
        'ts': 'typescript', 'tsx': 'typescript', 'java': 'java',
        'cpp': 'cpp', 'c': 'c', 'md': 'markdown', 'html': 'html',
        'css': 'css', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml'
    }
    lexer = syntax_map.get(file_type, 'python')
    
    try:
        syntax = Syntax(
            text,
            lexer,
            theme="monokai",
            line_numbers=True,
            start_line=line_start if line_start else 1,
            word_wrap=True
        )
        console.print(syntax)
    except Exception as e:
        # Fallback: just print the text
        console.print(text)
    
    # Metadata table
    console.print("\n[bold]Metadata:[/bold]")
    metadata_table = Table(show_header=False, box=None, padding=(0, 2))
    metadata_table.add_column("Key", style="cyan")
    metadata_table.add_column("Value")
    
    # File location
    metadata_table.add_row("• File", file_path)
    
    if line_start and line_end:
        metadata_table.add_row("• Lines", f"{line_start}-{line_end}")
    
    # Code metadata
    interesting_fields = {
        'function_name': '• Function',
        'class_name': '• Class',
        'has_error_handling': '• Has error handling',
        'has_logging': '• Has logging',
        'has_todo': '• Has TODO',
        'has_fixme': '• Has FIXME',
    }
    
    for field, label in interesting_fields.items():
        value = metadata.get(field)
        if value not in [None, '', 'None', 'none']:
            if isinstance(value, bool):
                value = "✓ Yes" if value else "✗ No"
            metadata_table.add_row(label, str(value))
    
    console.print(metadata_table)
    console.print()