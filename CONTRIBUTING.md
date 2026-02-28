# Contributing to Bugtrace

First off, thank you for considering contributing to Bugtrace! 🎉

Bugtrace is an open-source project, and we welcome contributions from everyone. Whether you're fixing bugs, adding features, improving documentation, or sharing ideas, your help is appreciated.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

---

## 📜 Code of Conduct

This project follows a Code of Conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

---

## 🤝 How Can I Contribute?

### Reporting Bugs

Found a bug? Help us fix it!

1. **Check existing issues** - Someone might have already reported it
2. **Open a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Your environment (OS, Python version, Ollama version)
   - Screenshots or logs (if applicable)

**Bug Report Template:**

```markdown
**Description**
A clear description of the bug.

**To Reproduce**

1. Go to '...'
2. Run command '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**

- OS: [e.g., Ubuntu 22.04, Windows 11, macOS 14]
- Python version: [e.g., 3.11.5]
- Bugtrace version: [e.g., 1.0.0]
- Ollama version: [e.g., 0.1.26]

**Additional Context**
Add any other context, screenshots, or logs.
```

### Suggesting Features

Have an idea to improve Bugtrace?

1. **Check existing feature requests** - It might already be planned
2. **Open a discussion** in [GitHub Discussions](https://github.com/DOOMSDAY101/bugtrace/discussions)
3. **Describe your idea**:
   - What problem does it solve?
   - How would it work?
   - Any examples or mockups?

### Improving Documentation

Documentation improvements are always welcome!

- Fix typos or unclear explanations
- Add examples or use cases
- Improve installation instructions
- Translate documentation (future)

### Writing Code

Want to contribute code? Great! See [Development Setup](#development-setup) below.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Git**
- **Ollama** (for testing)
- **Basic knowledge of**:
  - Python
  - LangChain
  - Vector databases (helpful but not required)

### Areas to Contribute

Here are some areas where we need help:

**High Priority:**

- 🔍 Log search tool implementation
- ⚙️ Config validation tool
- 📊 Ranked hypotheses output
- 🧪 Test coverage improvements

**Medium Priority:**

- 🤖 OpenAI LLM provider support
- 🌐 Anthropic (Claude) support
- 📄 Export reports to JSON/Markdown
- 🎨 Improved terminal UI

**Future:**

- 🔧 Automatic fix suggestions
- 🌳 Git integration
- 🌍 Multi-language parsing improvements
- 🕸️ Web UI

Check [Issues](https://github.com/DOOMSDAY101/bugtrace/issues) for specific tasks!

---

## 💻 Development Setup

### 1. Fork the Repository

Click the "Fork" button at the top right of the repository page.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/bugtrace.git
cd bugtrace
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/DOOMSDAY101/bugtrace.git
```

### 4. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 5. Install Dependencies

```bash
# Install in editable mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

### 6. Verify Setup

```bash
# Run Bugtrace
bugtrace --help

# Should show the logo and commands
```

### 7. Install Ollama and Pull Model

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull test model
ollama pull llama3.2:3b
ollama pull nomic-embed-text:latest

```

---

## 🔨 Making Changes

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/issue-description
```

**Branch naming conventions:**

- `feature/add-log-search` - New features
- `fix/session-crash` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/cleanup-agent` - Code refactoring
- `test/add-rag-tests` - Tests

### 2. Make Your Changes

Edit the code, following our [Coding Standards](#coding-standards).

### 3. Test Your Changes

```bash
# Test manually
cd test-project
bugtrace init
bugtrace index
bugtrace session

```

### 4. Update Documentation

If your changes affect user-facing behavior:

- Update `README.md`
- Update command help text
- Add examples if needed

---

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
# Good commits:
git commit -m "feat(session): add streaming response support"
git commit -m "fix(index): handle empty codebase gracefully"
git commit -m "docs(readme): add JavaScript project example"
git commit -m "refactor(agent): simplify intent routing logic"

# Bad commits:
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "asdf"
```

### Commit Best Practices

- ✅ Write clear, descriptive messages
- ✅ Use present tense ("add feature" not "added feature")
- ✅ Keep commits focused (one logical change per commit)
- ✅ Reference issue numbers when applicable (`fix #42`)

---

## 🔄 Pull Request Process

### 1. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 2. Open a Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:

**PR Template:**

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Other (describe)

## Related Issue

Fixes #(issue number)

## How Has This Been Tested?

Describe your testing process.

## Checklist

- [ ] My code follows the project's coding standards
- [ ] I have updated documentation as needed
- [ ] I have added tests (if applicable)
- [ ] All tests pass
- [ ] My commits follow the commit guidelines
```

### 3. Code Review

- Maintainers will review your PR
- Address any requested changes
- Be patient and respectful

### 4. Merging

Once approved:

- Maintainers will merge your PR
- Your changes will be in the next release! 🎉

---

## 🎨 Coding Standards

### Python Style

- **PEP 8** compliance
- **Type hints** for function signatures
- **Docstrings** for public functions/classes

**Example:**

```python
def search_codebase(query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    """
    Search the codebase for relevant code chunks.

    Args:
        query: Search query string
        top_k: Number of results to return

    Returns:
        List of search results with metadata
    """
    # Implementation
    pass
```

### Code Organization

- Keep functions small and focused
- Use meaningful variable names
- Add comments for complex logic
- Avoid deep nesting (max 3-4 levels)

### Import Order

```python
# Standard library
import os
from pathlib import Path

# Third-party
import typer
from rich.console import Console

# Local
from bugtrace.utils import fs
from bugtrace.config import settings
```

---

## 🧪 Testing

### Manual Testing

```bash
# Test in a sample project
cd ~/test-projects/sample-app
bugtrace init
bugtrace index
bugtrace session
```

## 📚 Documentation

### Where to Update Documentation

- **README.md** - User-facing features, installation, quick start
- **CHANGELOG.md** - Version changes
- **Code comments** - Complex logic
- **Docstrings** - All public functions/classes

### Documentation Style

- Clear and concise
- Use examples
- Assume reader has basic knowledge
- Link to external resources when helpful

---

## 💬 Community

### Getting Help

- **GitHub Discussions** - Ask questions, share ideas
- **Issues** - Report bugs, request features
- **Twitter/X** - Follow [@Sulaiman_Ife](https://x.com/Sulaiman_Ife) for updates

### Stay Updated

- ⭐ Star the repository
- 👀 Watch for releases
- 🐦 Follow on Twitter/X

---

## 🙏 Recognition

Contributors will be:

- Listed in release notes
- Mentioned in the README (for significant contributions)
- Thanked publicly on Twitter/X

---

## ❓ Questions?

Have questions about contributing? Feel free to:

- Open a discussion in [GitHub Discussions](https://github.com/DOOMSDAY101/bugtrace/discussions)
- Reach out on [Twitter/X](https://x.com/Sulaiman_Ife)
- Open an issue with the `question` label

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Bugtrace! 🚀**

Every contribution, no matter how small, helps make debugging easier for developers everywhere.
