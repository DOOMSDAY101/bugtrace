# bugtrace/rag/chunker.py
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language
)
import ast

class Chunker:
    """Smart file chunker using LangChain text splitters"""
    
    # Mapping of file extensions to LangChain language types
    LANGUAGE_MAP = {
        '.py': Language.PYTHON,
        '.js': Language.JS,
        '.ts': Language.JS,
        '.jsx': Language.JS,
        '.tsx': Language.JS,
        '.java': Language.JAVA,
        '.cpp': Language.CPP,
        '.c': Language.C,
        '.cs': Language.CSHARP,
        '.go': Language.GO,
        '.rs': Language.RUST,
        '.rb': Language.RUBY,
        '.php': Language.PHP,
        '.swift': Language.SWIFT,
        '.kt': Language.KOTLIN,
        '.scala': Language.SCALA,
        '.html': Language.HTML,
        '.md': Language.MARKDOWN,
    }
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize chunker with LangChain splitters.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Cache splitters for different languages
        self._splitters = {}
    
    def chunk_file(self, filepath: Path, content: str) -> List[Dict]:
        """
        Chunk file using appropriate LangChain splitter.
        
        Args:
            filepath: Path to the file
            content: File content as string
            
        Returns:
            List of chunks with metadata
        """
        if not content.strip():
            return []
        
        suffix = filepath.suffix.lower()
        
        # Get appropriate splitter
        if suffix in self.LANGUAGE_MAP:
            language = self.LANGUAGE_MAP[suffix]
            splitter = self._get_code_splitter(language)
        else:
            # Default to generic text splitter
            splitter = self._get_text_splitter()
        
        # Split the content
        chunks = splitter.split_text(content)
        
        # Convert to our chunk format with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            result.append({
                'text': chunk_text,
                'metadata': {
                    'file': str(filepath),
                    'chunk_id': i,
                    'language': suffix.lstrip('.'),
                    'total_chunks': len(chunks)
                }
            })
        
        return result
    
    def _get_code_splitter(self, language: Language) -> RecursiveCharacterTextSplitter:
        """
        Get or create a code-aware splitter for the given language.
        LangChain handles language-specific separators automatically.
        """
        if language not in self._splitters:
            self._splitters[language] = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        return self._splitters[language]
    
    def _get_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """
        Get or create a generic text splitter.
        Uses semantic separators (paragraphs, sentences, etc.)
        """
        if 'text' not in self._splitters:
            self._splitters['text'] = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=[
                    "\n\n",    # Paragraph breaks
                    "\n",      # Line breaks
                    ". ",      # Sentence ends
                    "! ",      # Exclamation
                    "? ",      # Question
                    "; ",      # Semicolon
                    ", ",      # Comma
                    " ",       # Space
                    "",        # Character
                ]
            )
        return self._splitters['text']


class EnhancedChunker(Chunker):
    """
    Enhanced chunker that adds semantic metadata for Python files.
    Uses AST for Python to extract function/class names.
    """
    
    def chunk_file(self, filepath: Path, content: str) -> List[Dict]:
        """
        Chunk file with enhanced metadata extraction.
        """
        # Get base chunks from parent class
        chunks = super().chunk_file(filepath, content)
        
        # Add enhanced metadata for Python files
        if filepath.suffix == '.py':
            chunks = self._enhance_python_chunks(filepath, content, chunks)
        
        return chunks
    
    def _enhance_python_chunks(self, filepath: Path, content: str, chunks: List[Dict]) -> List[Dict]:
        """
        Add function/class context to Python chunks using AST.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If parsing fails, return chunks as-is
            return chunks
        
        # Extract all function and class definitions with line numbers
        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                definitions.append({
                    'type': 'function',
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno,
                    'docstring': ast.get_docstring(node)
                })
            elif isinstance(node, ast.ClassDef):
                definitions.append({
                    'type': 'class',
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno,
                    'docstring': ast.get_docstring(node)
                })
        
        # Match chunks to definitions based on content
        for chunk in chunks:
            chunk_text = chunk['text']
            
            # Find which definition this chunk belongs to
            for defn in definitions:
                # Simple heuristic: if chunk contains the definition name
                if f"def {defn['name']}" in chunk_text or f"class {defn['name']}" in chunk_text:
                    chunk['metadata'].update({
                        'definition_type': defn['type'],
                        'definition_name': defn['name'],
                        'has_docstring': defn['docstring'] is not None
                    })
                    # Include docstring in chunk text if available
                    if defn['docstring'] and defn['docstring'] not in chunk_text:
                        chunk['text'] = f"# {defn['name']}: {defn['docstring']}\n\n{chunk_text}"
                    break
        
        return chunks