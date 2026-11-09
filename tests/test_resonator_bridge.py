"""Regression tests for V1.1 review fixes and notebook adapter contract."""
import json
from datetime import datetime, timedelta, timezone

import pytest
from entity.sensor.sensor_interface import normalize_observation
from entity.reasoning.reasoning_engine import Proposal, critic_review
from entity.runtime import EntityRuntime
from entity.memory.memory_manager import MemoryManager
from entity.adapters.resonator_bridge import ResonatorBridge, readout_to_observations


def make_obs(source="s1", value=20, timestamp=None, unit="C", evidence="E4", kind="hardware", provenance="device-log"):
    return normalize_observation({"source":source,"type":"temp","value":value,"timestamp":(timestamp or datetime.now(timezone.utc)).isoformat(),"confidence":0.8,"measurement_quality":"simulated" if kind=="simulation" else "valid","data_kind":kind,"evidence_class":evidence,"provenance":provenance,"unit":unit})


def test_e1_requires_page_located_reference_and_import_is_valid():
    with pytest.raises(ValueError): make_obs(evidence="E1",provenance="device-log:42")
    assert make_obs(evidence="E1",provenance="paper.pdf#page=4").evidence_class == "E1"


def test_small_same_unit_near_time_variation_is_not_conflict():
    now=datetime.now(timezone.utc)
    a,b=make_obs(value=20,timestamp=now),make_obs(source="s2",value=20.05,timestamp=now+timedelta(seconds=1))
    assert critic_review(Proposal("ok",["s1","s2"],0.8,[],[]),[a,b])["status"] == "FALLBACK"


def test_conflicting_value_and_unit_or_old_samples():
    now=datetime.now(timezone.utc)
    a,b=make_obs(value=20,timestamp=now),make_obs(source="s2",value=25,timestamp=now+timedelta(seconds=1))
    assert critic_review(Proposal("x",["s1","s2"],0.8,[],[]),[a,b])["status"] == "CONFLICT"
    c=make_obs(source="s3",value=25,timestamp=now+timedelta(seconds=30))
    assert critic_review(Proposal("x",["s1","s3"],0.8,[],[]),[a,c])["status"] == "FALLBACK"


def test_old_memory_migrates_as_e4(tmp_path):
    path=tmp_path/"old.jsonl"
    old={"id":"old","record_type":"decision","content":"legacy","source_ids":["sensor"],"created_at":"2025-01-01T00:00:00+00:00","validated":False}
    path.write_text(json.dumps(old)+"\n")
    restored=MemoryManager(path)
    assert restored.list()[0]["evidence_class"] == "E4"
    assert "legacy-record" in restored.list()[0]["provenance"][0]


def test_simulated_runtime_memory_keeps_e5(tmp_path):
    observations=readout_to_observations({"theta":0.1,"amp":0.3,"phi":1.0})
    runtime=EntityRuntime(memory=MemoryManager(tmp_path/"m.jsonl"))
    result=runtime.process(observations,remember=True)
    assert result["memory"]["write_verified"]
    assert runtime.memory.list()[0]["evidence_class"] == "E5"


def test_gate_blocks_bad_readout_and_allows_explicit_e5_simulation():
    bridge=ResonatorBridge()
    assert bridge.gate({"theta":float("nan"),"amp":1,"phi":0})["proceed"] is False
    good=bridge.gate({"theta":0.1,"amp":0.3,"phi":1})
    assert good["proceed"] is True and good["evidence_classes"] == ["E5"]
