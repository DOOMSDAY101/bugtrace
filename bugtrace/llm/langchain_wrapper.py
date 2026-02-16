"""
LangChain wrapper for Bugtrace LLMs.

Provides compatibility layer between Bugtrace LLMs and LangChain.
"""


from typing import TYPE_CHECKING
from langchain_ollama import ChatOllama


if TYPE_CHECKING:
    from ..llm.base import BaseLLM


def get_langchain_llm(llm: 'BaseLLM'):
    """
    Get LangChain-compatible LLM wrapper.
    
    Args:
        llm: Bugtrace LLM instance
    
    Returns:
        LangChain LLM instance
    """
    if llm.config.provider == "ollama":
        return ChatOllama( 
            model=llm.model,
            temperature=llm.temperature,)

    else:
        raise NotImplementedError(f"LangChain wrapper not implemented for {llm.config.provider}")