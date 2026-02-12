"""
Orchestrator Agent.

Main controller that coordinates all agents and the analysis workflow.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ..report.status import get_reporter
from ..report.streaming import StreamingHandler
from .context_builder import ContextBuilder
from .prompt_manager import PromptManager
from .fix_validator import FixValidator
from ..llm.base import BaseLLM, LLMError


class Orchestrator:
    """
    Main orchestrator for bug analysis workflow.
    
    Coordinates:
    1. RAG search (via bug_analyzer)
    2. Context building
    3. Prompt creation
    4. LLM analysis
    5. Report formatting
    
    Usage:
        orchestrator = Orchestrator(llm=ollama_llm)
        result = orchestrator.analyze(
            query="login fails",
            search_results=[...]
        )
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        stream: bool = True,
        mode: str = "debug"
    ):
        """
        Initialize orchestrator.
        
        Args:
            llm: LLM instance (OllamaLLM, etc.)
            stream: Enable streaming responses
            mode: Analysis mode (debug, explain, review, security)
        """
        self.llm = llm
        self.stream = stream
        self.mode = mode

        
        # Initialize agents
        self.reporter = get_reporter()
        self.context_builder = ContextBuilder()
        self.prompt_manager = PromptManager()
        self.streaming_handler = StreamingHandler()
        self.fix_validator = FixValidator(llm)

    
    def analyze(
        self,
        query: str,
        search_results: list[Dict[str, Any]],
        max_chunks: int = 6
    ) -> Dict[str, Any]:
        """
        Run complete analysis workflow.
        
        Args:
            query: User's bug description
            search_results: Results from RAG search
            max_chunks: Max code chunks to analyze
        
        Returns:
            Analysis result:
            {
                "query": "user question",
                "response": "LLM analysis",
                "context": {...},
                "metadata": {...}
            }
        """
        # Display header
        self.reporter.header("Bug Analysis", query)
        
        try:
            # Step 1: Build context
            context = self.context_builder.build_context(
                query=query,
                search_results=search_results,
                max_chunks=max_chunks
            )
            
            # Step 2: Build prompt
            with self.reporter.section("Preparing analysis"):
                messages = self.prompt_manager.build_debug_prompt(
                    query=query,
                    context=context,
                    mode=self.mode
                )
                
                self.reporter.success(f"Built {len(messages)} messages for LLM")
                self.reporter.info(f"Mode: {self.mode}")
                self.reporter.info(f"Model: {self.llm.model}")
            
            # Step 3: Get LLM analysis
            response = self._run_llm_analysis(messages)

            with self.reporter.section("Validating proposed fix"):
                try:
                    context_text = self.context_builder.format_context_for_prompt(context)

                    validated_response = self.fix_validator.validate(
                        context_text=context_text,
                        original_response=response,
                    )

                    response = validated_response
                    self.reporter.success("Fix validation complete")

                except Exception as e:
                    self.reporter.warning(
                        "Fix validation failed, using original analysis"
                    )
                    self.reporter.warning(str(e))
            
            # Step 4: Build result
            result = {
                "query": query,
                "response": response,
                "context": context,
                "metadata": {
                    "mode": self.mode,
                    "model": self.llm.model,
                    "chunks_analyzed": len(context["code_snippets"]),
                    "files_analyzed": context["summary"]["total_files"],
                    "validated": True,
                }
            }
            
            # Display completion
            self.reporter.complete()
            
            return result
        
        except LLMError as e:
            self.reporter.error(f"LLM Error: {str(e)}")
            raise
        
        except Exception as e:
            self.reporter.error(f"Analysis failed: {str(e)}")
            raise
    
    def _run_llm_analysis(self, messages: list) -> str:
        """
        Run LLM analysis with or without streaming.
        
        Args:
            messages: Messages to send to LLM
        
        Returns:
            LLM response text
        """
        if self.stream:
            return self._run_streaming_analysis(messages)
        else:
            return self._run_standard_analysis(messages)
    
    def _run_streaming_analysis(self, messages: list) -> str:
        """Run analysis with streaming response."""
        # Start streaming display
        self.streaming_handler.start(
            f"Analyzing with {self.llm.model}"
        )
        
        try:
            # Stream tokens
            for token in self.llm.chat_stream(messages):
                self.streaming_handler.write(token)
            
            # Get complete response
            response = self.streaming_handler.finish()
            return response
        
        except Exception as e:
            self.streaming_handler.finish()
            raise
    
    def _run_standard_analysis(self, messages: list) -> str:
        """Run analysis without streaming."""
        with self.reporter.section(
            f"Analyzing with {self.llm.model}",
            show_spinner=True
        ):
            response = self.llm.chat(messages)
            self.reporter.success("Analysis complete")
            return response
    
    def analyze_with_rag(
        self,
        query: str,
        bug_analyzer,  # Your existing BugAnalyzer instance
        max_chunks: int = 6
    ) -> Dict[str, Any]:
        """
        Run analysis with RAG integration.
        
        This is the main entry point when called from CLI.
        
        Args:
            query: User's bug description
            bug_analyzer: Your BugAnalyzer instance (from analyze module)
            max_chunks: Max chunks to retrieve
        
        Returns:
            Analysis result
        """
        # Step 1: Search with RAG
        with self.reporter.section("Searching codebase"):
            search_results = bug_analyzer.analyze_bug(query, top_k=max_chunks)
            self.reporter.success(f"Found {len(search_results)} relevant code chunks")
            
            # Show which files were found
            files = set()
            for result in search_results:
                file_path = result.get("metadata", {}).get("file", "unknown")
                files.add(file_path)
            
            for file in sorted(files):
                self.reporter.info(f"  • {Path(file).name}")
        
        # Step 2: Run full analysis
        return self.analyze(
            query=query,
            search_results=search_results,
            max_chunks=max_chunks
        )
    
    def set_mode(self, mode: str):
        """
        Change analysis mode.
        
        Args:
            mode: One of: debug, explain, review, security
        """
        valid_modes = ["debug", "explain", "review", "security"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        
        self.mode = mode
    
    def set_streaming(self, enabled: bool):
        """Enable or disable streaming responses."""
        self.stream = enabled