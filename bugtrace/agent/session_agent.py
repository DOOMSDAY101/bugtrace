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
        self.system_prompt = """You are a coding assistant.

        Answer the user directly and concisely.

        Only use tools when absolutely necessary.
        Always cite specific files and line numbers when discussing code.

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
        
        # Build initial state
        if not current_state.values.get("messages"):
            messages = [human_msg]
        else:
            messages = current_state.values["messages"] + [human_msg]
        
        initial_state = {"messages": messages}
        
        
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

                                # Tool-specific post-processing
                                if tool_name == "search_codebase":
                                    event["files"] = self._extract_files_from_result(msg.content)

                                yield event
                    
                    yield {
                        "type": "node_complete",
                        "node": node_name
                    }

    def _extract_files_from_result(self, result: str) -> list[str]:
        """Extract file paths from tool result."""
        files = []
        for line in result.split('\n'):
            if line.startswith('File: '):
                file_path = line.replace('File: ', '').strip()
                files.append(file_path)
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
