from bugtrace.rag.embeddings.base import BaseEmbedder
from bugtrace.rag.embeddings.ollama import OllamaEmbedder

def get_embedder(config: dict) -> BaseEmbedder:
    """
    Factory function to create embedder.
    Always uses Ollama for now, but designed for easy extension.
    
    Args:
        config: User's bugtrace.yaml config
        
    Returns:
        BaseEmbedder instance
    """
    llm_provider = config.get('llm', {}).get('provider', 'ollama')
    

    if llm_provider == 'ollama':
        return OllamaEmbedder(llm_provider)
    # elif provider == 'openai':
    #     return OpenAIEmbedder(model)
    # elif provider == 'anthropic':
    #     return AnthropicEmbedder(model)
    else:
        raise ValueError(f"Unsupported provider: {llm_provider}")

__all__ = ['BaseEmbedder', 'OllamaEmbedder', 'get_embedder']