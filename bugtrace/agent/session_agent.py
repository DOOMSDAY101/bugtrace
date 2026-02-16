"""
Session Agent for Interactive Debugging.

Sets up LangChain agent with combined memory and tools.
"""

from pathlib import Path
from typing import Optional
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_classic.memory import (
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    VectorStoreRetrieverMemory,
    CombinedMemory
)
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma

from ..llm.base import BaseLLM
from ..rag.vector_store import VectorStore
from ..tools.search_codebase import create_search_tool


# ReAct Agent Prompt Template
REACT_PROMPT_TEMPLATE = """You are an expert debugging assistant helping a developer understand and fix bugs in their codebase.

You have access to tools that let you search the codebase. Use them to gather context before answering.

TOOLS:
{tools}

When responding:
- Always cite file paths and line numbers when discussing code
- Think step-by-step and explain your reasoning
- Ask clarifying questions if needed
- Suggest concrete fixes with code examples
- Be conversational and helpful, not overly formal

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Previous conversation and context:
{chat_history}

{chat_summary}

Relevant code context from earlier:
{code_context}

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


class SessionAgent:
    """
    Interactive debugging agent with memory.
    
    Uses ReAct agent with combined memory:
    - ConversationBufferWindowMemory (recent chat)
    - ConversationSummaryMemory (compressed history)
    - VectorStoreRetrieverMemory (code context)
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        vector_store: VectorStore,
        project_root: Path,
        initial_query: Optional[str] = None
    ):
        """
        Initialize session agent.
        
        Args:
            llm: LLM instance (OllamaLLM, etc.)
            vector_store: Vector store with indexed code
            project_root: Project root directory
            initial_query: Optional initial bug description
        """
        self.llm = llm
        self.vector_store = vector_store
        self.project_root = project_root
        self.initial_query = initial_query
        
        # Create tools
        self.tools = [
            create_search_tool(vector_store, top_k=6)
        ]
        
        # Setup memory
        self.memory = self._setup_memory()
        
        # Create agent
        self.agent_executor = self._create_agent()
        
        # If initial query provided, do initial search
        if initial_query:
            self._initialize_context(initial_query)
    
    def _setup_memory(self) -> CombinedMemory:
        """
        Setup combined memory system.
        
        Returns:
            CombinedMemory with three memory types
        """
        # 1. Recent conversation (last 5 turns)
        recent_memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            return_messages=False
        )
        
        # 2. Compressed older conversation
        summary_memory = ConversationSummaryMemory(
            llm=self.llm.get_langchain_llm(),  # Need LangChain-compatible LLM
            memory_key="chat_summary",
            input_key="input",
            output_key="output",
            return_messages=False
        )
        
        # 3. Code/facts memory using vector store
        # Create a retriever from the vector store
        retriever = self.vector_store.vector_store.as_retriever(
            search_kwargs={"k": 3}
        )
        
        code_memory = VectorStoreRetrieverMemory(
            retriever=retriever,
            memory_key="code_context",
            input_key="input",
            return_messages=False
        )
        
        # Combine all memories
        combined_memory = CombinedMemory(
            memories=[recent_memory, summary_memory, code_memory]
        )
        
        return combined_memory
    
    def _create_agent(self) -> AgentExecutor:
        """
        Create ReAct agent with tools and memory.
        
        Returns:
            AgentExecutor
        """
        # Create prompt
        prompt = PromptTemplate(
            template=REACT_PROMPT_TEMPLATE,
            input_variables=["input", "agent_scratchpad", "chat_history", 
                           "chat_summary", "code_context"],
            partial_variables={
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )
        
        # Create agent
        agent = create_react_agent(
            llm=self.llm.get_langchain_llm(),
            tools=self.tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,  # Show thinking process
            max_iterations=8,  # Prevent infinite loops
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        return agent_executor
    
    def _initialize_context(self, query: str):
        """
        Do initial search to set context if bug description provided.
        
        Args:
            query: Initial bug description
        """
        # Search for relevant code
        results = self.vector_store.search(query, top_k=6)
        
        if results:
            # Store initial context in code memory
            context_summary = f"Initial context for '{query}':\n"
            files_found = set()
            
            for result in results:
                file_path = result['metadata'].get('file', 'unknown')
                files_found.add(file_path)
            
            context_summary += f"Relevant files: {', '.join(files_found)}"
            
            # Save to memory
            self.memory.save_context(
                {"input": f"Initialize context for: {query}"},
                {"output": context_summary}
            )
    
    def chat(self, user_input: str) -> dict:
        """
        Process user input and return agent response.
        
        Args:
            user_input: User's question or command
        
        Returns:
            Dict with 'output' (final answer) and 'intermediate_steps' (thinking)
        """
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result
        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "intermediate_steps": []
            }
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history."""
        try:
            history = self.memory.load_memory_variables({})
            return str(history)
        except:
            return "No history available"