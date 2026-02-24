from pathlib import Path
from typing import Optional, List, Dict,Literal

from ..llm.base import BaseLLM, Message
from ..rag.vector_store import VectorStore
from ..tools.search_codebase import create_search_tool
from langchain_core.prompts import PromptTemplate


from langchain_classic.memory import (
    ConversationBufferMemory,
)


# class IntentRouter:
#     """
#     Lightweight intent router - no LLM calls, no token cost.
    
#     Uses keyword patterns to detect when tools are needed.
#     """
    
#     def __init__(self):
#         # Define tool triggers with keywords
#         self.tool_patterns = {
#             'search_codebase': {
#                 'keywords': [
#                     # Bug/error keywords
#                     'bug', 'error', 'issue', 'problem', 'fail', 'crash', 'break',
#                     'exception', 'warning', 'traceback', 'stderr',
                    
#                     # Code investigation keywords
#                     'function', 'class', 'method', 'variable', 'code', 
#                     'file', 'line', 'module', 'import',
                    
#                     # Questions about code
#                     'why does', 'how does', 'what does', 'where is',
#                     'show me', 'find', 'search', 'look for',
                    
#                     # Analysis keywords
#                     'analyze', 'debug', 'fix', 'solve', 'investigate',
#                     'explain the code', 'understand the code'
#                 ],
#                 'min_words': 2  # Only trigger if query has 2+ words
#             },
            
#             # Add more tools here as you build them
#             # 'search_logs': {
#             #     'keywords': ['log', 'logs', 'logging', 'logged'],
#             #     'min_words': 2
#             # },
#             # 'run_tests': {
#             #     'keywords': ['test', 'tests', 'pytest', 'unittest'],
#             #     'min_words': 2
#             # }
#         }
        
#         # Greetings - always just chat
#         self.greeting_patterns = [
#             'hi', 'hello', 'hey', 'sup', 'yo',
#             'thanks', 'thank you', 'ok', 'okay', 'cool',
#             'bye', 'goodbye', 'see you'
#         ]
        
#         # Meta questions - always just chat
#         self.meta_patterns = [
#             'what can you do',
#             'what can you help',
#             'who are you',
#             'what are you',
#             'how can you help'
#         ]
    
#     def route(self, user_input: str) -> Literal['chat', 'search_codebase']:
#         """
#         Route user input to appropriate handler.
        
#         Returns:
#             'chat' - just talk to LLM
#             'search_codebase' - search code then talk to LLM
#             (can add more tool types as you build them)
#         """
#         query = user_input.lower().strip()
#         words = query.split()
        
#         # 1. Check greetings - always chat
#         if len(words) <= 2:
#             if any(query.startswith(g) for g in self.greeting_patterns):
#                 return 'chat'
        
#         # 2. Check meta questions - always chat
#         if any(pattern in query for pattern in self.meta_patterns):
#             return 'chat'
        
#         # 3. Check tool patterns
#         for tool_name, config in self.tool_patterns.items():
#             # Check minimum word count
#             if len(words) < config.get('min_words', 1):
#                 continue
            
#             # Check if any keywords match
#             if any(keyword in query for keyword in config['keywords']):
#                 return tool_name
        
#         # 4. Default: just chat
#         return 'chat'

class IntentRouter:
    """
    LangChain-based intent router using LLM classification.
    """
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm  # Your OllamaLLM instance
        
        # Define destinations
        self.destinations = """
chat: Use for general conversation, follow-up questions, and clarifications about previous responses
search_codebase: Use when user wants to investigate NEW code, find bugs, understand implementation, or analyze errors
"""
        
        # Router prompt
        ROUTER_TEMPLATE = """Given a user question and conversation history, determine which action to take.

Destinations:
{destinations}

Rules:
- If user is asking about something you previously said (e.g., "what files?", "explain that"), choose 'chat'
- If user wants to investigate NEW code or bugs, choose 'search_codebase'
- If uncertain, choose 'chat'
- Only choose 'search_codebase' if the user is asking to investigate new code,
  find bugs, or analyze implementation.
- For any conversational follow-ups about previous answers, explanations,
  clarifications, or questions about the files I already used, choose 'chat'.

User question: {input}
Recent conversation: {conversation_context}

Return ONLY the destination name (either 'chat' or 'search_codebase'):"""
        
        self.router_prompt = PromptTemplate(
            template=ROUTER_TEMPLATE,
            input_variables=["input", "conversation_context"],
            partial_variables={"destinations": self.destinations}
        )
    
    def route(self, user_input: str, conversation_context: str = "") -> Literal['chat', 'search_codebase']:
        """
        Route using LLM classification.
        
        Args:
            user_input: User's question
            conversation_context: Recent conversation history
        
        Returns:
            'chat' or 'search_codebase'
        """
        try:
            # Format the prompt
            prompt_text = self.router_prompt.format(
                input=user_input,
                conversation_context=conversation_context[:500]
            )
            
            # Use your OllamaLLM to classify
            messages = [Message(role="user", content=prompt_text)]
            
            # Get classification (short response)
            result = self.llm.chat(messages, max_tokens=10, temperature=0.0)
            
            # Parse result
            intent = result.strip().lower()
            
            print(f"[DEBUG] Router raw response: '{result}'", flush=True)
            
            # Determine intent
            if intent == 'search_codebase':
                return 'search_codebase'
            else:
                return 'chat'
                
        except Exception as e:
            print(f"[DEBUG] Router error: {e}, defaulting to chat", flush=True)
            return 'chat'

class SessionAgent:
    """
    Simple chat interface with conversation history.
    
    Just talks to the LLM - no code search, no tools
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        vector_store: VectorStore,  # Keep for future use
        project_root: Path,
    ):
        self.llm = llm
        self.vector_store = vector_store
        self.project_root = project_root
        self.search_codebase = create_search_tool(vector_store, top_k=6)
        self.router = IntentRouter(llm)

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages= True, # Return as string, not Message objects
            input_key="input",
            output_key="output"
        )        
        # System prompt
        self.system_prompt = """You are a helpful debugging assistant.

You help developers with:
- Understanding bugs and errors
- Explaining code concepts
- Suggesting approaches to problems

Be friendly, concise, and helpful."""
        self.code_system_prompt = """You are a debugging assistant analyzing code.

You have been provided with relevant code from the codebase.
Analyze it carefully and answer the user's question.

Always:
- Cite specific file names and line numbers
- Explain what the code does
- Point out potential issues
- Suggest fixes if applicable"""

    def _build_messages_with_history(self, system_prompt: str) -> List[Message]:
        messages = [Message(role="system", content=system_prompt)]
        
        # Load history as structured messages
        memory_vars = self.memory.load_memory_variables({})
        chat_history = memory_vars.get("chat_history", [])
        
        if chat_history:
            for msg in chat_history:
                # Normalize to your Message class
                if isinstance(msg, Message):
                    messages.append(msg)
                elif hasattr(msg, "role") and hasattr(msg, "content"):
                    messages.append(Message(role=msg.role, content=msg.content))
                elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(Message(role=msg["role"], content=msg["content"]))
                else:
                    # fallback: treat as user text
                    messages.append(Message(role="user", content=str(msg)))
        
        return messages
    def prepare_messages(self, user_input: str) -> dict:
        """
        Prepare messages for streaming (does routing + code search).
        Does NOT call LLM - returns messages ready for streaming.
        
        Returns:
            dict with 'messages' and 'intermediate_steps'
        """
        try:
            # Route the intent
            intent = self.router.route(user_input)
            print(f"\n[DEBUG] Intent: {intent}", flush=True)
            
            intermediate_steps = []
            
            if intent == 'search_codebase':
                intermediate_steps.append(('routing', f'Detected code question, searching codebase...'))
                # CODE MODE: Search code
                intermediate_steps.append(('search_codebase', f'Searching: {user_input[:50]}...'))
                
                # Call the search function
                 # 2. Index project
                from ..rag.indexer import index_project
                

                intermediate_steps.append(
                    ("indexing", "Ensuring project index is up to date...")
                )
                index_project(self.project_root, verbose=False)
                intermediate_steps.append(
                    ("indexing", "Index ready")
                )
                results = self.vector_store.search(user_input, top_k=6)                
                # Extract file info from results
                if results:
                    intermediate_steps.append(('search_codebase', f'Found {len(results)} relevant code sections'))
                    
                    # Extract file info for intermediate steps
                    for result in results:
                        meta = result.get('metadata', {})
                        file = meta.get('file', 'unknown')
                        lines = f"{meta.get('line_start', '?')}-{meta.get('line_end', '?')}"
                        func = meta.get('function_name', '')
                        
                        if func:
                            file_info = f"{file}::{func} (lines {lines})"
                        else:
                            file_info = f"{file} (lines {lines})"
                        
                        intermediate_steps.append(('file_checked', file_info))
                    
                    # Format results for LLM (same format as the tool)
                    formatted = [f"Found {len(results)} relevant code chunks:\n"]
                    
                    for i, result in enumerate(results, 1):
                        meta = result.get("metadata", {})
                        file = meta.get('file', 'unknown')
                        lines = f"{meta.get('line_start', '?')}-{meta.get('line_end', '?')}"
                        
                        formatted.append(f"\n--- Result {i} ---")
                        formatted.append(f"File: {file}")
                        formatted.append(f"Lines: {lines}")
                        
                        fn = meta.get("function_name")
                        if fn:
                            formatted.append(f"Function: {fn}")
                        
                        formatted.append(f"\n**Section {i}** - `{file}` (lines {lines})")
                        formatted.append("\nCode:\n```")
                        formatted.append(result["text"].strip())
                        formatted.append("```")
                    
                    code_results = "\n".join(formatted)
                else:
                    intermediate_steps.append(('search_codebase', 'No relevant code found'))
                    code_results = "No relevant code found in the codebase."

                print(f"[DEBUG] Found code, length: {len(code_results)}\n", flush=True)
                # Build messages with code context
                messages = self._build_messages_with_history(self.code_system_prompt)
                
                # Add query with code context
                user_message = f"""Question: {user_input}

    Relevant code from the codebase:
    {code_results}

    Based on the code above, analyze and answer the user's question. Reference specific files and line numbers."""
                
                messages.append(Message(role="user", content=user_message))
            
            else:
                # CHAT MODE: Just talk
                print(f"[DEBUG] Chat mode\n", flush=True)
                messages = self._build_messages_with_history(self.system_prompt)
                messages.append(Message(role="user", content=user_input))
            
            return {
                'messages': messages,
                'intermediate_steps': intermediate_steps
            }
            
        except Exception as e:
            import traceback
            print(f"[DEBUG] Exception: {traceback.format_exc()}", flush=True)
            return {
                'messages': [],
                'intermediate_steps': []
            }

    def clear_memory(self):
        """Clear conversation history."""
        self.memory.clear()
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history."""
        try:
            memory_vars = self.memory.load_memory_variables({})
            return memory_vars.get("chat_history", "No history")
        except:
            return "No history available"