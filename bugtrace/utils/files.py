from pathlib import Path
from datetime import datetime


def resolve_markdown_path(export_md: str | None) -> Path:
    """
    Resolve and validate markdown export path.
    
    Rules:
    - None → auto-generate filename in CWD
    - Directory → auto-generate filename inside it
    - Missing .md → append .md
    """
    if export_md is None:
        filename = f"bugtrace-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        return Path.cwd() / filename

    path = Path(export_md).expanduser()

    # If directory, generate filename inside it
    if path.exists() and path.is_dir():
        filename = f"bugtrace-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        return path / filename

    # Ensure .md extension
    if path.suffix != ".md":
        path = path.with_suffix(".md")

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    return path.resolve()
