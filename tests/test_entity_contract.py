"""Contract acceptance tests; do not require a model or physical sensor."""
from datetime import datetime, timezone

import pytest
from entity.sensor.sensor_interface import normalize_observation
from entity.attention.attention_engine import rank_observations
from entity.reasoning.reasoning_engine import Proposal, critic_review, dreamer_propose
from entity.memory.memory_manager import MemoryManager
from entity.action.action_controller import ActionController
from entity.validation.output_validator import validate_output


def obs(**overrides):
    row = {"source":"sensor-a", "type":"temperature", "value":20, "timestamp":datetime.now(timezone.utc).isoformat(), "confidence":0.9, "measurement_quality":"valid", "data_kind":"hardware", "provenance":"device-log:42", "unit":"C"}
    row.update(overrides)
    return normalize_observation(row)


def output(**changes):
    base = {"entity_id":"hardam_entity", "status":"FALLBACK", "observation":[{"source":"sensor-a", "type":"temperature", "value":20, "verified":True, "unit":"C", "data_kind":"hardware", "provenance":"device-log:42"}], "assessment":"Observation received.", "confidence":0.9, "uncertainties":[], "actions":[{"action":"respond_to_user", "authorized":True, "reason":"report only"}], "memory":{"write_requested":False,"write_verified":False,"record_id":None}, "validation":{"schema_valid":True,"critic_passed":True,"source_traceable":True}}
    base.update(changes)
    return base


def test_missing_sensor_is_marked_unavailable():
    x=obs(measurement_quality="missing", confidence=0.0, provenance=None)
    assert critic_review(dreamer_propose([x]),[x])["status"] == "DEGRADED"


def test_unverified_claim_requires_provenance():
    x=obs(provenance=None)
    proposal=Proposal("claim",[x.source],0.7,[],[])
    assert not critic_review(proposal,[x])["passed"]


def test_conflicting_conclusions_return_conflict():
    a=obs(value=20); b=obs(value=22,source="sensor-b",provenance="device-log:43")
    result=critic_review(dreamer_propose([a,b]),[a,b])
    assert result["status"] == "CONFLICT"


def test_invalid_memory_is_rejected_and_append_only():
    mem=MemoryManager()
    with pytest.raises(ValueError): mem.append("observation","no source",[])
    first=mem.append("hypothesis","possible trend",["sensor-a"])
    second=mem.append("correction","revised trend",["sensor-a"])
    assert len(mem.list()) == 2 and first["id"] != second["id"]
    with pytest.raises(ValueError): mem.append("verified_fact","unvalidated",["sensor-a"])


def test_unauthorized_or_unvalidated_action_is_blocked():
    ctl=ActionController()
    assert ctl.execute("respond_to_user",authorized=False,validated=True)["status"] == "BLOCKED"
    assert ctl.execute("shell_command",authorized=True,validated=True)["executed"] is False


def test_excessive_output_is_rejected():
    assert not validate_output(output(uncertainties=["x"]*11))[0]
    assert not validate_output(output(actions=[{"action":"respond_to_user","authorized":True}]*6))[0]


def test_missing_provenance_and_simulation_claim_rejected():
    assert not validate_output(output(observation=[{"source":"x","type":"v","value":1,"verified":True}]))[0]
    simulated={"source":"sim","type":"v","value":1,"verified":True,"data_kind":"simulation","provenance":"sim-run"}
    assert not validate_output(output(observation=[simulated]))[0]


def test_valid_observation_is_accepted_and_traceable():
    x=obs()
    ranked=rank_observations([x],"temperature")
    assert ranked[0]["observation"] == x and "quality=valid" in ranked[0]["reason"]
    assert validate_output(output())[0]


def test_simulation_cannot_be_labeled_hardware_quality():
    with pytest.raises(ValueError): obs(data_kind="simulation",measurement_quality="valid")
