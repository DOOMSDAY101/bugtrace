from pathlib import Path
import yaml


DEFAULT_CONFIG = {
    "llm": {
        "provider": "ollama",
        "model": "llama3.2:3b",
        "temperature": 0.2,
    },
    "paths": {
        "project_root": ".",
        "ignore": ["node_modules", "venv", ".git", ".bugtrace"],
        "logs": ["logs/"],
    },
    "rag": {
        "chunk_size": 500,
        "top_k": 6,
        "store": "chroma",
    },
    "tools": {
        "code_search": True,
        "log_search": True,
        "config_check": True,
    },
    "analysis": {
        "max_steps": 5,
        "reasoning_style": "concise",
    },
}


def create_default_config(
    project_root: Path,
    llm_provider: str,
    model: str,
) -> bool:
    """
    Creates bugtrace.yaml.
    Returns True if created, False if already exists.
    """
    config_path = project_root / "bugtrace.yaml"

    if config_path.exists():
        return False

    config = DEFAULT_CONFIG.copy()
    config["llm"]["provider"] = llm_provider
    config["llm"]["model"] = model

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    return True

def load_user_config(project_root: Path) -> dict:
    """
    Load user configuration from bugtrace.yaml.
    Falls back to DEFAULT_CONFIG if not found.
    """
    config_path = project_root / "bugtrace.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG.copy()