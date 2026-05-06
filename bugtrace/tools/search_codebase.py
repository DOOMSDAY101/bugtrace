"""
Search Codebase Tool for LangChain Agent.

Wraps the RAG vector store search functionality.
"""

from langchain.tools import tool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bugtrace.rag.vector_store import VectorStore

def create_search_tool(vector_store: "VectorStore", top_k: int = 3):
    retriever = vector_store.as_retriever(k=top_k)

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
            Formatted code chunks with file names, line numbers, and content
        """

        query = (query or "").strip()
        if not query:
            return "⚠️ Empty query received. Skipping code search."
        
        results = retriever.invoke(query)

        if not results:
            return f"No relevant code found for query: '{query}'"
        
        formatted = [f"Found {len(results)} relevant code chunks:\n"]

        for i, result in enumerate(results, 1):
            meta = getattr(result, "metadata", {}) or {}
            file = meta.get('file', 'unknown')
            lines = f"{meta.get('line_start', '?')}-{meta.get('line_end', '?')}"
            func = meta.get("function_name")
            
            formatted.append(f"\n{'='*60}")
            formatted.append(f"Result {i}/{len(results)}")
            formatted.append(f"{'='*60}")
            line_start = meta.get("line_start", "?")

            formatted.append(f"File: {file}:{line_start} (Lines {lines})")
            formatted.append(f"Lines: {lines}")
            
            if func:
                formatted.append(f"Function: {func}")
            
            formatted.append(f"\nCode:")
            formatted.append("```")
            formatted.append(result.page_content.strip())
            formatted.append("```")
        
        return "\n".join(formatted)

    return search_codebase