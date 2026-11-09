# HARDAM Entity V1.1 · WebGPU Backroom

This repository separates three systems and joins them only through explicit contracts:

1. **Physical reference** — optomechanical concepts from the user-supplied Kim et al. paper summary. The paper concerns physics, not AI; source details and reported values remain unverified until source pages are checked.
2. **HARDAM cognitive entity** — sensor normalization, attention ranking, Dreamer proposal, Critic review, provenance-bearing memory, authorization gate, and bounded output.
3. **Back Room environment** — browser/game UI, entity visualization, environment observations, and interaction. A complete Three.js/WebGPU game is not currently included in this repository.

The Python demo simulates an illustrative torsional signal and passes it through the real repository entity contracts. It does not need a GPU, does not download a model, and does not claim to reproduce the physical paper.

## Architecture and build roadmap

See [the full service architecture and staged deployment plan](docs/SERVICE_ARCHITECTURE.md), including the proposed gateway/core/brain/voice/world/runner services, voice concurrency safeguards, container isolation requirements, browser WebGPU boundary, and optional n8n integration.

The service list is a proposal, not a claim that these services are deployed. Currently absent are the FastAPI gateway, SQLite memory service, voice stack, full Three.js Back Room, Docker job runner, monitoring service, and n8n adapter. No `agent.py` voice implementation was present in the repository when this architecture was documented.

## Downloadables

- [Full architecture and Colab guide](docs/HARDAM_ENTITY_V1_1_README.md)
- [Service architecture and build roadmap](docs/SERVICE_ARCHITECTURE.md)
- [Colab simulation script](colab_entity_demo.py)
- [Evidence class definitions](schemas/evidence_classes.yaml)
- [Architecture overview](docs/entity_v11.md)

## Test the entity in Google Colab (CPU runtime)

```python
!git clone --depth 1 https://github.com/cookingsalam96-svg/webgpu-sanbox-backroom.git /content/hardam
%cd /content/hardam
!python colab_entity_demo.py --steps 8 --remember
```

Inspect append-only JSONL session memory:

```python
from pathlib import Path
print(Path('/content/hardam_entity_memory.jsonl').read_text())
```

## Evidence labels

- **E1** experimental evidence with a page-located source citation. The format is checked; the citation's truth/support needs source verification.
- **E2** mathematical derivation with reproducible provenance.
- **E3** engineering analogy, e.g. mapping resonator phase to 72 names.
- **E4** unverified hypothesis, including persona/mythology treated as factual claims.
- **E5** software-generated simulation, never a hardware measurement.

## Tests and limitations

Run `python -m pip install -r requirements.txt && python -m pytest -q` from the repo root. Test results are not claimed here. The Python simulation does not validate browser WebGPU, LFM2 model compatibility, physical hardware, or a full Back Room renderer. The separate browser notebook requires real-device testing.

Tool/action boundaries are allowlisted and fail closed. Arbitrary Python model-generated code is not executed. Memory is append-only JSONL, not cryptographically tamper-proof. No secrets are passed to browser code.
