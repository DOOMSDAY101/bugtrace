from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8")

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#") and not line.startswith("-e")
        ]

setup(
    name="bugtrace",
    version="1.0.0",
    author="Ifeoluwa Sulaiman",
    author_email="ifeoluwasulaiman30@gmail.com",
    description="AI-powered debugging assistant with RAG-based codebase search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DOOMSDAY101/bugtrace",
    project_urls={
        "Bug Tracker": "https://github.com/DOOMSDAY101/bugtrace/issues",
        "Documentation": "https://github.com/DOOMSDAY101/bugtrace#readme",
        "Source Code": "https://github.com/DOOMSDAY101/bugtrace",
        "Changelog": "https://github.com/DOOMSDAY101/bugtrace/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", ".bugtrace", ".bugtrace.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: English",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bugtrace=bugtrace.cli.main:run",
        ],
    },
    include_package_data=True,
    keywords=[
        "debugging",
        "ai",
        "llm",
        "rag",
        "codebase-search",
        "ollama",
        "assistant",
        "langchain",
        "semantic-search",
        "developer-tools",
    ],
    zip_safe=False,
)