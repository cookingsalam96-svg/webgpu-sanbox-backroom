"""Fail-closed authorization and action audit log."""
from datetime import datetime, timezone

ALLOWED = {"respond_to_user", "store_validated_memory", "run_local_analysis", "request_clarification", "generate_report"}

class ActionController:
    def __init__(self):
        self.audit_log = []

    def execute(self, action, *, authorized=False, validated=False):
        allowed = action in ALLOWED and authorized is True and validated is True
        row = {"action": action, "authorized": bool(authorized), "validated": bool(validated), "executed": allowed, "status": "EXECUTED" if allowed else "BLOCKED", "timestamp": datetime.now(timezone.utc).isoformat()}
        self.audit_log.append(row)
        return row.copy()
