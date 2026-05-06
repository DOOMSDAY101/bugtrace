# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-06

### Breaking Changes

- Replaced LangChain agent abstractions with LangGraph-based execution
- Removed legacy agent/memory abstractions in favor of explicit state management
- Refactored session agent architecture (new execution flow and message handling)
- Tool interaction model changed (now uses structured tool calls + ToolMessage)

### Added

#### LangGraph Agent System

- Introduced StateGraph-based ReAct agent
- Explicit control over agent → tool → agent loop
- Conditional execution flow (`continue` vs `end`)
- Built-in checkpointing with MemorySaver

#### Tooling Improvements

- Standardized tool interface using `@tool`
- Improved code search tool formatting (clear file + line references)
- Tool lifecycle events:
  - `tool_start`
  - `tool_end`

#### Streaming Overhaul

- Token-level streaming from agent node
- Structured execution events:
  - `token`
  - `tool_start`
  - `tool_end`
  - `node_complete`

- Better real-time UX and observability

### Changed

- Rewrote session agent using LangGraph instead of LangChain agents
- Simplified LLM interaction (direct `.invoke()` + `.bind_tools()`)
- Improved system prompt handling (injected once at runtime)
- Refactored conversation state handling using graph state
- Cleaner separation between agent logic and tools

### Removed

- LangChain agent executor abstractions
- Legacy memory systems (conversation buffer, retriever memory wrappers)
- Hidden agent loops (now fully explicit via graph)

### Fixed

- Improved handling of empty tool queries
- More robust message/state synchronization
- Cleaner extraction of file references from tool results
- General stability improvements in streaming and execution flow

## [1.0.0] - 2025-02-27

### 🎉 Initial Release

First stable release of Bugtrace - AI-powered debugging assistant!

### ✨ Features

#### Core Functionality

- **Interactive Debugging Sessions** - Chat naturally with an AI that understands your codebase
- **RAG-Based Code Search** - Vector database with semantic search finds relevant code instantly
- **Intelligent Intent Routing** - LLM-based classification determines when to search vs chat
- **Dual Memory System** - Combines recent conversation buffer with semantic context retrieval
- **Real-Time Streaming** - Beautiful markdown-formatted responses with progress indicators

#### CLI Commands

- `bugtrace init` - Initialize project with configuration
- `bugtrace scan` - Scan and track file changes
- `bugtrace index` - Build vector embeddings (incremental indexing)
- `bugtrace status` - Check project indexing status
- `bugtrace session` - Start interactive debugging
- `bugtrace analyze` - One-shot bug analysis
- `bugtrace clean` - Remove Bugtrace files

#### Smart Features

- **Context-Aware Conversations** - Understands follow-up questions like "what files did you cite?"
- **Precise References** - Shows exact file names, line numbers, and function names
- **Incremental Indexing** - Only processes new/changed files
- **File Tracking** - Automatic manifest management with SHA-256 hashing
- **Rich Terminal UI** - Progress indicators, markdown rendering, syntax highlighting

#### LLM Support

- **Ollama Integration** - Full support for local LLMs (llama3.2, llama3.1, etc.)
- **Streaming Responses** - Token-by-token output with live markdown formatting
- **Memory Management** - LangChain-powered conversation and vector memory

### 🛠️ Technical Stack

- LangChain - Agent orchestration and memory
- ChromaDB - Vector storage
- Ollama - Local LLM inference
- Rich - Terminal UI
- Typer - CLI framework

### 📝 Configuration

- YAML-based configuration (`bugtrace.yaml`)
- Customizable ignore patterns
- Adjustable RAG parameters (chunk size, top_k, etc.)
- LLM provider and model selection

### 🎯 Use Cases

- Debugging production issues
- Understanding legacy code
- Code review assistance
- Onboarding to new codebases
- Finding specific implementations

### ⚠️ Known Limitations

- Single tool (code search only - log search and config check coming in v1.1)
- Ollama-only LLM support (OpenAI/Anthropic in v1.2)
- No automatic fix generation (planned for v2.0)
- No Git integration yet (v2.0)

### 📦 Installation

```bash
git clone https://github.com/DOOMSDAY101/bugtrace.git
cd bugtrace
pip install -r requirements.txt
pip install -e .
```

### 🚀 Quick Start

```bash
bugtrace init
bugtrace index
bugtrace session
```

---

## [Unreleased]

### Planned for v2.1.0

- OpenAI support (GPT-4, GPT-3.5-turbo)
- Anthropic (Claude) support
- Multi-file bug tracking

### Planned for v2.2.0

- Automatic fix suggestions
- Git integration
- Team collaboration features
- Web UI

---

[1.0.0]: https://github.com/DOOMSDAY101/bugtrace/releases/tag/v1.0.0
