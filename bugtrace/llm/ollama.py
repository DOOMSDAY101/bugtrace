from typing import List, Dict, Optional, Iterator
import ollama
from .base import BaseLLM, LLMConfig, Message, LLMConnectionError, LLMModelNotFoundError



class OllamaLLM(BaseLLM):
    """
    Ollama provider implementation.
    
    Example usage:
        config = LLMConfig(provider="ollama", model="llama3.2:3b")
        llm = OllamaLLM(config)
        
        # Regular chat
        response = llm.chat([
            Message(role="system", content="You are a debugger"),
            Message(role="user", content="What's wrong with this code?")
        ])
        
        # Streaming chat
        for token in llm.chat_stream(messages):
            print(token, end="")
    """
    
    # def __init__(self, model: str = "llama3.2:3b", temperature: float = 0.2):
    def __init__(self, config: LLMConfig):
        """
        Initialize Ollama LLM.
        
        Args:
            model: Model name (e.g., 'llama3.2:3b', 'llama3.1:8b')
            temperature: Default temperature for generation
        """
        # self.model = model
        # self.default_temperature = temperature
        self.config = config
        self.model = config.model
        self.temperature = config.temperature
        self.provider = config.provider
        self.max_tokens = config.max_tokens 
        
        # Test connection
        try:
            # Simple test to verify model is available
            ollama.chat(
                model=config.model,
                messages=[{"role": "user", "content": "test"}],
                options={"num_predict": 1}  # Only generate 1 token for test
            )
        except Exception as e:
            raise LLMConnectionError(
                f"Failed to connect to Ollama with model '{self.model}'. "
                f"Make sure Ollama is running and the model is pulled.\n"
                f"Run: ollama pull {self.model}\n"
                f"Error: {e}"
            ) from e
    
    def chat(
        self,
        messages: List[Message],
        **kwargs
    ) -> str:
        """
        Generate a chat completion using Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            String response from the model
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=self._prepare_messages(messages),
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens or -1,
                    **kwargs,
                },
            )

            return response["message"]["content"]
            
        except Exception as e:
            msg = str(e).lower()
            if "not found" in msg:
                raise LLMModelNotFoundError(
                    f"Model '{self.model}' not found. "
                    f"Pull it with: ollama pull {self.model}"
                ) from e

            raise LLMConnectionError(
                f"Ollama chat failed. Is Ollama running? Error: {e}"
            ) from e
    
    def chat_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """
        Stream chat response token-by-token.
        """
        try:
            stream = ollama.chat(
                model=self.model,
                messages=self._prepare_messages(messages),
                stream=True,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens or -1,
                    **kwargs,
                },
            )

            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except Exception as e:
            msg = str(e).lower()
            if "not found" in msg:
                raise LLMModelNotFoundError(
                    f"Model '{self.model}' not found. "
                    f"Pull it with: ollama pull {self.model}"
                ) from e

            raise LLMConnectionError(
                f"Ollama streaming failed. Is Ollama running? Error: {e}"
            ) from e
        
    def is_available(self) -> bool:
        """Check if Ollama is running and model exists."""
        try:
            models = ollama.list()
            model_names = [m["name"] for m in models.get("models", [])]
            return any(self.model in name for name in model_names)
        except Exception:
            return False
        

    def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = ollama.list()
            return [m["name"] for m in response.get("models", [])]
        except Exception:
            return []

    def pull_model(self, model: str | None = None) -> bool:
        """Pull a model from Ollama."""
        try:
            ollama.pull(model or self.model)
            return True
        except Exception:
            return False
    def get_model_name(self) -> str:
        """Get the model name"""
        return self.model