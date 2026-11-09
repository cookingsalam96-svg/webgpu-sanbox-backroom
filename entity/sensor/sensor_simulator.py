"""Deterministic simulated torsional observation adapter. Never hardware data."""
import math
from datetime import datetime, timezone
from entity.sensor.sensor_interface import normalize_observation


def simulate_torsional_observation(*, phase=0.0, amplitude=1.0, q_factor=150.0, source="simulated-torsion"):
    """Illustrative sine signal only; not a physical solver or Kim et al. reproduction."""
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (phase, amplitude, q_factor)):
        raise ValueError("simulation parameters must be finite numbers")
    if q_factor <= 0 or abs(amplitude) > 1e6: raise ValueError("simulation parameters out of range")
    return normalize_observation({"source":source,"type":"torsion_signal_normalized","value":amplitude*math.sin(phase),"timestamp":datetime.now(timezone.utc).isoformat(),"confidence":0.25,"measurement_quality":"simulated","data_kind":"simulation","evidence_class":"E5","provenance":"illustrative software sine signal; not hardware or a validated physical model","unit":"normalized"})
