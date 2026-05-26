from pathlib import Path
from typing import TypedDict, Annotated, Sequence, Iterator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from ..rag.vector_store import VectorStore
from ..tools.search_codebase import create_search_tool
from ..llm import get_llm
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
import json



class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    intermediate_steps: list 

class SessionAgent:
    """
    LangGraph-based ReAct agent with proper tool integration.
    
    Uses LangGraph's built-in ReAct pattern:
    - Agent decides when to use tools
    - Proper message types (HumanMessage, AIMessage, ToolMessage)
    - State management with checkpointing
    - Easy to extend with new tools
    """

    def __init__(
        self,
        vector_store: VectorStore,
        project_root: Path,
        llm_config
    ):
        self.config = llm_config
        self.llm = get_llm(self.config)
        self.vector_store = vector_store
        self.project_root = project_root
        
        # Create tools
        self.tools = self._create_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Memory/checkpointing
        self.memory = MemorySaver()
        self.thread_id = "default_session"

        # Build LangGraph
        self.graph = self._build_graph()
        
        
        # System prompt
        self.system_prompt = """You are Bugtrace, an AI debugging assistant created to help developers find and fix bugs in their code

            PERSONALITY & INTERACTION:
            - You are friendly, professional, and helpful
            - When users greet you or ask personal questions, respond warmly before offering technical help
            - Your name is "Bugtrace" - you're a specialized debugging AI
            - You can engage in brief casual conversation, but always redirect to how you can help with their code
            - Remember user details they share (like their name or programming language) and use them naturally
            - Be concise in casual chat, detailed in technical explanations

            CORE RULES:
            - You MUST use retrieved code when debugging.
            - NEVER guess functions, files, or logic not shown in tool results.
            - Tool output is the ONLY source of truth.
            - If code is missing, search again with more specific terms.

            CITATION FORMAT (CRITICAL):
            When referencing code, you MUST use this EXACT format:
            - File references: `path/to/file.py:line_number` (e.g., `bugtrace/auth.py:65`)
            - Function references: `path/to/file.py:line_number::function_name()` (e.g., `bugtrace/auth.py:65::login()`)

            Examples of CORRECT citations:
            ✓ "Bug found in `bugtrace/auth.py:52::login()` - missing error handling"
            ✓ "The function at `bugtrace/middleware/auth.py:25::check_auth()` has..."
            ✓ "In `bugtrace/routes/login.py:78`, the code..."

            Examples of INCORRECT citations (DO NOT USE):
            ✗ "Bug in auth.py" (missing full path and line number)
            ✗ "Function: login" (missing file path and line number)
            ✗ "File: auth.py" (missing line number)

            ALWAYS include:
            1. Full file path (as returned by search tool)
            2. Line number (line_start from search results)
            3. Function name (if applicable)

            SEARCH STRATEGY:
            When investigating issues:
            1. Start with broad searches (e.g., "authentication", "login", "database")
            2. Then search for specific functions/patterns (e.g., "verify_password", "hash_password", "token validation")
            3. Search for error-related code (e.g., "error handling authentication", "exception logging")

            CRITICAL: Use DESCRIPTIVE search queries with context:
            ✓ GOOD: "user authentication password verification"
            ✓ GOOD: "login error handling database connection"
            ✓ GOOD: "JWT token validation expiry check"
            ✗ BAD: "auth"
            ✗ BAD: "user"
            ✗ BAD: single words

            DEBUGGING FLOW:
            1. Understand the issue (error, logs, behavior)
            2. Search codebase with DESCRIPTIVE multi-word queries
            3. Inspect retrieved code carefully
            4. If unclear, search again with MORE SPECIFIC terms
            5. When presenting findings, ALWAYS cite with full path and line numbers
            6. Only then propose a fix

            HALLUCINATION RULE:
            If it is not in retrieved code, you must not assume it exists.
"""
    def _create_tools(self) -> list[BaseTool]:
        """Create tools for the agent."""
        tools = []
        
        # Code search tool
        search_tool = create_search_tool(
            vector_store=self.vector_store,
            top_k=3
        )
        tools.append(search_tool)
        # Future tools can be added here:
        # tools.append(log_search_tool)
        # tools.append(config_check_tool)

        return tools
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph ReAct agent graph."""
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Create tool node
        tool_node = ToolNode(self.tools)
        
        # Define nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            }
        )
        
        # Tool -> Agent edge
        workflow.add_edge("tools", "agent")
        
        # Compile
        return workflow.compile(checkpointer=self.memory)
    

    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent reasoning node - decides what to do next."""
        messages = state["messages"]
        
        # Add system message if first message
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=self.system_prompt)] + messages
        
        # Call LLM with tools
        response = self.llm_with_tools.invoke(messages)
       
        
        # Update state
        return {
            "messages": messages + [response],
            "intermediate_steps": state.get("intermediate_steps", [])
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if agent should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the LLM made a tool call, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        
        # Otherwise, end
        return "end"

    def stream_agent_response(self, user_input: str) -> Iterator[dict]:
        """
        Stream agent execution with tool calls and responses.
        
        Yields events:
        - {'type': 'tool_start', 'tool': 'name', 'args': {...}}
        - {'type': 'tool_end', 'tool': 'name', 'result': '...', 'files': [...]}
        - {'type': 'response_start'}
        - {'type': 'token', 'content': 'token'}
        - {'type': 'response_end'}
        """
        # Create message
        human_msg = HumanMessage(content=user_input)
        
        # Get current state
        config = {"configurable": {"thread_id": self.thread_id}}

        current_state = self.graph.get_state(config)
        
        #  Build initial state
        if not current_state.values.get("messages"):
            initial_state = {"messages": [HumanMessage(content=user_input)]}
        else:
            initial_state = {
                "messages": current_state.values["messages"] + [HumanMessage(content=user_input)]
            }
        
        
        # Stream graph execution
        for mode,data in self.graph.stream(initial_state, config, stream_mode=["messages", "updates"]):   
            # TOKEN STREAMING
            if mode == "messages":
                msg, meta = data

                # Only stream from agent node
                if (
                    isinstance(msg, AIMessage)
                    and msg.content
                    and meta.get("langgraph_node") == "agent"
                ):
                    yield {
                        "type": "token",
                        "content": msg.content
                    }

            # NODE UPDATES
            elif mode == "updates":
                for node_name, node_output in data.items():

                    if node_name == "agent":
                        messages = node_output.get("messages", [])
                        if not messages:
                            continue

                        last_msg = messages[-1]

                        # Tool start
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            for tool_call in last_msg.tool_calls:
                                yield {
                                    "type": "tool_start",
                                    "tool": tool_call["name"],
                                    "args": tool_call.get("args", {})
                                }

                    elif node_name == "tools":
                        # Tool executed
                        messages = node_output.get("messages", [])
                        if not messages:
                            continue
                        
                        for msg in messages:
                            if isinstance(msg, ToolMessage):
                                # Extract files from result
                                tool_name = getattr(msg, "name", "tool")

                                
                                event = {
                                "type": "tool_end",
                                "tool": tool_name,
                                "result": msg.content,
                                }
                                # try:
                                #     parsed = json.loads(msg.content)
                                #     event = {
                                #         "type": "tool_end",
                                #         "tool": tool_name,
                                #         "result": json.dumps(parsed, indent=2),
                                #     }
                                # except Exception:
                                #     event = {
                                #         "type": "tool_end",
                                #         "tool": tool_name,
                                #         "result": msg.content,
                                #     }

                                # Tool-specific post-processing
                                if tool_name == "search_codebase":
                                    event["files"] = self._extract_files_from_result(msg.content)

                                yield event
                    
                    yield {
                        "type": "node_complete",
                        "node": node_name
                    }

    def _extract_files_from_result(self, result: str) -> list[str]:
        """Extract file paths from JSON tool result."""

        import json

        files = []

        try:
            data = json.loads(result)

            # search_codebase format
            if isinstance(data, dict) and "results" in data:
                for item in data["results"]:
                    file_path = item.get("file")
                    line_start = item.get("line_start")
                    line_end = item.get("line_end")
                    function = item.get("function")
                    if file_path:
                        files.append({
                        "file": file_path,
                        "line_start": line_start,
                        "line_end": line_end,
                        "function": function
                    })

            return files

        except Exception:
            # fallback (old format or broken output)
            for line in result.split("\n"):
                if line.startswith("File: "):
                    files.append(line.replace("File: ", "").strip())

            return files
    
    def invoke(self, user_input: str) -> str:
        """
        Invoke agent synchronously (non-streaming).
        
        Args:
            user_input: User's question
            
        Returns:
            Agent's response
        """
        human_msg = HumanMessage(content=user_input)
        
        config = {"configurable": {"thread_id": self.thread_id}}
        current_state = self.graph.get_state(config)
        
        if not current_state.values.get("messages"):
            initial_state = {
                "messages": [human_msg],
                "intermediate_steps": []
            }
        else:
            initial_state = {
                "messages": current_state.values["messages"] + [human_msg],
                "intermediate_steps": []
            }
        
        # Run the graph
        result = self.graph.invoke(initial_state, config)
        
        # Extract final response
        messages = result["messages"]
        
        # Find last AI message
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        
        return "No response generated."
    
    def clear_memory(self):
        """Clear conversation history."""
        # Reset thread (creates new conversation)
        import uuid
        self.thread_id = f"session_{uuid.uuid4().hex[:8]}"
    
    def get_conversation_history(self) -> list[BaseMessage]:
        """Get conversation history."""
        config = {"configurable": {"thread_id": self.thread_id}}
        state = self.graph.get_state(config)
        return state.values.get("messages", [])
