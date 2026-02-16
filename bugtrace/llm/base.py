from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any,List
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str  # "ollama", "openai", "anthropic"
    model: str
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None


@dataclass
class Message:
    """Chat message."""
    role: str  # "system", "user", "assistant"
    content: str

class BaseLLM(ABC):
    """
    Abstract base class for LLM providers.
    
    All providers must implement:
    - chat() for single response
    - chat_stream() for streaming response
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = config.model
        self.temperature = config.temperature
        self.provider = config.provider
        self.max_tokens = config.max_tokens

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
         **kwargs
    ) -> str:
        """
        Send chat messages and get response.
        
        Args:
            messages: List of Message objects
            **kwargs: Provider-specific options
        
        Returns:
            Complete response text
        """
        pass

    @abstractmethod
    def chat_stream(
        self,
        messages: list[Message],
        **kwargs
    ) -> Iterator[str]:
        """
        Send chat messages and stream response.
        
        Args:
            messages: List of Message objects
            **kwargs: Provider-specific options
        
        Yields:
            Response tokens as they're generated
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available/accessible."""
        pass
    
    def _prepare_messages(self, messages: list[Message]) -> Any:
        """
        Convert Message objects to provider-specific format.
        Override in subclasses if needed.
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def get_langchain_llm(self):
        """
        Get LangChain-compatible LLM wrapper.
        
        Returns:
            LangChain LLM instance for use with agents/chains
        """
        from .langchain_wrapper import get_langchain_llm
        return get_langchain_llm(self)

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the model being used.
        
        Returns:
            Model name string (e.g., 'llama3.2:3b')
        """
        pass

class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMConnectionError(LLMError):
    """Provider connection failed."""
    pass


class LLMModelNotFoundError(LLMError):
    """Model not found or not available."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass