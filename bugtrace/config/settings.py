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
        "chunk_size": 1000,
        "chunk_overlap": 200,
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

def validate_config(config: dict) -> dict:
    """
    Validate configuration dictionary.
    Raises ValueError if invalid.
    Returns the validated config.
    """
    errors = []
    
    # Validate top-level structure
    required_sections = ["llm", "paths", "rag", "tools", "analysis"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: '{section}'")
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Validate LLM section
    llm = config.get("llm", {})
    
    if "provider" not in llm:
        errors.append("llm.provider is required")
    elif llm["provider"] not in ["ollama", "openai", "anthropic"]:
        errors.append(f"llm.provider must be one of: ollama, openai, anthropic (got '{llm['provider']}')")
    
    if "model" not in llm:
        errors.append("llm.model is required")
    elif not isinstance(llm["model"], str) or not llm["model"].strip():
        errors.append("llm.model must be a non-empty string")
    
    temperature = llm.get("temperature", 0.2)
    if not isinstance(temperature, (int, float)):
        errors.append("llm.temperature must be a number")
    elif temperature < 0.0 or temperature > 2.0:
        errors.append("llm.temperature must be between 0.0 and 2.0")
    
    # Validate paths section
    paths = config.get("paths", {})
    
    if "ignore" in paths:
        if not isinstance(paths["ignore"], list):
            errors.append("paths.ignore must be a list")
        elif not all(isinstance(item, str) for item in paths["ignore"]):
            errors.append("paths.ignore must contain only strings")
    
    if "logs" in paths:
        if not isinstance(paths["logs"], list):
            errors.append("paths.logs must be a list")
        elif not all(isinstance(item, str) for item in paths["logs"]):
            errors.append("paths.logs must contain only strings")
    
    # Validate RAG section
    rag = config.get("rag", {})
    
    chunk_size = rag.get("chunk_size", 1000)
    if not isinstance(chunk_size, int):
        errors.append("rag.chunk_size must be an integer")
    elif chunk_size <= 0 or chunk_size > 2000:
        errors.append("rag.chunk_size must be between 1 and 2000")
    
    chunk_overlap = rag.get("chunk_overlap", 200)
    if not isinstance(chunk_overlap, int):
        errors.append("rag.chunk_overlap must be an integer")
    elif chunk_overlap < 200 or chunk_overlap > 2000:
        errors.append("rag.chunk_size must be between 200 and 2000")
    
    top_k = rag.get("top_k", 6)
    if not isinstance(top_k, int):
        errors.append("rag.top_k must be an integer")
    elif top_k <= 0 or top_k > 20:
        errors.append("rag.top_k must be between 1 and 20")
    
    if "store" in rag:
        if rag["store"] not in ["chroma"]:
            errors.append(f"rag.store must be one of: chroma (got '{rag['store']}')")
    
    # Validate tools section
    tools = config.get("tools", {})
    
    for tool_name in ["code_search", "log_search", "config_check"]:
        if tool_name in tools and not isinstance(tools[tool_name], bool):
            errors.append(f"tools.{tool_name} must be true or false")
    
    # Validate analysis section
    analysis = config.get("analysis", {})
    
    max_steps = analysis.get("max_steps", 5)
    if not isinstance(max_steps, int):
        errors.append("analysis.max_steps must be an integer")
    elif max_steps <= 0 or max_steps > 20:
        errors.append("analysis.max_steps must be between 1 and 20")
    
    reasoning_style = analysis.get("reasoning_style", "concise")
    if reasoning_style not in ["concise", "detailed", "step-by-step"]:
        errors.append(f"analysis.reasoning_style must be one of: concise, detailed, step-by-step (got '{reasoning_style}')")
    
    # Raise all errors at once
    if errors:
        raise ValueError("\n  • " + "\n  • ".join(errors))
    
    return config