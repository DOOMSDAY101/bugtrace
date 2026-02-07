# bugtrace/rag/chunker.py
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language
)
import ast
import re
import hashlib

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
                'metadata': self._create_metadata(filepath, chunk_text, i, len(chunks), full_content=content)
            })
        
        return result
        
    
    def _create_metadata(self, filepath: Path, chunk_text: str, chunk_id: int, total_chunks: int, full_content: str = None) -> Dict:
        """Create rich metadata for bug tracing"""

        line_start = None
        line_end = None
    
        if full_content:
            # Find where this chunk appears in the full content
            chunk_start_pos = full_content.find(chunk_text)
            if chunk_start_pos != -1:
                # Count newlines before this chunk
                line_start = full_content[:chunk_start_pos].count('\n') + 1
                # Count newlines in this chunk
                line_end = line_start + chunk_text.count('\n')
            metadata = {
                # File context
                'file': str(filepath),
                'file_name': filepath.name,
                'file_type': filepath.suffix.lstrip('.'),
                
                # Chunk context
                'chunk_id': chunk_id,
                'total_chunks': total_chunks,
                'chunk_hash': hashlib.md5(chunk_text.encode()).hexdigest()[:16],

                # ✅ Line numbers (NEW)
                'line_start': line_start,
                'line_end': line_end,
                
                # Code analysis (for bug tracing)
                'has_error_handling': self._has_error_handling(chunk_text),
                'has_logging': self._has_logging(chunk_text),
                'has_todo': self._has_todo(chunk_text),
                'has_fixme': self._has_fixme(chunk_text),
                'line_count': chunk_text.count('\n') + 1,
            }
            
            # Add language-specific metadata
            if filepath.suffix == '.py':
                metadata.update(self._extract_python_metadata(chunk_text))
            
            return metadata
        
    def _has_error_handling(self, text: str) -> bool:
        """Check if chunk has error handling"""
        patterns = [
            r'\btry\s*:',
            r'\bexcept\s+',
            r'\bcatch\s*\(',
            r'\bfinally\s*:',
            r'\.catch\(',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _has_logging(self, text: str) -> bool:
        """Check if chunk has logging statements"""
        patterns = [
            r'\blogger\.',
            r'\bprint\(',
            r'\bconsole\.log\(',
            r'\bLog\.',
            r'logging\.',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _has_todo(self, text: str) -> bool:
        """Check for TODO comments"""
        return bool(re.search(r'#\s*TODO|//\s*TODO', text, re.IGNORECASE))
    
    def _has_fixme(self, text: str) -> bool:
        """Check for FIXME comments"""
        return bool(re.search(r'#\s*FIXME|//\s*FIXME', text, re.IGNORECASE))
    
    def _extract_python_metadata(self, text: str) -> Dict:
        """Extract Python-specific metadata"""
        metadata = {}
        
        # Check for function definitions
        func_match = re.search(r'def\s+(\w+)\s*\(', text)
        if func_match:
            metadata['function_name'] = func_match.group(1)
        
        # Check for class definitions
        class_match = re.search(r'class\s+(\w+)', text)
        if class_match:
            metadata['class_name'] = class_match.group(1)
        
        return metadata

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