"""Validated input boundary for real or simulated sensor adapters."""
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Optional
from entity.evidence import EvidenceClass, validate_evidence_class

DATA_KINDS = {"hardware", "simulation", "user_supplied", "derived"}
QUALITIES = {"valid", "degraded", "missing", "simulated", "unknown"}
# Page-located citation shape is a provenance-format check, not proof the cited source supports the claim.
E1_CITATION = re.compile(r"^[A-Za-z0-9._/-]+#page=[1-9][0-9]*(?:#(?:figure|table|equation)=[A-Za-z0-9._-]+)?$")

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
    evidence_class: str = "E4"

    def to_dict(self):
        return {"source": self.source, "type": self.type, "value": self.value, "timestamp": self.timestamp, "confidence": self.confidence, "measurement_quality": self.measurement_quality, "data_kind": self.data_kind, "provenance": self.provenance, "unit": self.unit, "evidence_class": self.evidence_class}


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
    if data["data_kind"] not in DATA_KINDS or data["measurement_quality"] not in QUALITIES:
        raise ValueError("unsupported data kind or quality")
    if data["data_kind"] == "simulation" and data["measurement_quality"] not in {"simulated", "unknown"}:
        raise ValueError("simulation data must be marked simulated or unknown")
    evidence = validate_evidence_class(data.get("evidence_class", "E5" if data["data_kind"] == "simulation" else "E4"), data["data_kind"])
    provenance = data["provenance"]
    if provenance is not None and (not isinstance(provenance, str) or len(provenance) > 512):
        raise ValueError("provenance must be null or a string up to 512 characters")
    if evidence is EvidenceClass.E1:
        if data["data_kind"] != "hardware":
            raise ValueError("E1 is reserved for source-backed experimental evidence")
        if not provenance or not E1_CITATION.fullmatch(provenance):
            raise ValueError("E1 requires a page-located source citation such as 'paper-id#page=4'; format validation is not source verification")
    unit = data.get("unit")
    if unit is not None and (not isinstance(unit, str) or len(unit) > 32):
        raise ValueError("unit must be null or a string up to 32 characters")
    return Observation(data["source"], data["type"], data["value"], data["timestamp"], float(confidence), data["measurement_quality"], data["data_kind"], provenance, unit, evidence.value)
