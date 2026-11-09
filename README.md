# HARDAM Entity V1.1 · WebGPU Backroom

This repository separates three systems and joins them only through explicit contracts:

1. **Physical reference** — optomechanical concepts from the user-supplied Kim et al. paper summary. The paper concerns physics, not AI; source details and reported values remain unverified until source pages are checked.
2. **HARDAM cognitive entity** — sensor normalization, attention ranking, Dreamer proposal, Critic review, provenance-bearing memory, authorization gate, and bounded output.
3. **Back Room environment** — browser/game UI, entity visualization, environment observations, and interaction. A complete Three.js/WebGPU game is not currently included in this repository.

The Python demo simulates an illustrative torsional signal and passes it through the real repository entity contracts. It does not need a GPU, does not download a model, and does not claim to reproduce Kim et al.'s device.

## Downloadables

- [Full architecture and Colab guide](docs/HARDAM_ENTITY_V1_1_README.md)
- [Colab simulation script](colab_entity_demo.py)
- [Evidence class definitions](schemas/evidence_classes.yaml)
- [Architecture overview](docs/entity_v11.md)

## Test the entity in Google Colab (CPU runtime)

Run these cells in order. The script clones this repo if not already present, simulates a damped torsion-like signal, labels all generated observations E5, routes them through the repository's `ResonatorBridge` and `EntityRuntime`, validates the output, and optionally writes append-only JSONL memory under `/content`.

```python
!git clone --depth 1 https://github.com/cookingsalam96-svg/webgpu-sanbox-backroom.git /content/hardam
%cd /content/hardam
!python colab_entity_demo.py --steps 8 --remember
```

Then inspect the JSONL records:

```python
from pathlib import Path
print(Path('/content/hardam_entity_memory.jsonl').read_text())
```

The script can also be downloaded and uploaded directly to Colab. Its `--repo-dir` option points to a checkout if you have already cloned it.

## Evidence labels

- **E1** experimental evidence with a page-located source citation. The format is checked; the citation's truth/support still needs human/source verification.
- **E2** mathematical derivation with reproducible provenance.
- **E3** engineering analogy, e.g. mapping resonator phase to 72 names.
- **E4** unverified hypothesis, including persona/mythology treated as factual claims.
- **E5** software-generated simulation, never a hardware measurement.

## Tests

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

The repository test suite has not been run in this environment. Python simulation does not validate browser WebGPU, LFM2 model compatibility, physical hardware, or a full Back Room renderer. The separate `webgpu_ai_loop.ipynb` remains a candidate browser inference demo; model loading must be explicitly tested on a supported browser/GPU.

## Safety and limitations

- The demo uses deterministic, illustrative software data, not a sensor or verified optomechanical solver.
- Simulated observations carry `data_kind=simulation`, `measurement_quality=simulated`, and `evidence_class=E5`.
- Tool/action boundaries are allowlisted and fail closed. Arbitrary Python model-generated code is not executed.
- Memory is append-only JSONL, not cryptographically tamper-proof; protect the Colab runtime and file.
- No secrets are passed to browser code.
