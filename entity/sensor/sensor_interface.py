"""Validated input boundary for real or simulated sensor adapters."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

DATA_KINDS = {"hardware", "simulation", "user_supplied", "derived"}
QUALITIES = {"valid", "degraded", "missing", "simulated", "unknown"}

@dataclass(frozen=True)
class Observation:
    source: str
    type: str
    value: Any
    timestamp: str
    confidence: float
    measurement_quality: str
    data_kind: str
    provenance: Optional[str]
    unit: Optional[str] = None

    def to_dict(self):
        return {"source": self.source, "type": self.type, "value": self.value,
                "timestamp": self.timestamp, "confidence": self.confidence,
                "measurement_quality": self.measurement_quality,
                "data_kind": self.data_kind, "provenance": self.provenance, "unit": self.unit}


def normalize_observation(data):
    if not isinstance(data, dict):
        raise ValueError("observation must be an object")
    required = {"source", "type", "value", "timestamp", "confidence", "measurement_quality", "data_kind", "provenance"}
    if not required.issubset(data):
        raise ValueError("observation is missing required fields")
    if not isinstance(data["source"], str) or not data["source"].strip() or len(data["source"]) > 128:
        raise ValueError("source must be a non-empty string of at most 128 characters")
    if not isinstance(data["type"], str) or not data["type"].strip() or len(data["type"]) > 64:
        raise ValueError("type must be a non-empty string of at most 64 characters")
    try:
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ValueError("timestamp must be ISO-8601")
    confidence = data["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be a number in [0, 1]")
    if data["data_kind"] not in DATA_KINDS:
        raise ValueError("unsupported data_kind")
    if data["measurement_quality"] not in QUALITIES:
        raise ValueError("unsupported measurement_quality")
    if data["data_kind"] == "simulation" and data["measurement_quality"] not in {"simulated", "unknown"}:
        raise ValueError("simulation data must be marked simulated or unknown")
    provenance = data["provenance"]
    if provenance is not None and (not isinstance(provenance, str) or len(provenance) > 512):
        raise ValueError("provenance must be null or a string up to 512 characters")
    unit = data.get("unit")
    if unit is not None and (not isinstance(unit, str) or len(unit) > 32):
        raise ValueError("unit must be null or a string up to 32 characters")
    return Observation(data["source"], data["type"], data["value"], data["timestamp"], float(confidence), data["measurement_quality"], data["data_kind"], provenance, unit)
