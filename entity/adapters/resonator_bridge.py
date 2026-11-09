"""Colab/browser adapter for a simulated jax-js resonator readout."""
import math
from datetime import datetime, timezone
from entity.runtime import EntityRuntime
from entity.memory.memory_manager import MemoryManager
from entity.sensor.sensor_interface import normalize_observation

SOURCE = "jaxjs-torsion-resonator"
PROVENANCE = "jax-js damped torsional oscillator simulation (E5); not hardware, not a validated model of Kim et al."
FIELDS = (("torsion_angle", "theta", "normalized"), ("torsion_amplitude", "amp", "normalized"), ("torsion_phase_rad", "phi", "rad"))


def readout_to_observations(readout, *, source=SOURCE):
    if not isinstance(readout, dict): raise ValueError("readout must be an object")
    now = datetime.now(timezone.utc).isoformat()
    observations = []
    for kind, key, unit in FIELDS:
        value = readout.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 1e6:
            raise ValueError(f"readout.{key} must be a finite number")
        observations.append(normalize_observation({"source":source,"type":kind,"value":round(float(value),6),"timestamp":now,"confidence":0.25,"measurement_quality":"simulated","data_kind":"simulation","evidence_class":"E5","provenance":PROVENANCE,"unit":unit}))
    return observations


class ResonatorBridge:
    def __init__(self, memory_path=None, runtime=None):
        self.runtime = runtime or EntityRuntime(memory=MemoryManager(memory_path))

    def gate(self, readout, *, step=0, task="", remember=False):
        base = {"step":step,"evidence_classes":["E5"]}
        try:
            observations = readout_to_observations(readout)
            result = self.runtime.process(observations,task=f"step {step}: {task}"[:300],remember=remember,authorize_response=True)
        except Exception as exc:
            return {**base,"status":"BLOCKED","proceed":False,"assessment":f"gate error: {type(exc).__name__}: {exc}"[:500],"schema_valid":False,"critic_passed":False,"memory":{"write_requested":bool(remember),"write_verified":False,"record_id":None}}
        validation = result["validation"]
        no_hardware_claim = all(not item["verified"] and item["data_kind"] == "simulation" and item["evidence_class"] == "E5" for item in result["observation"])
        proceed = result["status"] == "FALLBACK" and validation["schema_valid"] and validation["critic_passed"] and no_hardware_claim
        return {**base,"status":result["status"],"proceed":bool(proceed),"assessment":result["assessment"],"confidence":result["confidence"],"schema_valid":validation["schema_valid"],"critic_passed":validation["critic_passed"],"memory":result["memory"]}
