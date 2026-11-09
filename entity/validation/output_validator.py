"""Strict bounded output validation (standard-library implementation)."""
STATUSES = {"READY", "FALLBACK", "DEGRADED", "CONFLICT", "BLOCKED"}
TOP = {"entity_id", "status", "observation", "assessment", "confidence", "uncertainties", "actions", "memory", "validation"}


def validate_output(data):
    errors = []
    if not isinstance(data, dict):
        return False, ["output must be an object"]
    if set(data) != TOP:
        errors.append("top-level keys must match entity output contract")
    if not isinstance(data.get("entity_id"), str) or len(data.get("entity_id", "")) > 64:
        errors.append("invalid entity_id")
    if data.get("status") not in STATUSES:
        errors.append("invalid status")
    observations = data.get("observation")
    if not isinstance(observations, list) or len(observations) > 20:
        errors.append("observation must be an array of at most 20")
    else:
        required = {"source", "type", "value", "verified"}
        for i, item in enumerate(observations):
            if not isinstance(item, dict) or not required.issubset(item) or set(item) - (required | {"unit", "data_kind", "provenance"}):
                errors.append(f"invalid observation[{i}]")
                continue
            if not isinstance(item["source"], str) or len(item["source"]) > 128 or not isinstance(item["type"], str) or len(item["type"]) > 64 or type(item["verified"]) is not bool:
                errors.append(f"invalid observation fields[{i}]")
            if item.get("data_kind") == "simulation" and item["verified"]:
                errors.append(f"simulation cannot be represented as verified hardware measurement[{i}]")
            if item["verified"] and not item.get("provenance"):
                errors.append(f"verified observation requires provenance[{i}]")
    assessment = data.get("assessment")
    if not isinstance(assessment, str) or len(assessment) > 4000:
        errors.append("assessment must be a string of at most 4000 characters")
    confidence = data.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence must be in [0, 1]")
    uncertainties = data.get("uncertainties")
    if not isinstance(uncertainties, list) or len(uncertainties) > 10 or any(not isinstance(x, str) or len(x) > 500 for x in uncertainties):
        errors.append("uncertainties must contain at most 10 strings up to 500 characters")
    actions = data.get("actions")
    if not isinstance(actions, list) or len(actions) > 5:
        errors.append("actions must be an array of at most 5")
    else:
        for i, action in enumerate(actions):
            if not isinstance(action, dict) or not {"action", "authorized"}.issubset(action) or set(action) - {"action", "authorized", "reason"} or not isinstance(action.get("action"), str) or len(action.get("action", "")) > 128 or type(action.get("authorized")) is not bool:
                errors.append(f"invalid actions[{i}]")
    memory = data.get("memory")
    if not isinstance(memory, dict) or set(memory) - {"write_requested", "write_verified", "record_id"} or not {"write_requested", "write_verified"}.issubset(memory) or type(memory.get("write_requested")) is not bool or type(memory.get("write_verified")) is not bool:
        errors.append("invalid memory contract")
    validation = data.get("validation")
    if not isinstance(validation, dict) or set(validation) != {"schema_valid", "critic_passed", "source_traceable"} or any(type(validation.get(k)) is not bool for k in ("schema_valid", "critic_passed", "source_traceable")):
        errors.append("invalid validation contract")
    return not errors, errors
