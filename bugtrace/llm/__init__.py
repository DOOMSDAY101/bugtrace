from .base import BaseLLM, LLMConfig, Message, LLMError, LLMConnectionError, LLMModelNotFoundError
from .ollama import OllamaLLM


def get_llm(config: dict) -> BaseLLM:
    """
    Factory function to get appropriate LLM based on config.
    
    Args:
        config: User configuration dict from bugtrace.yaml
        
    Returns:
        Initialized LLM instance
        
    Raises:
        ValueError: If provider is not supported
    """
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "ollama")
    model = llm_config.get("model", "llama3.2:3b")
    temperature = llm_config.get("temperature", 0.2)
    max_tokens =llm_config.get("max_tokens")  
    
    llm_config_obj = LLMConfig(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

    if provider == "ollama":
        # return OllamaLLM(provider=provider,model=model, temperature=temperature)
        return OllamaLLM(llm_config_obj)
    # elif provider == "openai":
    #     return OpenAILLM(model=model, temperature=temperature)
    # elif provider == "anthropic":
    #     return AnthropicLLM(model=model, temperature=temperature)
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Supported providers: ollama"
        )
    
__all__ = [
    "BaseLLM",
    "LLMConfig",
    "Message",
    "LLMError",
    "LLMConnectionError",
    "LLMModelNotFoundError",
    "OllamaLLM",
]
