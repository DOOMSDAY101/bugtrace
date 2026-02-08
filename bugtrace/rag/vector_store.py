# bugtrace/rag/vector_store.py
from pathlib import Path
from typing import List, Dict
from langchain_chroma import Chroma 
import hashlib

class VectorStore:
    """ChromaDB wrapper for storing code embeddings"""
    
    def __init__(self, index_dir: Path, project_root: Path, embedder):
        """
        Initialize ChromaDB vector store with auto-generated collection name.
        
        Args:
            index_dir: Directory to store ChromaDB data (.bugtrace/index)
            project_root: Project root path (used for collection naming)
        """
        self.index_dir = index_dir
        self.project_root = project_root
        self.embedder = embedder

        # Generate unique collection name
        self.collection_name = self._generate_collection_name()
        project_name = project_root.name
        self.persist_dir = index_dir / self.collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            self.vector_store = Chroma(
                collection_name="default",
                embedding_function=embedder,  # Works because embedder has embed_documents/embed_query
                persist_directory=str(self.persist_dir),
                collection_metadata={"hnsw:space": "cosine",
                                    "project_root": str(project_root)
                                    }
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}")
        
    def _generate_collection_name(self) -> str:
        """
        Generate unique collection name based on project.
        Format: projectname_<hash>
        
        Returns:
            Unique collection name
        """
        # Get project name from directory
        project_name = self.project_root.name.lower()
        
        # Clean project name (remove special chars)
        project_name = ''.join(c if c.isalnum() else '_' for c in project_name)
        
        # Create hash from project path for uniqueness
        path_hash = hashlib.md5(str(self.project_root).encode()).hexdigest()[:8]
        
        # Combine: projectname_hash
        collection_name = f"{project_name}_{path_hash}"
        
        return collection_name
    
    def add_chunks(self, chunks: List[Dict], embeddings_list: List[List[float]]):
        """
        Store chunks with their embeddings in ChromaDB.
        
        Args:
            chunks: List of chunk dicts with 'text' and 'metadata'
        """
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        ids = []
        texts = [chunk['text'] for chunk in chunks]
        metadatas = []
        
        for chunk in chunks:
            chunk_id = f"{chunk['metadata']['file']}_{chunk['metadata']['chunk_id']}"
            chunk_id_hash = hashlib.md5(chunk_id.encode()).hexdigest()
            ids.append(chunk_id_hash)
            
            clean_metadata = {
                k: str(v) if not isinstance(v, bool) else v
                for k, v in chunk['metadata'].items()
                if v is not None and not isinstance(v, (list, dict))
            }
            metadatas.append(clean_metadata)
        
        self.vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings_list
        )
    
    def delete_file_chunks(self, filepath: str):
        """
        Delete all chunks from a specific file.
        Used when file is removed or changed.
        
        Args:
            filepath: Path to file whose chunks should be deleted
        """
        filepath = str(Path(filepath).resolve())
        # Query all chunks from this file
        try:
            all_data = self.vector_store.get()
            ids_to_delete = [
                all_data['ids'][i]
                for i, metadata in enumerate(all_data['metadatas'])
                if metadata.get('file') == filepath
            ]
            if ids_to_delete:
                self.vector_store.delete(ids=ids_to_delete)
        except Exception:
            pass
    
    def search(self, query: str, top_k: int = 6) -> List[Dict]:
        """
        Search for similar chunks.
        Chroma automatically uses embedder.embed_query() internally.
        """
        results = self.vector_store.similarity_search_with_score(query=query, k=top_k)
        
        return [
            {
                'text': doc.page_content,
                'metadata': doc.metadata,
                'score': score
            }
            for doc, score in results
        ]
    
    
    def get_stats(self) -> Dict:
        """Get statistics"""
        try:
            count = len(self.vector_store.get()['ids'])
        except:
            count = 0
        
        return {
            'collection_name': self.collection_name,
            'total_chunks': count,
            'index_dir': str(self.index_dir)
        }