from pathlib import Path
from typing import Optional, List, Dict

from ..llm.base import BaseLLM, Message
from ..rag.vector_store import VectorStore


class SessionAgent:
    """
    Simple chat interface with conversation history.
    
    Just talks to the LLM - no code search, no tools.
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        vector_store: VectorStore,  # Keep for future use
        project_root: Path,
        initial_query: Optional[str] = None
    ):
        self.llm = llm
        self.vector_store = vector_store
        self.project_root = project_root
        
        # Simple conversation history
        self.history: List[Dict[str, str]] = []
        
        # System prompt
        self.system_prompt = """You are a helpful debugging assistant.

You help developers with:
- Understanding bugs and errors
- Explaining code concepts
- Suggesting approaches to problems

Be friendly, concise, and helpful."""
    
    def chat(self, user_input: str) -> dict:
        """
        Chat with the LLM.
        
        Args:
            user_input: User's message
        
        Returns:
            dict with 'output' (response) and 'intermediate_steps' (empty list)
        """
        try:
            # Build messages with history
            messages = [Message(role="system", content=self.system_prompt)]
            
            # Add conversation history (last 5 exchanges)
            for entry in self.history[-5:]:
                messages.append(Message(role="user", content=entry['user']))
                messages.append(Message(role="assistant", content=entry['assistant']))
            
            # Add current message
            messages.append(Message(role="user", content=user_input))
            
            # Get LLM response
            response = self.llm.chat(messages)
            
            # Save to history
            self.history.append({
                'user': user_input,
                'assistant': response
            })
            
            return {
                'output': response,
                'intermediate_steps': []
            }
            
        except Exception as e:
            return {
                'output': f"Error: {str(e)}",
                'intermediate_steps': []
            }