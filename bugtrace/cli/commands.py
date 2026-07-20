from langchain_core.messages import HumanMessage, AIMessage

def cmd_quit(console, agent, user_input):
    console.print("\n[yellow]👋 Session ended[/yellow]\n")
    return "exit"


def cmd_clear(console, agent, user_input):
    agent.clear_memory()
    console.clear()
    console.print("\n[green]✓ Conversation cleared. New session started.[/green]\n")
    return "continue"


def cmd_history(console, agent, user_input):
    messages = agent.get_conversation_history()

    console.print()  
    console.rule("[bold cyan]💬 Conversation History[/bold cyan]")
    console.print() 


    for msg in messages:
        if isinstance(msg, HumanMessage):
            console.print(f"[cyan]You:[/cyan] {msg.content}")
        elif isinstance(msg, AIMessage):
            console.print(f"[green]Bugtrace:[/green] {msg.content}")

            if getattr(msg, "tool_calls", None):
                for tool in msg.tool_calls:
                    tool_name = tool.get("name", "unknown_tool")
                    tool_args = tool.get("args", {})

                    console.print(
                        f"   [magenta]🔧 tool:[/magenta] {tool_name}"
                    )

                    # optional: show query if exists
                    if isinstance(tool_args, dict) and "query" in tool_args:
                        console.print(
                            f"      [dim]query:[/dim] {tool_args['query']}"
                        )

    console.print() 
    console.rule("[dim]End of History[/dim]")
    console.print() 
    return "continue"


def cmd_help(console, agent, user_input):
    console.print("""
[bold cyan]Available Commands[/bold cyan]

/q or /quit     Exit session
/clear          Clear memory + terminal
/history        Show conversation history
/help           Show this menu
""")
    return "continue"


# =========================
# REGISTRY
# =========================

COMMANDS = {
    "/q": cmd_quit,
    "/quit": cmd_quit,
    "/clear": cmd_clear,
    "/history": cmd_history,
    "/help": cmd_help,
}


def handle_command(user_input, console, agent):
    """
    Returns:
        "exit"     -> stop session
        "continue" -> skip agent call
        None       -> not a command
    """

    handler = COMMANDS.get(user_input.lower())

    if handler:
        return handler(console, agent, user_input)

    return None