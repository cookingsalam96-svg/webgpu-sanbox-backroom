"""Dual-role proposal and critic interfaces; critic validates provenance and claims."""
from dataclasses import dataclass
from datetime import datetime
import math

@dataclass
class Proposal:
    assessment: str
    evidence: list
    confidence: float
    uncertainties: list
    actions: list
    claims: list = None


def dreamer_propose(observations, task=""):
    """Deterministic fallback implementing the Dreamer interface; injectable model adapter."""
    if not observations:
        return Proposal("No observations are available; request more evidence.", [], 0.0, ["sensor input unavailable"], [{"action":"request_clarification","authorized":True,"reason":"No evidence supplied"}], [])
    return Proposal(f"Assessment is limited to {len(observations)} supplied observation(s); task={task[:300]}", [o.source for o in observations], min(o.confidence for o in observations), ["Interpretation may be incomplete; evidence source has not necessarily been independently verified."], [{"action":"respond_to_user","authorized":True,"reason":"Return bounded assessment"}], [])


def _timestamp(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None


def _values_conflict(a, b, *, absolute_tolerance=0.1, relative_tolerance=0.01, time_window_seconds=5.0):
    """Compare only same-unit, near-simultaneous values; avoid treating normal sensor noise as conflict."""
    if a.unit != b.unit:
        return False
    ta, tb = _timestamp(a.timestamp), _timestamp(b.timestamp)
    if ta is None or tb is None:
        return True  # malformed timing is fail-closed when values otherwise appear comparable
    if abs((ta - tb).total_seconds()) > time_window_seconds:
        return False
    if isinstance(a.value, bool) or isinstance(b.value, bool):
        return a.value != b.value
    if isinstance(a.value, (int, float)) and isinstance(b.value, (int, float)):
        if not math.isfinite(float(a.value)) or not math.isfinite(float(b.value)):
            return True
        tolerance = max(absolute_tolerance, relative_tolerance * max(abs(a.value), abs(b.value)))
        return abs(a.value - b.value) > tolerance
    return a.value != b.value


def critic_review(proposal, observations):
    sources = {o.source for o in observations if o.provenance}
    unsupported = sorted(set(proposal.evidence) - sources)
    by_type = {}
    for observation in observations:
        if observation.measurement_quality != "missing":
            by_type.setdefault(observation.type, []).append(observation)
    contradictions = sorted(kind for kind, group in by_type.items() if any(_values_conflict(group[i], group[j]) for i in range(len(group)) for j in range(i + 1, len(group))))
    invalid_claims = []
    for claim in proposal.claims or []:
        if not isinstance(claim, dict) or not isinstance(claim.get("text"), str) or not claim.get("evidence_sources"):
            invalid_claims.append("claim lacks evidence sources")
        elif not set(claim["evidence_sources"]).issubset(sources):
            invalid_claims.append("claim references unsupported source")
        elif claim.get("evidence_class") == "E1" and not any(o.evidence_class == "E1" and o.source in claim["evidence_sources"] for o in observations):
            invalid_claims.append("E1 claim lacks page-cited experimental evidence")
    if contradictions:
        return {"status":"CONFLICT","passed":False,"unsupported":unsupported,"contradictions":contradictions,"invalid_claims":invalid_claims,"reason":"Conflicting near-simultaneous values for observation type(s): "+", ".join(contradictions)}
    if unsupported or invalid_claims or any(o.measurement_quality == "missing" for o in observations):
        return {"status":"DEGRADED","passed":False,"unsupported":unsupported,"contradictions":[],"invalid_claims":invalid_claims,"reason":"Evidence is incomplete, untraceable, or claim support failed."}
    return {"status":"FALLBACK","passed":True,"unsupported":[],"contradictions":[],"invalid_claims":[],"reason":"Evidence references are traceable; this is not independent scientific verification."}
