# HARDAM Entity V1.1 verification and integration

The fallback layers remain the provisional contract. This phase adds verification and interfaces, not another reasoning engine.

## Three separate systems

1. **Physical reference:** optomechanical resonator, optical coupling, torsion, calibration, and resonance detection. No physical sensor is provided by this repo.
2. **Cognitive system:** Dreamer proposal, independent deterministic Critic gate, attention ranking, append-only memory, action authorization, bounded output.
3. **Environmental system:** Back Room renderer, entity representation, environmental events, and visualization. This repository currently has no Three.js/WebGPU game runtime files; `sensor_simulator.py` is a clearly marked signal adapter, not an environment or physical simulator.

Integration remains through typed observation and output contracts, not shared responsibilities.

## Evidence classes

- **E1** experimentally verified: only assign with source/page-level evidence; generic hardware provenance alone is insufficient.
- **E2** mathematically derived: retain reproducible derivation provenance.
- **E3** engineering analogy: architecture mapping, not a scientific result.
- **E4** unverified hypothesis: default for unclassified real-world input.
- **E5** simulated: software-generated; must be `data_kind=simulation`.

These labels are not confidence probabilities. The simulator emits E5 and never claims it reproduces Kim et al.'s device.

## V1.1 flow

`typed sensor input -> attention ranking -> Dreamer proposal -> Critic provenance/contradiction checks -> append-only memory (explicit request) -> fail-closed allowlisted action -> bounded output`.

Dreamer and Critic are role-separated contracts. The current Dreamer is deterministic fallback logic and Critic is a deterministic validation function, not a second model. Model adapters can later implement the Dreamer interface; the Critic remains a distinct gate. Action proposals from the model cannot self-authorize.

Memory JSONL persistence is opt-in by passing a path to `MemoryManager(path=...)`. Writes require source IDs and provenance and are append-only. Runtime users must protect the file and host environment; append-only API is not cryptographic tamper protection.

## Validation

Run `python -m pip install -r requirements.txt && python -m pytest -q`. Tests cover evidence labels, provenance, conflicts, persistent memory reload, E5 simulation labeling, bounded output and fail-closed authorization. They do not test physical hardware, browser WebGPU, or a Three.js game runtime.
