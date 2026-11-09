#!/usr/bin/env python3
"""CPU-only Google Colab demo: stimulate the HARDAM entity with E5 synthetic data.

This produces an illustrative damped torsion-like signal and routes each update
through the repository's actual sensor -> attention -> Dreamer -> Critic ->
memory/action/output contracts. It does not require WebGPU or an LLM and is not
a physical solver or a reproduction of Kim et al.

Colab quick start:
    !git clone --depth 1 https://github.com/cookingsalam96-svg/webgpu-sanbox-backroom.git /content/hardam
    %cd /content/hardam
    !python colab_entity_demo.py --steps 8 --remember
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import subprocess
from pathlib import Path

REPO_URL = "https://github.com/cookingsalam96-svg/webgpu-sanbox-backroom.git"


def find_repo(repo_dir: str | None) -> Path:
    if repo_dir:
        root = Path(repo_dir).expanduser().resolve()
    else:
        here = Path(__file__).resolve().parent
        if (here / "entity" / "runtime.py").is_file():
            root = here
        elif Path("/content/hardam/entity/runtime.py").is_file():
            root = Path("/content/hardam")
        else:
            root = Path("/content/hardam")
            if not (root / "entity" / "runtime.py").is_file():
                root.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(root)], check=True)
    if not (root / "entity" / "runtime.py").is_file():
        raise FileNotFoundError(f"No HARDAM package found at {root}; clone the repository or pass --repo-dir")
    return root


def make_readout(step: int, q: float, dt: float) -> dict:
    """Simple deterministic damped oscillator visualization input, not a physical model."""
    omega = 2.0 * math.pi
    t = step * dt
    decay = math.exp(-omega * t / q)
    theta = 0.25 * decay * math.cos(omega * t)
    velocity = -0.25 * omega * decay * math.sin(omega * t)
    amplitude = math.hypot(theta, velocity / omega)
    phi = math.atan2(-velocity / omega, theta) % (2.0 * math.pi)
    return {"theta": theta, "amp": amplitude, "phi": phi, "sigma": 0.0}


def run(args) -> int:
    root = find_repo(args.repo_dir)
    sys.path.insert(0, str(root))
    from entity.adapters.resonator_bridge import ResonatorBridge

    bridge = ResonatorBridge(memory_path=args.memory_path if args.remember else None)
    print("HARDAM Entity V1.1 · CPU simulation · E5 (simulated; not hardware)")
    print(f"repo={root} steps={args.steps} illustrative_Q={args.q} dt={args.dt} remember={args.remember}\n")

    for step in range(1, args.steps + 1):
        readout = make_readout(step, args.q, args.dt)
        verdict = bridge.gate(
            readout,
            step=step,
            task="observe the simulated torsion state",
            remember=args.remember,
        )
        row = {
            "step": step,
            "theta": round(readout["theta"], 6),
            "amplitude": round(readout["amp"], 6),
            "phase_rad": round(readout["phi"], 6),
            "status": verdict["status"],
            "proceed": verdict["proceed"],
            "evidence": verdict["evidence_classes"],
            "critic_passed": verdict["critic_passed"],
            "schema_valid": verdict["schema_valid"],
            "memory": verdict["memory"],
        }
        print(json.dumps(row, ensure_ascii=False))
        if not verdict["proceed"]:
            print("Gate blocked continuation:", verdict["assessment"])
            return 2

    if args.remember:
        print(f"\nAppend-only memory file: {Path(args.memory_path).resolve()}")
    print("\nSimulation finished. No hardware was accessed and no LLM/WebGPU inference was run.")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=8, help="synthetic updates (1..1000)")
    parser.add_argument("--q", type=float, default=150.0, help="illustrative damping/Q control; not measured")
    parser.add_argument("--dt", type=float, default=0.05, help="synthetic time step in arbitrary seconds")
    parser.add_argument("--remember", action="store_true", help="append E5 records to JSONL memory")
    parser.add_argument("--memory-path", default="/content/hardam_entity_memory.jsonl")
    parser.add_argument("--repo-dir", default=None, help="existing checkout; otherwise auto-detect or clone to /content/hardam")
    args = parser.parse_args()
    if not 1 <= args.steps <= 1000:
        parser.error("--steps must be between 1 and 1000")
    if not math.isfinite(args.q) or args.q <= 0 or args.q > 1e6:
        parser.error("--q must be finite and in (0, 1e6]")
    if not math.isfinite(args.dt) or args.dt <= 0 or args.dt > 10:
        parser.error("--dt must be finite and in (0, 10]")
    return args


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
