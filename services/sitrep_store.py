"""
services/sitrep_store.py
------------------------
Persistent storage for SITREPs, detection contexts, and chat histories.

Stores data in a JSON file to survive server restarts.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import config

logger = logging.getLogger(__name__)


class SitrepStore:
    """
    Manages persistent storage of SITREPs and chat histories.
    
    Data structure:
    {
        "scan_id": {
            "timestamp": "2024-02-15T10:30:00",
            "detection_context": "...",
            "sitrep": "...",
            "model": "claude-sonnet-4-20250514",
            "tokens": 524,
            "chat_history": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
    }
    """
    
    def __init__(self, store_path: str = None):
        self.store_path = Path(store_path or config.SITREP_STORE_PATH)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_store_exists()
    
    def _ensure_store_exists(self):
        """Create store file if it doesn't exist."""
        if not self.store_path.exists():
            self._write_store({})
    
    def _read_store(self) -> Dict:
        """Read entire store from disk."""
        try:
            with open(self.store_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not read store, initializing empty")
            return {}
    
    def _write_store(self, data: Dict):
        """Write entire store to disk."""
        try:
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write store: {e}")
    
    def save_sitrep(self, scan_id: str, detection_context: str, 
                    sitrep: str, model: str, tokens: int):
        """
        Save a SITREP for a scan.
        
        Args:
            scan_id: Unique scan identifier
            detection_context: Full detection context string
            sitrep: Generated SITREP text
            model: Claude model used
            tokens: Total tokens used
        """
        store = self._read_store()
        
        store[scan_id] = {
            "timestamp": datetime.utcnow().isoformat(),
            "detection_context": detection_context,
            "sitrep": sitrep,
            "model": model,
            "tokens": tokens,
            "chat_history": []
        }
        
        self._write_store(store)
        logger.info(f"Saved SITREP for scan {scan_id}")
    
    def get_sitrep(self, scan_id: str) -> Optional[Dict]:
        """
        Retrieve a SITREP by scan ID.
        
        Args:
            scan_id: Unique scan identifier
            
        Returns:
            Dict with SITREP data or None if not found
        """
        store = self._read_store()
        return store.get(scan_id)
    
    def add_chat_message(self, scan_id: str, role: str, content: str):
        """
        Add a message to the chat history for a scan.
        
        Args:
            scan_id: Unique scan identifier
            role: "user" or "assistant"
            content: Message content
        """
        store = self._read_store()
        
        if scan_id not in store:
            logger.warning(f"Scan {scan_id} not found, cannot add chat message")
            return
        
        store[scan_id]["chat_history"].append({
            "role": role,
            "content": content
        })
        
        self._write_store(store)
        logger.debug(f"Added {role} message to scan {scan_id}")
    
    def get_chat_history(self, scan_id: str) -> List[Dict]:
        """
        Get chat history for a scan.
        
        Args:
            scan_id: Unique scan identifier
            
        Returns:
            List of chat messages or empty list if not found
        """
        store = self._read_store()
        scan_data = store.get(scan_id, {})
        return scan_data.get("chat_history", [])
    
    def cleanup_old_scans(self, keep_last_n: int = 100):
        """
        Remove old scans to prevent unbounded growth.
        
        Args:
            keep_last_n: Number of most recent scans to keep
        """
        store = self._read_store()
        
        if len(store) <= keep_last_n:
            return
        
        # Sort by timestamp, keep most recent
        sorted_scans = sorted(
            store.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )
        
        new_store = dict(sorted_scans[:keep_last_n])
        self._write_store(new_store)
        
        removed = len(store) - len(new_store)
        logger.info(f"Cleaned up {removed} old scans, kept {len(new_store)}")


# Global store instance
_store = None

def get_store() -> SitrepStore:
    """Get or create the global SitrepStore instance."""
    global _store
    if _store is None:
        _store = SitrepStore()
    return _store
