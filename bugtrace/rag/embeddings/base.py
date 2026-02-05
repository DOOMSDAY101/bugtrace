from abc import ABC, abstractmethod
from typing import List

class BaseEmbedder(ABC):
    """Abstract base class for all embedding implementations"""
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Integer dimension (e.g., 768 for nomic-embed-text)
        """
        pass