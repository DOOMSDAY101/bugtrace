from pathlib import Path
import json


def ensure_state_dir(project_root: Path) -> Path:
    state_dir = project_root / ".bugtrace"
    state_dir.mkdir(exist_ok=True)

    (state_dir / "logs").mkdir(exist_ok=True)

    manifest = state_dir / "manifest.json"
    if not manifest.exists():
        manifest.write_text(json.dumps({}, indent=2))

    state = state_dir / "state.json"
    if not state.exists():
        state.write_text(
            json.dumps(
                {
                    "config_hash": None,
                    "last_indexed": None,
                },
                indent=2,
            )
        )

    return state_dir
