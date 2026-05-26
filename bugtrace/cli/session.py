"""
Session command for interactive debugging.

Provides conversational interface for bug investigation.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt

from ..config.settings import load_user_config
from ..llm import get_llm, LLMConnectionError
from ..rag.embeddings import get_embedder
from ..rag.indexer import index_project
from ..rag.vector_store import VectorStore
from ..agent.session_agent import SessionAgent
from rich.spinner import Spinner
from rich.live import Live
from langchain_core.messages import HumanMessage
from bugtrace.utils.errors import print_traceback



console = Console()


def session_command(
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory"
    ),
):
    """
    Start interactive debugging session.
    
    Examples:
        bugtrace session "login fails intermittently"
        bugtrace session  # Exploratory mode
    """
    
    console.print("\n[bold cyan]🔍 Initializing session...[/bold cyan]")
    
    try:
        # 1. Load config
        config = load_user_config(project_root)
        
        # 2. Index project
        index_project(project_root, verbose=False)
        console.print(f"[green]✓[/green] Project indexed")
        
        # 3. Setup LLM using factory
        llm = get_llm(config)
        
        # Check LLM availability
        # if not llm.is_available():
        #     provider = config.get('llm', {}).get('provider', 'ollama')
        #     model = config.get('llm', {}).get('model', 'unknown')
            
        #     console.print(f"[red]✗[/red] Model '{model}' not available for {provider}")
        #     console.print(f"\nCheck that {provider} is properly configured.")
        #     raise typer.Exit(1)
        try:
            llm.invoke([HumanMessage(content="ping")])
        except Exception as e:
            console.print(f"[red]✗[/red] LLM is not responding: {e}")
            console.print("\nMake sure Ollama is running:")
            console.print("  ollama serve")
            raise typer.Exit(1)
        
        # 4. Setup embedder using factory
        try:
            embedder = get_embedder(config)
        except ValueError as e:
            # Factory raises ValueError for unsupported providers
            console.print(f"[red]✗[/red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            # Provider-specific errors (e.g., Ollama connection error)
            console.print(f"[red]✗[/red] Failed to initialize embedder: {e}")
            raise typer.Exit(1)
        
        # 5. Setup vector store
        bugtrace_dir = project_root / ".bugtrace"
        index_dir = bugtrace_dir / "index"
        
        vector_store = VectorStore(
            index_dir=index_dir,
            project_root=project_root,
            embedder=embedder
        )
        
        # 5. Create session agent
        agent = SessionAgent(
            llm_config=config,
            vector_store=vector_store,
            project_root=project_root,
        )
        
        # 6. Display session info
        console.print()
        console.print("[bold]💬 Exploratory debugging session[/bold]")
        
        console.print("[dim]Type your questions (type \\q to quit)[/dim]\n")
        
        # 7. Interactive loop
        run_session_loop(agent)
        
    except LLMConnectionError as e:
        console.print(f"\n[red]✗[/red] LLM Connection Error: {e}")
        console.print("\nMake sure Ollama is running:")
        console.print("  [cyan]ollama serve[/cyan]")
        raise typer.Exit(1)
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 Session interrupted[/yellow]")
        raise typer.Exit(0)
    
    except Exception as e:
        print_traceback(e, "Session failed")
        raise typer.Exit(1)
    
def run_session_loop(agent: SessionAgent):
    from rich.live import Live
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.spinner import Spinner

    console = Console()

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

            if user_input.lower() in ['\\q', 'quit', 'exit']:
                console.print("\n[yellow]👋 Session ended[/yellow]\n")
                break

            if not user_input:
                continue

            event_stream = agent.stream_agent_response(user_input)

            console.print("\n[bold green]💡 Agent:[/bold green]")

            buffer = ""
            started = False
            thinking = True

            spinner = Spinner("dots", text="Thinking...")

            # SINGLE STREAM CONTROL
            with Live(spinner, console=console, transient=False) as live:

                for event in event_stream:
                    et = event["type"]

                    # =========================
                    # TOOL START
                    # =========================
                    if et == "tool_start":
                        thinking = True
                        console.print(f"\n[dim]→ Using tool {event['tool']}[/dim]")

                        query = event.get("args", {}).get("query")
                        if query:
                            console.print(f"[dim]  Query: {query}[/dim]")

                    # =========================
                    # TOOL END
                    # =========================
                    elif et == "tool_end":
                        thinking = True

                        tool = event.get("tool")
                        result = event.get("result")

                        console.print(f"\n[dim]✔ Tool finished: {tool}[/dim]")

                        if tool == "search_codebase":
                            files = event.get("files", [])

                            if files:
                                console.print(f"[dim]  Found {len(files)} file(s):[/dim]")

                                for file_info in files[:5]:
                                    if isinstance(file_info, dict):
                                        file = file_info.get("file", "unknown")
                                        line_start = file_info.get("line_start")
                                        line_end = file_info.get("line_end")
                                        function = file_info.get("function")
                                        
                                        # Build display string
                                        display = f"    • {file}"
                                        
                                        if line_start and line_end:
                                            display = f"    • {file}:{line_start} (Lines {line_start}-{line_end})"
                                        
                                        if function:
                                            display += f" :: {function}()"
                                        
                                        console.print(f"[dim]{display}[/dim]")
                                    else:
                                        # Fallback for string format
                                        console.print(f"[dim]    • {file_info}[/dim]")

                                if len(files) > 5:
                                    console.print(
                                        f"[dim]    ... and {len(files) - 5} more[/dim]"
                                    )

                        else:
                            if result:
                                console.print(f"[dim]  Result: {result[:200]}[/dim]")

                    # =========================
                    # FIRST TOKEN ARRIVES
                    # =========================
                    elif et == "token":

                        # stop spinner ONLY when real output starts
                        if not started:
                            started = True
                            # console.print()  # spacing

                        thinking = False
                        buffer += event["content"]

                        live.update(Markdown(buffer))

                    # =========================
                    # NODE DEBUG (optional)
                    # =========================
                    elif et == "node_complete":
                        console.print(f"\n[dim]--- {event['node']} done ---[/dim]")

                    # =========================
                    # SPINNER UPDATE LOGIC
                    # =========================
                    if thinking and not started:
                        live.update(spinner)

            console.print("\n")

        except KeyboardInterrupt:
            console.print("\n\n[yellow]👋 Session interrupted[/yellow]")
            break

        except Exception as e:
            print_traceback(e, "Error")

def display_thinking(intermediate_steps: list):
    """Display agent's thinking process."""
    for step in intermediate_steps:
        if isinstance(step, tuple) and len(step) >= 2:
            action, detail = step[0], step[1]
            console.print(f"  [dim]🔍 {action}: {detail}[/dim]")