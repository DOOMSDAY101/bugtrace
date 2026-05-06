from .base import LLMError, LLMConnectionError
from langchain_ollama import ChatOllama

def get_llm(config):
    llm_cfg = config["llm"]

    provider = llm_cfg["provider"]
    model = llm_cfg["model"]
    temperature = llm_cfg.get("temperature", 0.2)

    if provider == "ollama":
        return ChatOllama(
            model=model,
            temperature=temperature,
            streaming=True
        )

    raise ValueError(f"Unsupported provider: {provider}")
    
__all__ = [
    "OllamaLLM",
    "get_llm",
    "LLMConnectionError",
    "LLMModelNotFoundError",
]
