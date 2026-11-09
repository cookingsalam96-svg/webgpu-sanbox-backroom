"""Append-only traceable memory with optional JSONL persistence and reload."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4
from entity.evidence import validate_evidence_class

RECORD_TYPES = {"observation", "decision", "verified_fact", "hypothesis", "correction", "rejected_claim"}

class MemoryManager:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self._records = []
        self._lock = RLock()
        if self.path and self.path.exists():
            with self.path.open(encoding="utf-8") as f:
                for line_number, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                        self._validate_record(row)
                        self._records.append(row)
                    except (ValueError, TypeError, json.JSONDecodeError) as exc:
                        raise ValueError(f"invalid memory record at line {line_number}: {exc}") from exc

    @staticmethod
    def _validate_record(row):
        if not isinstance(row, dict) or not all(row.get(k) for k in ("id", "record_type", "content", "source_ids", "created_at", "provenance")):
            raise ValueError("record requires id, type, content, source_ids, timestamp and provenance")
        if row["record_type"] not in RECORD_TYPES or not isinstance(row["source_ids"], list) or not row["source_ids"]:
            raise ValueError("invalid record type or empty source identifiers")
        if not isinstance(row["provenance"], list) or not row["provenance"] or any(not isinstance(p, str) or not p.strip() for p in row["provenance"]):
            raise ValueError("every record requires provenance")
        validate_evidence_class(row.get("evidence_class"))
        if row["record_type"] == "verified_fact" and not row.get("validated"):
            raise ValueError("unvalidated verified_fact")

    def append(self, record_type, content, source_ids, *, validated=False, evidence_class="E4", provenance=None):
        if record_type not in RECORD_TYPES or not isinstance(content, str) or not content.strip() or len(content) > 4000:
            raise ValueError("invalid memory record")
        if not isinstance(source_ids, list) or not source_ids or any(not isinstance(s, str) or not s.strip() for s in source_ids):
            raise ValueError("memory requires non-empty source identifiers")
        if not isinstance(provenance, list) or not provenance or any(not isinstance(p, str) or not p.strip() for p in provenance):
            raise ValueError("memory requires provenance for every record")
        validate_evidence_class(evidence_class)
        if record_type == "verified_fact" and not validated:
            raise ValueError("hypotheses cannot be promoted to verified facts without validation")
        row = {"id": uuid4().hex, "record_type": record_type, "content": content.strip(), "source_ids": list(source_ids), "created_at": datetime.now(timezone.utc).isoformat(), "validated": bool(validated), "evidence_class": evidence_class, "provenance": list(provenance)}
        with self._lock:
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
            self._records.append(row)
        return row.copy()

    def list(self):
        with self._lock:
            return [row.copy() for row in self._records]
