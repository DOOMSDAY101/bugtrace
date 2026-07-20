"""
Search Codebase Tool for LangChain Agent.

Wraps the RAG vector store search functionality.
"""

from langchain.tools import tool
from typing import TYPE_CHECKING, List, Dict, Any
import json

if TYPE_CHECKING:
    from bugtrace.rag.vector_store import VectorStore

def create_search_tool(vector_store: "VectorStore", top_k: int = 5):

    @tool("search_codebase")
    def search_codebase(query: str) -> str:
        """
        Search the codebase for relevant code chunks.
        
        Use this tool when you need to find:
        - Functions, classes, or methods
        - Bug locations or error-prone code
        - Implementation details
        - Specific features or flows
        - DO NOT use tools for greetings, casual chat, or non-technical input.
        Args:
            query: Search query describing what code you're looking for
            
        Returns:
            JSON string containing structured code chunks
        """

        query = (query or "").strip()
        if not query:
            # return "⚠️ Empty query received. Skipping code search."
            return json.dumps({
                "error": "Empty query received",
                "results": []
            })
        
        results = vector_store.search(query=query,top_k=top_k)


        if not results:
            # return f"No relevant code found for query: '{query}'"
            return json.dumps({
                "query": query,
                "count": 0,
                "results": []
            })
        
        
        structured_results: List[Dict[str, Any]] = []


        for result in results:
            # meta = getattr(result, "metadata", {}) or {}
            meta = result.get("metadata", {})

            structured_results.append({
                "file": meta.get("file", "unknown"),
                "line_start": meta.get("line_start", None),
                "line_end": meta.get("line_end", None),
                "function": meta.get("function_name", None),
                "code": result.get("text", "").strip(),
                "score": result.get("score", 0.0),
                "source": result.get("source", "hybrid")
            })

        return json.dumps({
            "query": query,
            "count": len(structured_results),
            "results": structured_results
        }, indent=2)

    return search_codebase
