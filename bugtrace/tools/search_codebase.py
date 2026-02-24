"""
Search Codebase Tool for LangChain Agent.

Wraps the RAG vector store search functionality.
"""

from langchain.tools import tool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bugtrace.rag.vector_store import VectorStore


def create_search_tool(vector_store: "VectorStore", top_k: int = 6):
    @tool("search_codebase")
    def search_codebase(query: str) -> str:
        """
        Search the codebase for relevant code chunks.

        Use this tool when you need to find:
        - functions or classes
        - features or flows
        - bugs or error messages
        """

        results = vector_store.search(query, top_k=top_k)

        if not results:
            return f"No relevant code found for query: '{query}'"

        formatted = [f"Found {len(results)} relevant code chunks:\n"]

        for i, result in enumerate(results, 1):
            meta = result.get("metadata", {})
            file = meta.get('file', 'unknown')
            lines = f"{meta.get('line_start', '?')}-{meta.get('line_end', '?')}"

            formatted.append(f"\n--- Result {i} ---")
            formatted.append(f"File: {meta.get('file', 'unknown')}")
            formatted.append(
                f"Lines: {meta.get('line_start', '?')}-{meta.get('line_end', '?')}"
            )

            fn = meta.get("function_name")
            if fn:
                formatted.append(f"Function: {fn}")
            formatted.append(f"\n**Section {i}** - `{file}` (lines {lines})")

            formatted.append("\nCode:\n```")
            formatted.append(result["text"].strip())
            formatted.append("```")

        return "\n".join(formatted)

    return search_codebase