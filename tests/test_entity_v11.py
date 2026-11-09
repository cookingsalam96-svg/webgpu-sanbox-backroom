"""V1.1 tests; E1 now uses page-located citation provenance."""
import json
from datetime import datetime, timezone
import pytest
from entity.evidence import validate_evidence_class
from entity.sensor.sensor_interface import normalize_observation
from entity.sensor.sensor_simulator import simulate_torsional_observation
from entity.reasoning.reasoning_engine import Proposal, critic_review
from entity.runtime import EntityRuntime
from entity.memory.memory_manager import MemoryManager
from entity.validation.output_validator import validate_output


def obs(source="sensor-a", value=20, evidence="E1", kind="hardware", provenance="paper.pdf#page=4"):
    return normalize_observation({"source":source,"type":"temperature","value":value,"timestamp":datetime.now(timezone.utc).isoformat(),"confidence":0.9,"measurement_quality":"valid","data_kind":kind,"evidence_class":evidence,"provenance":provenance,"unit":"C"})


def test_evidence_class_rules():
    assert validate_evidence_class("E3").value == "E3"
    with pytest.raises(ValueError): validate_evidence_class("E5", "hardware")
    with pytest.raises(ValueError): validate_evidence_class("E1", "simulation")


def test_dreamer_critic_detects_contradictions():
    a,b=obs(value=20),obs(source="sensor-b",value=22,provenance="paper.pdf#page=5")
    proposal=Proposal("20 C",["sensor-a"],0.8,[],[],claims=[])
    assert critic_review(proposal,[a,b])["status"] == "CONFLICT"


def test_unsupported_claim_is_rejected():
    o=obs()
    proposal=Proposal("claim",["not-a-source"],0.9,[],[],claims=[{"text":"claim","evidence_sources":["not-a-source"],"evidence_class":"E1"}])
    assert critic_review(proposal,[o])["passed"] is False


def test_persistent_memory_reload_and_provenance(tmp_path):
    path=tmp_path/"memory.jsonl"
    mem=MemoryManager(path)
    record=mem.append("hypothesis","possible trend",["sensor-a"],evidence_class="E4",provenance=["device-log:42"])
    restored=MemoryManager(path)
    assert restored.list()[0]["id"] == record["id"]
    assert restored.list()[0]["provenance"] == ["device-log:42"]


def test_memory_requires_provenance():
    with pytest.raises(ValueError): MemoryManager().append("decision","x",["sensor"])


def test_simulated_sensor_is_explicitly_e5():
    simulated=simulate_torsional_observation(phase=1.0)
    assert simulated.data_kind == "simulation" and simulated.evidence_class == "E5"
    assert simulated.measurement_quality == "simulated"
    result=EntityRuntime().process([simulated])
    assert result["observation"][0]["verified"] is False
    assert validate_output(result)[0]


def test_runtime_fail_closed_and_bounded_output():
    result=EntityRuntime().process([obs()],task="report",remember=True,authorize_response=False)
    assert result["validation"]["schema_valid"]
    assert result["actions"][0]["authorized"] is False
    assert result["memory"]["write_verified"] is True
    with pytest.raises(ValueError): EntityRuntime().process([obs()]*21)


def test_legacy_observation_defaults_to_hypothesis_not_experimental_fact():
    row={"source":"sensor","type":"x","value":1,"timestamp":datetime.now(timezone.utc).isoformat(),"confidence":0.5,"measurement_quality":"valid","data_kind":"hardware","provenance":"log"}
    assert normalize_observation(row).evidence_class == "E4"
