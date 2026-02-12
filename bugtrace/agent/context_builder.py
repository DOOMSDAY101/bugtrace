"""
Context Builder Agent.

Transforms RAG search results into structured context for LLM.
"""

from typing import List, Dict, Any
from pathlib import Path
from ..report.status import get_reporter


class ContextBuilder:
    """
    Prepares code context for LLM analysis.
    
    Takes raw search results from RAG and structures them into
    LLM-friendly format with metadata.
    
    Usage:
        builder = ContextBuilder()
        context = builder.build_context(
            query="login fails",
            search_results=[...]
        )
    """
    
    def __init__(self):
        self.reporter = get_reporter()
    
    def build_context(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        max_chunks: int = 6
    ) -> Dict[str, Any]:
        """
        Build structured context from search results.
        
        Args:
            query: User's bug description
            search_results: List of chunks from RAG search
            max_chunks: Maximum chunks to include
        
        Returns:
            Structured context dict:
            {
                "query": "user's question",
                "code_snippets": [
                    {
                        "file": "path/to/file.py",
                        "file_name": "file.py",
                        "lines": "45-62",
                        "code": "actual code",
                        "function": "function_name",
                        "metadata": {...}
                    }
                ],
                "summary": {
                    "total_files": 3,
                    "total_chunks": 6,
                    "languages": ["python"]
                }
            }
        """
        with self.reporter.section("Building context for AI"):
            # Limit results
            limited_results = search_results[:max_chunks]
            
            # Structure snippets
            snippets = []
            files_seen = set()
            
            for result in limited_results:
                snippet = self._structure_snippet(result)
                snippets.append(snippet)
                files_seen.add(snippet["file"])
            
            # Build summary
            summary = self._build_summary(snippets, files_seen)
            
            # Report what was built
            self.reporter.success(f"Structured {len(snippets)} code snippets")
            self.reporter.info(f"From {summary['total_files']} files")
            
            # List files
            for file in sorted(files_seen):
                self.reporter.info(f"  • {file}")
            
            context = {
                "query": query,
                "code_snippets": snippets,
                "summary": summary
            }
            
            return context
    
    def _structure_snippet(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure a single search result into snippet format.
        
        Args:
            result: Raw search result from RAG
        
        Returns:
            Structured snippet with metadata
        """
        metadata = result.get("metadata", {})
        
        # Extract key fields
        file_path = metadata.get("file", "unknown")
        file_name = Path(file_path).name
        
        snippet = {
            "file": file_path,
            "file_name": file_name,
            "code": result.get("text", ""),
            "metadata": {}
        }
        
        # Add optional metadata fields
        optional_fields = [
            "line_start",
            "line_end",
            "function_name",
            "chunk_id",
            "file_type",
            "has_error_handling",
            "has_logging",
            "has_todo"
        ]
        
        for field in optional_fields:
            if field in metadata:
                snippet["metadata"][field] = metadata[field]
        
        # Build line range if available
        if "line_start" in metadata and "line_end" in metadata:
            snippet["lines"] = f"{metadata['line_start']}-{metadata['line_end']}"
        
        # Add function name at top level if available
        if "function_name" in metadata:
            snippet["function"] = metadata["function_name"]
        
        return snippet
    
    def _build_summary(
        self,
        snippets: List[Dict[str, Any]],
        files: set
    ) -> Dict[str, Any]:
        """Build summary statistics about the context."""
        # Extract languages
        languages = set()
        for snippet in snippets:
            file_type = snippet["metadata"].get("file_type")
            if file_type:
                languages.add(file_type)
        
        return {
            "total_files": len(files),
            "total_chunks": len(snippets),
            "languages": sorted(list(languages))
        }
    
    def format_snippet_for_prompt(self, snippet: Dict[str, Any]) -> str:
        """
        Format a single snippet for inclusion in LLM prompt.
        
        Args:
            snippet: Structured snippet
        
        Returns:
            Formatted text for prompt
        """
        lines = []
        
        # Header
        lines.append("---")
        lines.append(f"File: {snippet['file']}")
        
        if "lines" in snippet:
            lines.append(f"Lines: {snippet['lines']}")
        
        if "function" in snippet:
            lines.append(f"Function: {snippet['function']}")
        
        # Metadata flags
        metadata = snippet.get("metadata", {})
        if metadata:
            flags = []
            if metadata.get("has_error_handling") is False:
                flags.append("No error handling")
            if metadata.get("has_logging") is False:
                flags.append("No logging")
            if metadata.get("has_todo"):
                flags.append("Has TODO")
            
            if flags:
                lines.append(f"Notes: {', '.join(flags)}")
        
        # Code
        lines.append("")
        lines.append("Code:")
        lines.append("```" + snippet.get("metadata", {}).get("file_type", ""))
        lines.append(snippet["code"].strip())
        lines.append("```")
        
        return "\n".join(lines)
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format entire context for LLM prompt.
        
        Args:
            context: Full context from build_context()
        
        Returns:
            Formatted text for prompt
        """
        lines = []
        
        # Summary
        summary = context["summary"]
        lines.append(f"Analyzing {summary['total_chunks']} code snippets from {summary['total_files']} files")
        lines.append("")
        
        # Each snippet
        for snippet in context["code_snippets"]:
            lines.append(self.format_snippet_for_prompt(snippet))
            lines.append("")
        
        return "\n".join(lines)