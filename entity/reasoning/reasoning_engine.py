"""Dual-role proposal and critic interfaces; critic validates provenance and claims."""
from dataclasses import dataclass

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


def critic_review(proposal, observations):
    sources = {o.source for o in observations if o.provenance}
    unsupported = sorted(set(proposal.evidence) - sources)
    contradictions = []
    by_type = {}
    for o in observations:
        if o.measurement_quality != "missing": by_type.setdefault(o.type, set()).add(repr(o.value))
    contradictions = sorted(kind for kind, values in by_type.items() if len(values) > 1)
    invalid_claims = []
    for claim in proposal.claims or []:
        if not isinstance(claim, dict) or not isinstance(claim.get("text"), str) or not claim.get("evidence_sources"):
            invalid_claims.append("claim lacks evidence sources")
        elif not set(claim["evidence_sources"]).issubset(sources):
            invalid_claims.append("claim references unsupported source")
        elif claim.get("evidence_class") == "E1" and not any(o.evidence_class == "E1" and o.source in claim["evidence_sources"] for o in observations):
            invalid_claims.append("E1 claim lacks experimentally verified source")
    if contradictions:
        return {"status":"CONFLICT","passed":False,"unsupported":unsupported,"contradictions":contradictions,"invalid_claims":invalid_claims,"reason":"Conflicting values for observation type(s): "+", ".join(contradictions)}
    if unsupported or invalid_claims or any(o.measurement_quality == "missing" for o in observations):
        return {"status":"DEGRADED","passed":False,"unsupported":unsupported,"contradictions":[],"invalid_claims":invalid_claims,"reason":"Evidence is incomplete, untraceable, or claim support failed."}
    return {"status":"FALLBACK","passed":True,"unsupported":[],"contradictions":[],"invalid_claims":[],"reason":"Evidence references are traceable; this is not independent scientific verification."}
