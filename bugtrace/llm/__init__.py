from .base import LLMError, LLMConnectionError
from langchain_ollama import ChatOllama
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

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
    
    elif provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            streaming=True,
            base_url="https://models.inference.ai.azure.com",
            api_key=os.getenv("OPENAI_API_KEY") 
        )

    raise ValueError(f"Unsupported provider: {provider}")
    
__all__ = [
    "OllamaLLM",
    "get_llm",
    "LLMConnectionError",
    "LLMModelNotFoundError",
]
