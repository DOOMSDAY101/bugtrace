from pathlib import Path
import hashlib
import json
from typing import Dict, List
from fnmatch import fnmatch


def ensure_state_dir(project_root: Path) -> Path:
    state_dir = project_root / ".bugtrace"
    state_dir.mkdir(exist_ok=True)

    (state_dir / "logs").mkdir(exist_ok=True)

    manifest = state_dir / "manifest.json"
    if not manifest.exists():
        manifest.write_text(json.dumps({}, indent=2))

    # state = state_dir / "state.json"
    # if not state.exists():
    #     state.write_text(
    #         json.dumps(
    #             {
    #                 "config_hash": None,
    #             },
    #             indent=2,
    #         )
    #     )

    return state_dir

def hash_file(file_path: Path) -> str:
    """Return SHA256 hash of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def should_ignore(path: Path, project_root: Path, ignore_patterns: List[str]) -> bool:
    """
    Check if a path should be ignored based on patterns.
    Supports:
    - Exact folder names (__pycache__, node_modules)
    - Glob patterns (*.pyc, *.log)
    - Hidden folders/files (.git, .bugtrace) - must match exactly with the dot
    - Relative paths
    """
    # Get relative path from project root
    try:
        rel_path = path.relative_to(project_root)
    except ValueError:
        return False
    
    rel_path_str = str(rel_path).replace('\\', '/')
    
    for pattern in ignore_patterns:
        # Special handling for patterns starting with . (hidden files/folders)
        if pattern.startswith('.'):
            # For hidden patterns, only match if the part starts with .
            for part in rel_path.parts:
                if part == pattern or part == pattern.lstrip('.'):
                    # Exact match with or without the dot
                    if part.startswith('.'):
                        return True
            
            # Check filename if it's a hidden file
            if path.name == pattern or (path.name.startswith('.') and path.name == pattern):
                return True
        else:
            # For non-hidden patterns, use normal matching
            # Check if any part of the path matches the pattern (for folder names)
            for part in rel_path.parts:
                if fnmatch(part, pattern):
                    return True
            
            # Check the full relative path
            if fnmatch(rel_path_str, pattern):
                return True
            
            # Check just the filename
            if fnmatch(path.name, pattern):
                return True
    
    return False

def walk_project(project_root: Path, ignore: List[str] = None) -> List[Path]:
    """
    Recursively walk project directory and return list of files.
    Supports ignore patterns like .gitignore:
      - exact filenames/folders (__pycache__, node_modules)
      - glob patterns (*.pyc, *.log)
      - hidden folders starting with . (.git, .bugtrace) - won't match regular folders
      - folder names anywhere in the tree
    """
    ignore = ignore or []
    all_files = []
    
    def _walk(current_path: Path):
        """Recursive walker that respects ignore patterns"""
        try:
            for item in current_path.iterdir():
                # Check if this item should be ignored
                if should_ignore(item, project_root, ignore):
                    continue
                
                if item.is_dir():
                    # Recursively walk subdirectory
                    _walk(item)
                elif item.is_file():
                    all_files.append(item)
        except PermissionError:
            # Skip directories we don't have permission to read
            pass
    
    _walk(project_root)
    return all_files

def load_manifest(state_dir: Path) -> Dict:
    manifest_path = state_dir / "manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return {}

def save_manifest(state_dir: Path, manifest: Dict):
    manifest_path = state_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

def update_manifest(state_dir: Path, files: List[Path]) -> Dict:
    """
    Update manifest with file hashes.
    Removes files that are no longer tracked (either deleted or now ignored).
    Returns stats: {new, changed, unchanged, removed}
    """
    old_manifest = load_manifest(state_dir)
    new_manifest = {}
    stats = {"new": 0, "changed": 0, "unchanged": 0, "removed": 0}
    
    # Track which files are currently being scanned
    current_files = {str(filepath) for filepath in files}
    
    # Process current files
    for filepath in files:
        file_key = str(filepath)
        current_hash = hash_file(filepath)
        
        if file_key not in old_manifest:
            stats["new"] += 1
        elif old_manifest[file_key] != current_hash:
            stats["changed"] += 1
        else:
            stats["unchanged"] += 1
        
        new_manifest[file_key] = current_hash
    
    # Count removed files (were in old manifest but not in current scan)
    for old_file in old_manifest.keys():
        if old_file not in current_files:
            stats["removed"] += 1
    
    save_manifest(state_dir, new_manifest)
    return stats

    # """
    # Hash files and update manifest.json.
    # Returns dict with stats: new, changed, unchanged.
    # """
    # manifest = load_manifest(state_dir)
    # stats = {"new": 0, "changed": 0, "unchanged": 0}

    # for file_path in files:
    #     file_str = str(file_path)
    #     file_hash = hash_file(file_path)

    #     if file_str not in manifest:
    #         stats["new"] += 1
    #     elif manifest[file_str] != file_hash:
    #         stats["changed"] += 1
    #     else:
    #         stats["unchanged"] += 1

    #     manifest[file_str] = file_hash

    # save_manifest(state_dir, manifest)
    # return stats