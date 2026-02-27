<div align="center">
```
██████╗ ██╗   ██╗ ██████╗ ████████╗██████╗  █████╗  ██████╗███████╗
██╔══██╗██║   ██║██╔════╝ ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
██████╔╝██║   ██║██║  ███╗   ██║   ██████╔╝███████║██║     █████╗  
██╔══██╗██║   ██║██║   ██║   ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
██████╔╝╚██████╔╝╚██████╔╝   ██║   ██║  ██║██║  ██║╚██████╗███████╗
╚═════╝  ╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
```

# Bugtrace

**AI-Powered Debugging Assistant with RAG-Based Codebase Search**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DOOMSDAY101/bugtrace/releases)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)](https://github.com/DOOMSDAY101/bugtrace)

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 Overview

**Bugtrace** is an intelligent debugging assistant that uses Retrieval-Augmented Generation (RAG) to understand your codebase and help you find bugs interactively. Unlike traditional debuggers, Bugtrace provides conversational, context-aware assistance powered by local LLMs.

### Why Bugtrace?

- 🔍 **Smart Code Search**: Semantic search finds relevant code instantly
- 💬 **Interactive Sessions**: Chat naturally about your bugs
- 🧠 **Context-Aware**: Remembers conversation history and understands follow-ups
- 📍 **Precise References**: Shows exact file names, line numbers, and functions
- 🆓 **100% Local**: Works with Ollama - no API costs, your code stays private
- ⚡ **Fast Setup**: Initialize in seconds, start debugging immediately

---

## ✨ Features

### Core Capabilities

- **Interactive Debugging Sessions**: Chat with an AI that understands your entire codebase
- **RAG-Based Search**: Vector database indexes your code for semantic search
- **Intelligent Intent Routing**: Automatically determines when to search code vs answer from memory
- **Dual Memory System**: Maintains both recent conversation context and semantic retrieval from past discussions
- **Real-Time Streaming**: Beautiful markdown-formatted responses stream as they're generated
- **File Tracking**: Incremental indexing - only processes new/changed files

### Advanced Features

- **Function-Level References**: Pinpoints exact functions, classes, and line numbers
- **Progress Indicators**: Visual feedback shows when code is being searched
- **Conversation Memory**: Understands "what files did you cite?" and other follow-ups
- **Project-Aware**: Respects `.gitignore`-style patterns for focused analysis
- **Extensible Architecture**: Easy to add new tools and LLM providers

---

## 🚀 Installation

### Prerequisites

- **Python 3.9+** (tested on 3.9, 3.10, 3.11)
- **Ollama** (for local LLM inference)
- **nomic-embed-text:latest** (for creating vector embeddings)

### Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

### Install Bugtrace

#### Method 1: From GitHub (Current)

```bash
git clone https://github.com/DOOMSDAY101/bugtrace.git
cd bugtrace
pip install -r requirements.txt
pip install -e .
```

#### Method 2: From PyPI (Coming Soon)

```bash
pip install bugtrace
```

#### Method 3: Docker (Coming Soon)

```bash
docker pull doomsday101/bugtrace:latest
```

### Verify Installation

```bash
bugtrace --help
```

You should see the Bugtrace logo and available commands.

---

## 🏁 Quick Start

### 1. Pull an Ollama Model

```bash
# Recommended: Fast 3B model
ollama pull llama3.2:3b

# pull the vector embedding model
ollama pull nomic-embed-text:latest
```

### 2. Initialize in Your Project

```bash
cd your-project
bugtrace init
```

This creates:

- `bugtrace.yaml` - Configuration file
- `.bugtrace/` - State and index directory

### 3. Index Your Codebase

```bash
bugtrace index
```

This builds a vector database of your code. Only runs once (or when files change).

### 4. Start Interactive Session

```bash
bugtrace session
```

### Example Session

You: why does login fail with 500 error?
→ Detected code question, searching codebase...
🔍 Found 6 relevant code sections
├─ src/auth.py::login (lines 45-60)
├─ src/middleware/auth.py::check_auth (lines 25-40)
├─ src/routes/login.py::handle_login (lines 78-95)
💡 Agent:
The 500 error in your login is caused by missing error handling in
src/auth.py at line 52. The database.get_user() call doesn't handle
connection failures, which results in an unhandled exception.
Here's the problematic code in src/auth.py (lines 45-60):
pythondef login(self, username: str, password: str):
user = database.get_user(username) # ← No error handling
if user is None:
raise UserNotFoundError(...)
Suggested Fix:
Add a try-except block to handle database errors:
pythondef login(self, username: str, password: str):
try:
user = database.get_user(username)
except DatabaseError as e:
logger.error(f"Database connection failed: {e}")
raise AuthenticationError("Database connection failed") from e

    if user is None:
        raise UserNotFoundError(...)

```

You: what files did you cite?

💡 Agent:

I cited these files:
1. **src/auth.py** (lines 45-60) - The main login function
2. **src/middleware/auth.py** (lines 25-40) - Authentication middleware
3. **src/routes/login.py** (lines 78-95) - Login route handler

The primary issue was in src/auth.py where database errors weren't being caught.

You: thanks!

💡 Agent:

You're welcome! Let me know if you need help implementing the fix or
if you encounter any other issues.
```

---

## 📖 Documentation

### Commands

#### `bugtrace init`

Initialize Bugtrace in your project.

```bash
# Initialize with defaults
bugtrace init

# Specify LLM provider and model
bugtrace init --llm ollama --model llama3.1:8b

# Initialize in specific directory
bugtrace init --path /path/to/project
```

#### `bugtrace scan`

Scan project files and update manifest (tracks file changes).

```bash
bugtrace scan
```

#### `bugtrace index`

Build vector embeddings from your codebase.

```bash
# Incremental index (only new/changed files)
bugtrace index

# Force full re-index
bugtrace index --force
```

#### `bugtrace status`

Check current project indexing status.

```bash
bugtrace status
```

#### `bugtrace session`

Start interactive debugging session.

```bash
bugtrace session

# In session:
# - Ask questions about your code
# - Type \q to quit
```

#### `bugtrace analyze`

One-shot bug analysis (non-interactive).

```bash
bugtrace analyze "login returns 500 error"

# With options
bugtrace analyze "memory leak in worker" \
  --top-k 10 \
  --show-code \
  --export-md report.md
```

#### `bugtrace clean`

Remove all Bugtrace files from project.

```bash
bugtrace clean
```

---

### Configuration

Edit `bugtrace.yaml` to customize behavior:

```yaml
llm:
  provider: ollama # LLM provider (ollama, openai - coming soon)
  model: llama3.2:3b # Model name
  temperature: 0.2 # Response creativity (0.0-1.0)

paths:
  project_root: . # Project root directory
  ignore: # Files/folders to ignore
    - node_modules
    - venv
    - .env
    - .git
    - .bugtrace
    - "*.pyc"
    - "__pycache__"

rag:
  chunk_size: 1000 # Code chunk size for indexing
  chunk_overlap: 200 # Overlap between chunks
  top_k: 6 # Number of results to retrieve
  store: chroma # Vector store backend

tools:
  code_search: true # Enable code search
  log_search: true # Enable log search (coming soon)
  config_check: true # Enable config validation (coming soon)

analysis:
  max_steps: 5 # Max reasoning steps
  reasoning_style: concise # Response style (concise, detailed)
```

---

## 🛠️ Core Technologies

Bugtrace is built on modern AI and developer tooling:

| Technology                                      | Purpose                                       |
| ----------------------------------------------- | --------------------------------------------- |
| [LangChain](https://python.langchain.com/)      | AI agent orchestration and memory management  |
| [ChromaDB](https://www.trychroma.com/)          | Vector database for semantic code search      |
| [Ollama](https://ollama.com/)                   | Local LLM inference (privacy-first)           |
| [Rich](https://rich.readthedocs.io/)            | Beautiful terminal UI with markdown rendering |
| [Typer](https://typer.tiangolo.com/)            | Modern CLI framework                          |
| [Sentence Transformers](https://www.sbert.net/) | Code embeddings for semantic search           |

---

## 🗺️ Roadmap

### v1.1.0 (Next Release)

- [ ] Log search tool - Find errors in application logs
- [ ] Config validation - Detect misconfigurations
- [ ] Ranked hypotheses - Multiple possible causes with confidence scores
- [ ] Export reports - Save analysis to markdown/JSON

### v1.2.0

- [ ] OpenAI support - Use GPT-4 for more complex reasoning
- [ ] Anthropic (Claude) support
- [ ] Multi-file bug tracking - Track issues across related files

### v2.0.0

- [ ] Automatic fix suggestions with diff preview
- [ ] Git integration - Commit fixes directly
- [ ] Team collaboration features
- [ ] Web UI for easier interaction

[See full roadmap →](https://github.com/DOOMSDAY101/bugtrace/issues)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Ways to Contribute

- 🐛 **Report Bugs**: [Open an issue](https://github.com/DOOMSDAY101/bugtrace/issues/new)
- 💡 **Suggest Features**: Share your ideas in [Discussions](https://github.com/DOOMSDAY101/bugtrace/discussions)
- 📖 **Improve Docs**: Fix typos, add examples
- 🔧 **Submit PRs**: See [CONTRIBUTING.md](CONTRIBUTING.md)

### Development Setup

```bash
# Clone repo
git clone https://github.com/DOOMSDAY101/bugtrace.git
cd bugtrace

# Install in editable mode
pip install -e .
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ifeoluwa Sulaiman**

- GitHub: [@DOOMSDAY101](https://github.com/DOOMSDAY101)
- Twitter/X: [@Sulaiman_Ife](https://x.com/Sulaiman_Ife)
- LinkedIn: [ifeoluwa-sulaiman](https://www.linkedin.com/in/ifeoluwa-sulaiman)

---

## 🙏 Acknowledgments

Special thanks to:

- The [LangChain](https://github.com/langchain-ai/langchain) team for the agent framework
- [Ollama](https://ollama.com/) for making local LLMs accessible
- The open-source community for inspiration and tools

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/DOOMSDAY101/bugtrace/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DOOMSDAY101/bugtrace/discussions)
- **Twitter/X**: [@Sulaiman_Ife](https://x.com/Sulaiman_Ife)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by [Ifeoluwa Sulaiman](https://github.com/DOOMSDAY101)

</div>
```

---
