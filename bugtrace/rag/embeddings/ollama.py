from typing import List
import math
import ollama
from bugtrace.rag.embeddings.base import BaseEmbedder

class OllamaEmbedder(BaseEmbedder):
    """Ollama embedding implementation"""
    
    # Default embedding models for different LLM providers
    DEFAULT_MODELS = {
        'ollama': 'nomic-embed-text',
    }
    
    def __init__(self, llm_provider: str = 'ollama'):
        """
        Initialize Ollama embedder with auto-selected model.
        
        Args:
            llm_provider: The LLM provider from config (used to pick embedding model)
        """
        self.model = self.DEFAULT_MODELS.get(llm_provider, 'nomic-embed-text')
        self._dimension = None
        
        # Test connection and get dimension
        try:
            test_result = ollama.embeddings(model=self.model, prompt="test")
            self._dimension = len(test_result["embedding"])
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to Ollama with model '{self.model}'. "
                f"Make sure Ollama is running and the model is pulled.\n"
                f"Run: ollama pull {self.model}\n"
                f"Error: {e}"
            )
    
    def _normalize(self, vec: List[float]) -> List[float]:
        """Normalize vector to unit length for better similarity search"""
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            return vec
        return [x / norm for x in vec]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        if not texts:
            return []
        
        embeddings = []
        for text in texts:
            if not text or not text.strip():
                # Return zero vector for empty text
                embeddings.append([0.0] * self._dimension)
                continue
            
            result = ollama.embeddings(model=self.model, prompt=text)
            embeddings.append(self._normalize(result["embedding"]))
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension
    
    # LangChain interface (for Chroma compatibility)
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """LangChain interface - just calls our embed_texts"""
        return self.embed_texts(texts)
    
    def embed_query(self, text: str) -> List[float]:
        result = ollama.embeddings(model=self.model, prompt=text)
        return self._normalize(result["embedding"])