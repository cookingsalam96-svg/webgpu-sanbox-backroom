"""Append-only traceable memory. No update/delete API is exposed."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4

RECORD_TYPES = {"observation", "decision", "verified_fact", "hypothesis", "correction", "rejected_claim"}

class MemoryManager:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self._records = []
        self._lock = RLock()

    def append(self, record_type, content, source_ids, *, validated=False):
        if record_type not in RECORD_TYPES or not isinstance(content, str) or not content.strip() or len(content) > 4000:
            raise ValueError("invalid memory record")
        if not isinstance(source_ids, list) or not source_ids or any(not isinstance(s, str) or not s.strip() for s in source_ids):
            raise ValueError("memory requires non-empty source identifiers")
        if record_type == "verified_fact" and not validated:
            raise ValueError("hypotheses cannot be promoted to verified facts without validation")
        row = {"id": uuid4().hex, "record_type": record_type, "content": content.strip(), "source_ids": list(source_ids), "created_at": datetime.now(timezone.utc).isoformat(), "validated": bool(validated)}
        with self._lock:
            self._records.append(row)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row.copy()

    def list(self):
        with self._lock:
            return [row.copy() for row in self._records]
