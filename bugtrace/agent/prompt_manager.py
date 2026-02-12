"""
Prompt Manager Agent.

Builds effective prompts for different analysis scenarios.
"""

from typing import Dict, Any, List
from ..llm.base import Message


class PromptManager:
    """
    Creates optimized prompts for LLM debugging.
    
    Supports different analysis modes:
    - debug: Find and explain bugs
    - explain: Explain how code works
    - review: Code review and suggestions
    - security: Security analysis
    
    Usage:
        manager = PromptManager()
        messages = manager.build_debug_prompt(
            query="login fails",
            context={...}
        )
    """
    
    # System prompts for different modes
    SYSTEM_PROMPTS = {
        "debug": """You are an expert debugging assistant analyzing a real codebase.

IMPORTANT CONSTRAINTS (must follow strictly):
- Do NOT invent new classes, attributes, or methods that are not present in the provided code
- Do NOT assume access to objects unless explicitly shown in the code
- Validate each proposed fix by tracing execution step-by-step
- If a fix would fail, say so and correct it
- If information is missing, state the assumption explicitly

Your task:
1. Analyze the provided code snippets carefully
2. Identify the root cause of the bug
3. Provide specific, actionable fixes
4. Reference exact file locations (file path + line numbers)
5. Ensure the fix is internally consistent with the codebase

Format your response with these sections:
- **Root Cause**
- **Evidence** (file + line numbers)
- **Correct Fix** (validated against the code)
- **Why This Fix Works**
- **Prevention**

Be precise. Prefer correctness over confidence.""",
        
        "explain": """You are a code explanation expert.

Your task:
1. Explain how the provided code works
2. Describe the flow and logic
3. Highlight important patterns or decisions
4. Point out potential issues or edge cases

Use clear language and reference specific files and line numbers.""",
        
        "review": """You are a code reviewer performing a thorough review.

Your task:
1. Review code quality and best practices
2. Identify potential bugs or issues
3. Suggest improvements
4. Highlight good patterns

Provide constructive feedback with specific file and line references.""",
        
        "security": """You are a security analyst reviewing code.

Your task:
1. Identify security vulnerabilities
2. Check for common security issues (SQL injection, XSS, etc.)
3. Review authentication and authorization
4. Check input validation

Provide specific security recommendations with code references."""
    }
    
    def __init__(self):
        pass
    
    def build_debug_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        mode: str = "debug"
    ) -> List[Message]:
        """
        Build complete prompt for debugging.
        
        Args:
            query: User's bug description
            context: Context from ContextBuilder
            mode: Analysis mode (debug, explain, review, security)
        
        Returns:
            List of Message objects ready for LLM
        """
        # System message
        system_prompt = self.SYSTEM_PROMPTS.get(mode, self.SYSTEM_PROMPTS["debug"])
        
        # User message
        user_prompt = self._build_user_prompt(query, context, mode)
        
        return [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt)
        ]
    
    def _build_user_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        mode: str
    ) -> str:
        """Build user prompt with context."""
        lines = []
        
        # Bug description
        if mode == "debug":
            lines.append(f"**Bug Description:** {query}")
        elif mode == "explain":
            lines.append(f"**Explain:** {query}")
        elif mode == "review":
            lines.append(f"**Review Request:** {query}")
        elif mode == "security":
            lines.append(f"**Security Concern:** {query}")
        
        lines.append("")
        
        # Context summary
        summary = context.get("summary", {})
        lines.append(f"**Context:** Analyzing {summary.get('total_chunks', 0)} code snippets from {summary.get('total_files', 0)} files")
        lines.append("")
        
        # Code snippets
        lines.append("**Relevant Code:**")
        lines.append("")
        
        for snippet in context.get("code_snippets", []):
            lines.append(self._format_snippet(snippet))
            lines.append("")
        
        # Instruction based on mode
        if mode == "debug":
            lines.append("**Based on this code, identify what's causing the bug and how to fix it.**")
        elif mode == "explain":
            lines.append("**Explain how this code works and what it's trying to accomplish.**")
        elif mode == "review":
            lines.append("**Review this code and provide improvement suggestions.**")
        elif mode == "security":
            lines.append("**Analyze this code for security vulnerabilities.**")
        
        return "\n".join(lines)
    
    def _format_snippet(self, snippet: Dict[str, Any]) -> str:
        """Format code snippet for prompt."""
        lines = []
        
        # Header
        lines.append("---")
        lines.append(f"**File:** `{snippet['file']}`")
        
        if "lines" in snippet:
            lines.append(f"**Lines:** {snippet['lines']}")
        
        if "function" in snippet:
            lines.append(f"**Function:** `{snippet['function']}`")
        
        # Metadata flags
        metadata = snippet.get("metadata", {})
        if metadata:
            notes = []
            
            if metadata.get("has_error_handling") is False:
                notes.append("⚠️ No error handling")
            
            if metadata.get("has_logging") is False:
                notes.append("⚠️ No logging")
            
            if metadata.get("has_todo"):
                notes.append("📝 Has TODO comments")
            
            if notes:
                lines.append(f"**Notes:** {' • '.join(notes)}")
        
        # Code block
        lines.append("")
        file_type = snippet.get("metadata", {}).get("file_type", "")
        lines.append(f"```{file_type}")
        lines.append(snippet["code"].strip())
        lines.append("```")
        
        return "\n".join(lines)
    
    def build_simple_prompt(self, query: str, code: str) -> List[Message]:
        """
        Build simple prompt without RAG context.
        
        Useful for quick questions or when RAG is not available.
        
        Args:
            query: User question
            code: Code snippet
        
        Returns:
            List of Message objects
        """
        return [
            Message(
                role="system",
                content=self.SYSTEM_PROMPTS["debug"]
            ),
            Message(
                role="user",
                content=f"{query}\n\n```\n{code}\n```"
            )
        ]
    
    def build_followup_prompt(
        self,
        original_query: str,
        original_response: str,
        followup_query: str
    ) -> List[Message]:
        """
        Build prompt for follow-up questions.
        
        Args:
            original_query: Original bug description
            original_response: Previous LLM response
            followup_query: Follow-up question
        
        Returns:
            List of Message objects with conversation history
        """
        return [
            Message(role="system", content=self.SYSTEM_PROMPTS["debug"]),
            Message(role="user", content=original_query),
            Message(role="assistant", content=original_response),
            Message(role="user", content=followup_query)
        ]