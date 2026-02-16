"""
Search Codebase Tool for LangChain Agent.

Wraps the RAG vector store search functionality.
"""

from langchain.tools import tool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bugtrace.rag.vector_store import VectorStore


@tool
def search_codebase(query: str) -> str:
    """
    Search the codebase for relevant code chunks based on a description.
    
    Use this tool when you need to find code related to:
    - Specific functions or classes
    - Features or functionality
    - Error messages or bugs
    - Code patterns
    
    Args:
        query: Natural language description of what code to find.
               Examples: "login authentication", "password hashing", 
               "database connection error handling"
    
    Returns:
        Formatted string with relevant code chunks including file paths,
        line numbers, and code snippets.
    """
    # This will be injected at runtime by the agent
    # See session_agent.py for implementation
    raise NotImplementedError("This tool must be bound to a vector store instance")


def create_search_tool(vector_store: 'VectorStore', top_k: int = 6):
    """
    Create a search_codebase tool bound to a specific vector store.
    
    Args:
        vector_store: VectorStore instance to search
        top_k: Number of results to return
    
    Returns:
        Configured search tool
    """
    @tool
    def search_codebase_impl(query: str) -> str:
        """
        Search the codebase for relevant code chunks based on a description.
        
        Use this tool when you need to find code related to:
        - Specific functions or classes
        - Features or functionality
        - Error messages or bugs
        - Code patterns
        
        Args:
            query: Natural language description of what code to find.
                   Examples: "login authentication", "password hashing", 
                   "database connection error handling"
        
        Returns:
            Formatted string with relevant code chunks including file paths,
            line numbers, and code snippets.
        """
        # Search vector store
        results = vector_store.search(query, top_k=top_k)
        
        if not results:
            return f"No relevant code found for query: '{query}'"
        
        # Format results
        formatted_results = []
        formatted_results.append(f"Found {len(results)} relevant code chunks:\n")
        
        for idx, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            file_path = metadata.get('file', 'unknown')
            line_start = metadata.get('line_start', '?')
            line_end = metadata.get('line_end', '?')
            function_name = metadata.get('function_name', 'unknown')
            
            formatted_results.append(f"\n--- Result {idx} ---")
            formatted_results.append(f"File: {file_path}")
            formatted_results.append(f"Lines: {line_start}-{line_end}")
            
            if function_name and function_name != 'unknown':
                formatted_results.append(f"Function: {function_name}")
            
            formatted_results.append(f"\nCode:")
            formatted_results.append("```")
            formatted_results.append(result['text'].strip())
            formatted_results.append("```")
        
        return "\n".join(formatted_results)
    
    # Rename to match the base tool
    search_codebase_impl.name = "search_codebase"
    
    return search_codebase_impl