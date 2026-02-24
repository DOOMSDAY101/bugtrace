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



console = Console()


def session_command(
    bug_description: Optional[str] = typer.Argument(
        None,
        help="Optional initial bug description"
    ),
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
        if not llm.is_available():
            provider = config.get('llm', {}).get('provider', 'ollama')
            model = config.get('llm', {}).get('model', 'unknown')
            
            console.print(f"[red]✗[/red] Model '{model}' not available for {provider}")
            console.print(f"\nCheck that {provider} is properly configured.")
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
            llm=llm,
            vector_store=vector_store,
            project_root=project_root,
            initial_query=bug_description
        )
        
        # 6. Display session info
        console.print()
        if bug_description:
            console.print(f"[bold]💬 Debugging:[/bold] {bug_description}")
            console.print("[green]✓[/green] Initial context loaded")
        else:
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
        console.print(f"\n[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


# def run_session_loop(agent: SessionAgent):
#     """Run the interactive session loop with streaming."""
#     from rich.spinner import Spinner
#     from rich.live import Live
    
#     while True:
#         try:
#             # Get user input
#             user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
            
#             # Check for quit command
#             if user_input.lower() in ['\\q', 'quit', 'exit']:
#                 console.print("\n[yellow]👋 Session ended[/yellow]\n")
#                 break
            
#             # Skip empty input
#             if not user_input:
#                 continue
            
#             # Show spinner while waiting
#             spinner = Spinner("dots", text="Responding...")
            
#             try:
#                 from ..llm.base import Message
                
#                 messages = [Message(role="system", content=agent.system_prompt)]
                
#                 # Add history
#                 # Load history from LangChain memory
#                 memory_variables = agent.memory.load_memory_variables({})
#                 chat_history = memory_variables.get("chat_history", "")
                
#                 # Add history if exists
#                 if chat_history:
#                     history_lines = chat_history.strip().split("\n")
#                     for line in history_lines:
#                         if line.startswith("Human: "):
#                             messages.append(Message(role="user", content=line[7:]))
#                         elif line.startswith("AI: "):
#                             messages.append(Message(role="assistant", content=line[4:]))
                
#                 messages.append(Message(role="user", content=user_input))
                
#                 # Start streaming
#                 stream = agent.llm.chat_stream(messages)
                
#                 # Show spinner until first token
#                 with Live(spinner, console=console, transient=True):
#                     first_token = next(stream)
                
#                 # Show Agent label and first token
#                 console.print()  
#                 console.print(f"[bold green]💡 Agent:[/bold green] ", end="")  # No \n here
#                 console.print(first_token, end="")
#                 # Continue streaming rest of tokens
#                 full_response = [first_token]
#                 for token in stream:
#                     console.print(token, end="")
#                     full_response.append(token)
#                 console.print()  # New line
                
#                 # Save to history
#                 response_text = "".join(full_response)
#                 agent.memory.save_context(
#                     {"input": user_input},
#                     {"output": response_text}
#                 )
            
#             except Exception as e:
#                 console.print(f"\n[red]Error:[/red] {e}")
        
#         except KeyboardInterrupt:
#             console.print("\n\n[yellow]👋 Session interrupted[/yellow]")
#             break
        
#         except Exception as e:
#             console.print(f"\n[red]Error:[/red] {e}")
#             console.print("[dim]Type \\q to quit[/dim]")


def run_session_loop(agent: SessionAgent):
    """Run the interactive session loop with real-time formatted streaming."""
    from rich.spinner import Spinner
    from rich.live import Live
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
            
            if user_input.lower() in ['\\q', 'quit', 'exit']:
                console.print("\n[yellow]👋 Session ended[/yellow]\n")
                break
            
            if not user_input:
                continue
            
            spinner = Spinner("dots", text="Processing...")
            
            try:
                # Prepare messages
                with Live(spinner, console=console, transient=True):
                    prepared = agent.prepare_messages(user_input)
                
                messages = prepared['messages']
                intermediate_steps = prepared['intermediate_steps']
                
                # Display intermediate steps
                if intermediate_steps:
                    display_thinking(intermediate_steps)
                
                # Stream response
                stream = agent.llm.chat_stream(messages)
                
                # Show spinner until first token
                with Live(spinner, console=console, transient=True):
                    first_token = next(stream)
                
                # Show Agent label
                console.print()
                console.print(f"[bold green]💡 Agent:[/bold green]\n")
                
                # Use Rich Markdown streaming
                accumulated = first_token
                full_response = [first_token]
                
                # Create a Live display for markdown
                from rich.live import Live
                from rich.markdown import Markdown
                from rich.text import Text

                text = Text(accumulated, overflow="fold")

                
                with Live(text, console=console, refresh_per_second=10,screen=False,          # IMPORTANT
                    auto_refresh=True) as live:
                    # live.update(Markdown(accumulated))
                    
                    for token in stream:
                        accumulated += token
                        full_response.append(token)
                        
                        # Update markdown display in real-time
                        text.append(token)
                        live.update(text)
                        live.update(Markdown(accumulated))
                    
                
                console.print()  # spacing
                
                
                # Save to memory
                response_text = "".join(full_response)
                agent.memory.save_context(
                    {"input": user_input},
                    {"output": response_text}
                )
            
            except Exception as e:
                import traceback
                console.print(f"\n[red]Error:[/red] {e}")
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]👋 Session interrupted[/yellow]")
            break
        
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")
            console.print("[dim]Type \\q to quit[/dim]")


# def display_thinking(intermediate_steps: list):
#     """
#     Display agent's thinking process.
    
#     Args:
#         intermediate_steps: List of (action, observation) tuples
#     """
#     for action, observation in intermediate_steps:
#         # Show action
#         action_name = getattr(action, 'tool', 'unknown')
#         action_input = getattr(action, 'tool_input', '')
        
#         console.print(f"  [dim]→ {action_name}[/dim]", end="")
        
#         if action_input:
#             # Show abbreviated input
#             if isinstance(action_input, dict):
#                 input_str = str(action_input.get('query', action_input))
#             else:
#                 input_str = str(action_input)
            
#             if len(input_str) > 50:
#                 input_str = input_str[:47] + "..."
            
#             console.print(f"[dim]: {input_str}[/dim]")
#         else:
#             console.print()


def display_thinking(intermediate_steps: list):
    """Display agent's thinking process."""
    for step in intermediate_steps:
        if isinstance(step, tuple) and len(step) >= 2:
            action, detail = step[0], step[1]
            console.print(f"  [dim]🔍 {action}: {detail}[/dim]")