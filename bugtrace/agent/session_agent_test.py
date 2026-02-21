"""
Session Agent for Interactive Debugging.

Sets up LangChain agent with combined memory and tools.
"""

from pathlib import Path
from typing import Optional
# from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

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
from langchain_core.runnables import RunnablePassthrough


# ReAct Agent Prompt Template
# REACT_PROMPT_TEMPLATE = """You are an expert debugging assistant helping a developer understand and fix bugs in their codebase.

# You have access to tools that let you search the codebase. **Only use tools when you need to find code.** For general conversation or greetings, just respond normally.

# TOOLS:
# {tools}

# WHEN TO USE TOOLS:
# - User asks about specific code, functions, classes, or files
# - User describes a bug that needs investigation
# - User asks "how does X work" where X is code-related

# WHEN NOT TO USE TOOLS:
# - Greetings like "hi", "hello", "hey"
# - General questions like "what can you do?"
# - Follow-up questions where you already have the context

# TOOL USE FORMAT:
# Action: search_codebase
# Action Input: your search query here

# Example - Greeting (NO TOOL):
# Question: hi
# Thought: This is a greeting, no need to search code.
# Final Answer: Hello! I'm here to help you debug issues in your codebase. You can ask me about bugs, how code works, or describe issues you're facing.

# Example - Code Question (USE TOOL):
# Question: why does login fail?
# Thought: I need to find the login code to understand the issue.
# Action: search_codebase
# Action Input: login authentication
# Observation: [search results]
# Thought: Now I can analyze the code.
# Final Answer: [analysis based on code]

# Use the following format:

# Question: the input question you must answer
# Thought: think about what to do
# Action: the action to take, must be one of [{tool_names}]
# Action Input: the input to the action (just the query string, nothing else)
# Observation: the result of the action
# ... (this Thought/Action/Action Input/Observation can repeat N times)
# Thought: I now know the final answer
# Final Answer: the final answer to the original input question

# Previous conversation and context:
# {chat_history}

# {chat_summary}

# Relevant code context from earlier:
# {code_context}

# Begin!

# Question: {input}
# Thought: {agent_scratchpad}"""

# ROUTER_PROMPT = """
# You are an intent router for a developer assistant.

# Decide whether the user message requires:
# (A) normal conversation, or
# (B) deep code investigation using search tools.

# Choose (B) ONLY if the message clearly refers to:
# - a bug
# - an error
# - unexpected behavior
# - debugging a codebase
# - investigating source code

# If the message is a greeting, discussion, brainstorming,
# or high-level question, choose (A).

# Respond with EXACTLY one token:
# CHAT or AGENT

# User message:
# "{input}"
# """

CONVERSATION_PROMPT = """You are an expert debugging assistant.

You are chatting with a developer about their codebase.

You may be given:
- recent conversation history
- a summary of earlier discussion
- relevant code snippets or file context

You are chatting with a developer about their codebase.
You may call tools when they are helpful.

Use tools ONLY if you need more information from the codebase.
If no tool is needed, answer directly.

Use the provided context naturally when helpful.
If no code context is relevant, just answer conversationally.

Conversation history:
{chat_history}

Conversation summary:
{chat_summary}

User message:
{input}

{agent_scratchpad}
Answer naturally and concisely.
"""
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
        self.chain = self._create_chain()
        
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
    
    # def _create_agent(self) -> AgentExecutor:
    #     """
    #     Create ReAct agent with tools and memory.
        
    #     Returns:
    #         AgentExecutor
    #     """
    #     # Create prompt
    #     prompt = PromptTemplate(
    #         template=REACT_PROMPT_TEMPLATE,
    #         input_variables=["input", "agent_scratchpad", "chat_history", 
    #                        "chat_summary", "code_context"],
    #         partial_variables={
    #             "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
    #             "tool_names": ", ".join([tool.name for tool in self.tools])
    #         }
    #     )
        
    #     # Create agent
    #     agent = create_react_agent(
    #         llm=self.llm.get_langchain_llm(),
    #         tools=self.tools,
    #         prompt=prompt
    #     )
        
    #     # Create executor
    #     agent_executor = AgentExecutor(
    #         agent=agent,
    #         tools=self.tools,
    #         memory=self.memory,
    #         verbose=False,  # Show thinking process
    #         max_iterations=5,  # Prevent infinite loops
    #         handle_parsing_errors=True,
    #         return_intermediate_steps=True,
    #         early_stopping_method="generate"
    #     )
        
    #     return agent_executor
    

    def _create_chain(self):
        prompt = PromptTemplate(
            template=CONVERSATION_PROMPT,
            input_variables=[
                "input",
                "chat_history",
                "chat_summary",
                "code_context",
            ],
        )

        # return (
        #     {
        #         "input": RunnablePassthrough(),
        #         "chat_history": lambda _: self.memory.load_memory_variables({}).get("chat_history", ""),
        #         "chat_summary": lambda _: self.memory.load_memory_variables({}).get("chat_summary", ""),
        #         "code_context": lambda _: self.memory.load_memory_variables({}).get("code_context", ""),
        #     }
        #     | prompt
        #     | self.llm.get_langchain_llm()
        # )
        def run_chain(user_input: str):
        # Load memory
            mem_vars = self.memory.load_memory_variables({"input": user_input})
            chat_history = mem_vars.get("chat_history", "")
            chat_summary = mem_vars.get("chat_summary", "")
            code_context = mem_vars.get("code_context", "")

            # Format prompt with all variables
            full_prompt = prompt.format(
                input=user_input,
                chat_history=chat_history,
                chat_summary=chat_summary,
                code_context=code_context,
            )

            # Call LLM
            return self.llm.get_langchain_llm().invoke(full_prompt)
        return run_chain
    
    def _create_agent(self):
        prompt = PromptTemplate(
            template=CONVERSATION_PROMPT,
            input_variables=["input", "chat_history", "chat_summary", "agent_scratchpad"],
        )

        agent = create_tool_calling_agent(
            llm=self.llm.get_langchain_llm(),
            tools=self.tools,
            prompt=prompt,
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            return_intermediate_steps=False,
        )
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
        
        # def route_intent(self, user_input: str) -> str:
        #     router_prompt = ROUTER_PROMPT.format(input=user_input)

        #     decision_resp = self.llm.chat([
        #         {"role": "user", "content": router_prompt}
        #     ], temperature=0.0, max_tokens=1)

        # # Extract decision and normalize
        #     decision = decision_resp.strip().upper()
        #     return decision if decision in {"CHAT", "AGENT"} else "CHAT"


    # def chat(self, user_input: str) -> dict:
    #     """
    #     Process user input and route to chat or agent.

    #     Args:
    #         user_input: User's question or command

    #     Returns:
    #         Dict with:
    #         - 'output': final response
    #         - 'intermediate_steps': any agent reasoning steps
    #     """
    #     try:
    #         # Determine intent
    #         intent = self.route_intent(user_input)

    #         if intent == "CHAT":
    #             # Wrap string in Ollama-compatible message
    #             response = self.llm.chat([
    #                 {"role": "user", "content": user_input}
    #             ])
    #             return {
    #                 "output": response,
    #                 "intermediate_steps": []
    #             }

    #         # AGENT path: invoke the agent executor
    #         result = self.agent_executor.invoke({"input": user_input})
    #         return result

    #     except Exception as e:
    #         return {
    #             "output": f"Error: {str(e)}",
    #             "intermediate_steps": []
    #         }
    
    # def chat(self, user_input: str) -> dict:
    #     """
    #     Process user input conversationally with memory and implicit code context.
    #     """
    #     try:
    #         # Call the chain - it returns an AIMessage object
    #         response = self.chain(user_input)
            
    #         # Extract text from AIMessage - FIX: get the content attribute
    #         if hasattr(response, 'content'):
    #             response_text = response.content
    #         else:
    #             response_text = str(response)
            
    #         # Save to memory
    #         self.memory.save_context(
    #             {"input": user_input},
    #             {"output": response_text}
    #         )
            
    #         return {
    #             "output": response_text,
    #             "intermediate_steps": []
    #         }
    #     except Exception as e:
    #         # Add more detail to error for debugging
    #         import traceback
    #         error_detail = traceback.format_exc()
    #         print(f"[DEBUG] Full error: {error_detail}")
    #         return {
    #             "output": f"Error: {str(e)}",
    #             "intermediate_steps": []
    #         } 
    
    def chat(self, user_input: str) -> dict:
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return {
                "output": result["output"],
                "intermediate_steps": [],
            }
        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "intermediate_steps": [],
            }
   
    def get_conversation_history(self) -> str:
        """Get formatted conversation history."""
        try:
            history = self.memory.load_memory_variables({})
            return str(history)
        except:
            return "No history available"