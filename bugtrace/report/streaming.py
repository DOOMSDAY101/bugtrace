"""
Streaming response handler for LLM outputs.

Displays AI responses as they're generated (typing effect).
"""

from typing import Iterator, Optional
from .status import get_reporter


class StreamingHandler:
    """
    Handles streaming LLM responses with real-time display.
    
    Usage:
        handler = StreamingHandler()
        
        # Start streaming
        handler.start("Analyzing with Ollama...")
        
        # Stream tokens
        for token in llm_stream:
            handler.write(token)
        
        # End streaming
        response = handler.finish()
    """
    
    def __init__(self):
        self.reporter = get_reporter()
        self._buffer = []
        self._is_streaming = False
    
    def start(self, title: str = "AI Response"):
        """Start streaming section."""
        self._buffer = []
        self._is_streaming = True
        self.reporter.stream_start(title)
    
    def write(self, token: str):
        """Write a single token to the stream."""
        if self._is_streaming:
            self._buffer.append(token)
            self.reporter.stream_token(token)
    
    def finish(self) -> str:
        """End streaming and return full response."""
        if self._is_streaming:
            self.reporter.stream_end()
            self._is_streaming = False
        
        return "".join(self._buffer)
    
    def get_response(self) -> str:
        """Get accumulated response without ending stream."""
        return "".join(self._buffer)


class BufferedStreamHandler:
    """
    Alternative handler that buffers chunks before displaying.
    
    Useful for formatting responses before display.
    """
    
    def __init__(self, chunk_size: int = 5):
        self.reporter = get_reporter()
        self._buffer = []
        self._chunk_size = chunk_size
        self._chunks_written = 0
    
    def start(self, title: str = "AI Response"):
        """Start streaming section."""
        self._buffer = []
        self._chunks_written = 0
        self.reporter.stream_start(title)
    
    def write(self, token: str):
        """Buffer tokens and write in chunks."""
        self._buffer.append(token)
        
        # Write every N tokens
        if len(self._buffer) >= self._chunk_size:
            chunk = "".join(self._buffer)
            self.reporter.stream_token(chunk)
            self._buffer = []
            self._chunks_written += 1
    
    def finish(self) -> str:
        """Flush remaining buffer and end stream."""
        # Write remaining tokens
        if self._buffer:
            chunk = "".join(self._buffer)
            self.reporter.stream_token(chunk)
        
        self.reporter.stream_end()
        return self.get_full_response()
    
    def get_full_response(self) -> str:
        """Get complete response."""
        return "".join(self._buffer)