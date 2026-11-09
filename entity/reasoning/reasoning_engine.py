"""Dual-role proposal and critic contracts with deterministic evidence checks."""
from dataclasses import dataclass

@dataclass
class Proposal:
    assessment: str
    evidence: list
    confidence: float
    uncertainties: list
    actions: list


def dreamer_propose(observations, task=""):
    """Minimal deterministic Dreamer fallback; injectable LLMs can implement this interface."""
    if not observations:
        return Proposal("No observations are available; request more evidence.", [], 0.0, ["sensor input unavailable"], [{"action": "request_clarification", "authorized": True, "reason": "No evidence supplied"}])
    refs = [o.source for o in observations]
    return Proposal(f"Assessment is limited to {len(observations)} supplied observation(s); task={task[:300]}", refs, min(o.confidence for o in observations), ["Interpretation may be incomplete; evidence source has not necessarily been independently verified."], [{"action": "respond_to_user", "authorized": True, "reason": "Return bounded assessment"}])


def critic_review(proposal, observations):
    """Verify referenced sources and detect contradictions among same-type values."""
    sources = {o.source for o in observations if o.provenance}
    referenced = set(proposal.evidence)
    unsupported = sorted(referenced - sources)
    contradictions = []
    by_type = {}
    for o in observations:
        if o.measurement_quality != "missing":
            by_type.setdefault(o.type, set()).add(repr(o.value))
    for kind, values in by_type.items():
        if len(values) > 1:
            contradictions.append(kind)
    if contradictions:
        return {"status": "CONFLICT", "passed": False, "unsupported": unsupported, "contradictions": contradictions, "reason": "Conflicting values for observation type(s): " + ", ".join(sorted(contradictions))}
    if unsupported:
        return {"status": "DEGRADED", "passed": False, "unsupported": unsupported, "contradictions": [], "reason": "Evidence is missing provenance or does not match a provenance-bearing source."}
    if any(o.measurement_quality == "missing" for o in observations):
        return {"status": "DEGRADED", "passed": False, "unsupported": [], "contradictions": [], "reason": "At least one sensor is marked missing."}
    return {"status": "FALLBACK", "passed": True, "unsupported": [], "contradictions": [], "reason": "Evidence references match provenance-bearing observations; this is not independent scientific verification."}
