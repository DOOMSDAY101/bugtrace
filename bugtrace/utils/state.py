# bugtrace/utils/state.py
from pathlib import Path
import json
from typing import Dict, Optional, List
from datetime import datetime


class StateManager:
    """
    Manages .bugtrace/state.json for tracking config changes,
    index status, and project metadata.
    """
    
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_path = state_dir / "state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load state.json or create default"""
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding='utf-8'))
            except:
                return self._default_state()
        return self._default_state()
    
    def _default_state(self) -> dict:
        """Default state structure"""
        
        return {
            "version": "0.1.0",
            "created_at": datetime.now().isoformat(),
            "last_scan": None,
            "last_index": None,
            "config_hash": None,
            "indexed_files": {},  # {filepath: hash}
            "metadata": {
                "total_files": 0,
                "total_chunks": 0,
                "last_analysis": None,
            }
        }
    
    def save(self):
        """Save state to disk"""
        self.state_path.write_text(
            json.dumps(self.state, indent=2),
            encoding='utf-8'
        )
    
    def update_scan_time(self):
        """Update last scan timestamp"""
        self.state["last_scan"] = datetime.now().isoformat()
        self.save()
    
    def update_index_time(self):
        """Update last index timestamp"""
        self.state["last_index"] = datetime.now().isoformat()
        self.save()
    
    def update_config_hash(self, new_hash: str):
        """Update config hash"""
        self.state["config_hash"] = new_hash
        self.save()
    
    def config_changed(self, current_hash: str) -> bool:
        """Check if config has changed since last index"""
        return self.state.get("config_hash") != current_hash
    
    def get_files_to_index(self, manifest: Dict[str, str]) -> Dict[str, str]:
        """
        Compare manifest with indexed files.
        Returns dict of files that need indexing {filepath: hash}
        """
        indexed = self.state.get("indexed_files", {})
        files_to_index = {}
        
        for filepath, file_hash in manifest.items():
            # File is new or changed
            if filepath not in indexed or indexed[filepath] != file_hash:
                files_to_index[filepath] = file_hash
        
        return files_to_index
    
    def mark_files_indexed(self, files: Dict[str, str]):
        """Mark files as indexed"""
        if "indexed_files" not in self.state:
            self.state["indexed_files"] = {}
        
        self.state["indexed_files"].update(files)
        self.save()
    
    def update_metadata(self, **kwargs):
        """Update metadata fields"""
        if "metadata" not in self.state:
            self.state["metadata"] = {}
        
        self.state["metadata"].update(kwargs)
        self.save()