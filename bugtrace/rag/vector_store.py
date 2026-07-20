from pathlib import Path
from typing import List, Dict
from langchain_chroma import Chroma 
import hashlib
from bugtrace.rag.bm25_store import BM25Store

class VectorStore:
    """ChromaDB wrapper for storing code embeddings"""
    
    def __init__(self, index_dir: Path, project_root: Path, embedder,collection_name=None):
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
        if collection_name:
            self.collection_name = collection_name
        else:
            self.collection_name = self._generate_collection_name()
        project_name = project_root.name
        self.persist_dir = index_dir / self.collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize BM25 Store for hybrid search
        self.bm25_store = BM25Store(
            self.persist_dir / "bm25"
        )

        # self.reranker = Reranker()
        
        # Initialize ChromaDB client
        try:
            self.vector_store = Chroma(
                collection_name=self.collection_name,
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
        self.bm25_store.add_chunks(chunks)
    
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
            self.bm25_store.delete_file_chunks(filepath)
        except Exception:
            pass
        
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

    def search(self, query: str, top_k: int = 5, retrieval_k: int = 15):
        """
        Hybrid retrieval:
        - semantic search
        - BM25 keyword search
        """

        semantic_results = self.vector_store.similarity_search_with_score(
            query=query,
            k=retrieval_k
        )

        semantic = []

        for doc, score in semantic_results:
            normalized_score = 1 / (1 + score)
            semantic.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": float(normalized_score),
                "semantic_score": float(normalized_score),
                "bm25_score": None,
                "rerank_score": None,
                "source": "semantic"
            })

        keyword = self.bm25_store.search(
            query=query,
            k=retrieval_k
        )

        # Merge + deduplicate
        combined = {}

        for item in semantic + keyword:
            key = (
                item["metadata"].get("file"),
                str(item["metadata"].get("chunk_id"))
            )

            if key not in combined:
                combined[key] = item
            else:
                # keep better score
                existing = combined[key]

                if item.get("bm25_score") is not None:
                    existing["bm25_score"] = item["bm25_score"]

                if item.get("semantic_score") is not None:
                    existing["semantic_score"] = item["semantic_score"]
                
                # only call hybrid when both contributed
                if (
                    existing.get("bm25_score") is not None
                    and existing.get("semantic_score") is not None
                ):
                    existing["source"] = "hybrid"

        merged = list(combined.values())

        
        # for item in reranked:
        for item in merged:
            bm25 = item.get("bm25_score") or 0.0
            semantic = item.get("semantic_score") or 0.0

            final = (
                0.5 * bm25 +
                0.5 * semantic
            )

            if item["source"] == "hybrid":
                final += 0.05

            item["final_score"] = final
            item["score"] = final

            item["score_breakdown"] = {
                "bm25": bm25,
                "semantic": semantic,
                "final": final
            }

        merged.sort(
            key=lambda x: x["final_score"],
            reverse=True
        )

        return merged[:top_k]


    
    
    # def as_retriever(self, k: int = 3):
    #     return self.vector_store.as_retriever(
    #         search_type="similarity",
    #         search_kwargs={"k": k}
    #     )
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

    @property
    def bm25(self):
        return self.bm25_store