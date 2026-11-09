# HARDAM service architecture and deployment roadmap

This document records the recommended service decomposition and staged implementation plan. It is an architecture proposal, not a claim that every service already exists. The current repository contains the Python entity contracts, an E5 simulation adapter, a Colab entity demo, and a browser WebGPU candidate notebook. There is no supplied `agent.py`, no FastAPI service, no Docker Compose deployment, no voice service, and no complete Three.js world runtime yet.

## System boundaries

Keep three domains separate and connect them through versioned, validated interfaces:

1. **Physical reference:** optomechanics concepts and any future hardware adapters. Paper-derived values require traceable source evidence; software simulation must never be reported as a hardware measurement.
2. **Cognitive Entity:** gateway/session boundary, async coordinator, model adapter, Dreamer proposal, Critic policy, memory, permissioned tools, and audit/health.
3. **Back Room world:** browser-owned rendering, WebGPU/WebGL capability, avatar/world state, environment observations, and user interaction.

The browser owns the visual scene and its WebGPU context. A Docker container does not automatically receive browser GPU access. Backend services receive only structured observations and return bounded entity/world events.

## Proposed services

| Service | Responsibility | Candidate technology | Current status |
| --- | --- | --- | --- |
| `entity-gateway` | API auth, sessions, input validation, rate limits | FastAPI | Proposed |
| `entity-core` | Async turn orchestration, cancellation, state transitions | Python asyncio | Existing contracts are not yet exposed as service |
| `entity-brain` | Local text inference adapter | llama.cpp or browser Transformers.js adapter | Not integrated; select one deployment mode per target |
| `entity-dreamer` | Planning/reflection proposal interface | Python module/service | Deterministic fallback exists; not a separate model |
| `entity-critic` | Evidence, output, policy, and action validation | Python module/service | Deterministic checks exist; not a separate trained model |
| `entity-memory` | Durable records and retrieval | SQLite initially | Current JSONL memory manager is append-oriented, not SQLite |
| `entity-voice` | Audio capture, VAD, STT, turn handling, TTS, playback | faster-whisper + licensed local TTS | Not present; proposed module boundaries below |
| `entity-world` | Browser avatar and world state | Three.js, WebGPU with explicit WebGL fallback | Not present as a full runtime |
| `entity-tools` | Approved, narrowly scoped tool APIs | Explicit allowlist and per-tool validation | Python registry/contracts exist; arbitrary code disabled |
| `entity-runner` | Isolated build/test jobs and artifact review | Docker job containers | Not implemented; see isolation controls |
| `entity-monitor` | Health, logs, metrics, resource status | Prometheus-compatible metrics | Not implemented |

Start as a modular monolith or small Compose deployment. On an 8 GB CPU-only machine, do not start all model services concurrently; first measure resident memory, cold-start time, throughput, and latency one component at a time.

## Voice subsystem boundary

No `agent.py` was supplied in the repository at the time this document was authored. If a voice prototype is added later, it belongs under a voice subsystem; it is not the whole Entity:

```text
entity_voice/
  ears/
    microphone.py
    vad.py
    stt.py
  brain/
    conversation.py
  mouth/
    tts.py
    audio_player.py
  controller/
    turn_manager.py
    barge_in.py
  voice_service.py
```

Concurrency requirements:

- One microphone capture owner reads audio frames and distributes each immutable frame to subscribers; multiple readers must not compete for a queue.
- Evaluate VAD exactly once for each frame and distribute the timestamped result alongside that frame.
- Sentence segmentation uses a persistent buffer and emits complete clauses without discarding remaining text.
- Playback state follows the audio device/player lifecycle and clears only when playback has actually completed or stopped.
- Use managed temporary directories/files and guaranteed cleanup; never use insecure `tempfile.mktemp`.
- Offline startup requires pre-cached models, checksums/versions, and an explicit offline-mode test. Never silently download models at runtime when offline mode is requested.
- Latency numbers such as 150 ms TTS, 200 ms STT, or under 300 ms combined are targets only until measured on named hardware with a reproducible benchmark.
- Voice must identify as an AI assistant on calls. Use licensed synthetic voices; do not clone a person's voice without authorization. Outbound calls must be opt-in and contact-authorized; no deceptive or unsolicited cold calling.

## Container and job isolation

The job runner is a security boundary, not a general shell tool for the model. The model may submit a structured job proposal; a separate policy/approval gate decides whether it runs. Never expose the host Docker socket or mount personal files into job containers.

Recommended defaults for any future runner:

- Non-root user, no privileged mode, no host PID/network namespaces.
- No Docker socket, host home directory, SSH keys, tokens, or arbitrary host mounts.
- Read-only root filesystem where practical; one fresh temporary workspace per job.
- CPU, memory, process-count, disk, and wall-clock limits.
- Network disabled by default; narrowly allowlist an explicit network need only after authorization.
- Separate private service network from isolated job network.
- Explicit human approval for artifact export, external APIs, or any persistent side effect.
- Record job request, policy decision, image digest, limits, exit status, and artifact hashes.
- Destroy the job container and temporary workspace after completion or timeout.

Docker controls reduce risk but do not make arbitrary code execution fully secure. Use a stronger isolation boundary if untrusted code must run.

## Browser world and inference

```text
Browser
  ├─ Three.js scene and entity avatar
  ├─ WebGPU capability/adapter check
  ├─ optional WebGL renderer fallback (rendering only)
  ├─ local browser model adapter, if selected
  ├─ audio UI and world simulation
  └─ authenticated WebSocket/HTTP boundary
       └─ Entity Gateway → Entity Core → Dreamer/Critic/Memory/Tools
```

WebGL fallback is a renderer choice; it must not be confused with inference fallback. If browser model inference is configured for WebGPU-only, report lack of WebGPU clearly and do not silently select CPU inference. Browser GPU resources remain owned by the browser.

## Optional n8n integration

Treat the supplied n8n endpoint as an untrusted optional integration until its ownership, TLS, authentication, authorization scopes, retention, and data handling are verified. It is not the trusted Entity core. Send only the minimum approved payload; do not send private memory, recordings, or credentials by default. Use a dedicated revocable credential stored server-side, explicit allowlisted workflows, timeouts, audit logs, and a human approval boundary for side effects. Core local operation should continue when the workflow service is unavailable.

## Staged build sequence and acceptance checks

1. **Foundation:** gateway auth/session contracts, health endpoints, structured logs, private service network. Acceptance: unauthenticated requests rejected, health checks work, no secrets emitted.
2. **Entity Core:** async orchestration, Dreamer/Critic interfaces, typed task and action contracts. Acceptance: bounded steps, cancellation, malformed output rejected, Critic cannot be bypassed.
3. **Memory:** SQLite-backed versioned append-only event table, migration and recovery tests. Acceptance: provenance/evidence preserved across restart; failed writes are visible; no silent overwrite.
4. **Voice:** single audio capture producer, per-frame VAD fanout, STT, turn manager, TTS and barge-in. Acceptance: queue concurrency test, playback lifecycle test, offline startup, consent controls, measured latency report.
5. **Virtual World:** browser scene, avatar, and typed world-state synchronization. Acceptance: WebGPU detection, rendering-only fallback behavior, bounded observation events, no false sensor/hardware claims.
6. **Development Sandbox:** isolated, approval-gated build/test jobs. Acceptance: no host socket/mount, offline default, resource/time limits, cleanup on success/failure, export approval.
7. **n8n integration:** optional, authenticated and minimized workflow adapter. Acceptance: local operation without service; authorization, timeout, failure, and data-minimization tests.
8. **Validation:** restart recovery, offline operation, resource ceilings, security review, end-to-end simulation, and named-device latency benchmark.

## Current implementation versus proposal

Implemented in this repository: evidence classes E1–E5, typed observation/output validation, deterministic attention and Dreamer/Critic contracts, append-only JSONL memory, action authorization checks, resonator bridge, CPU simulation demo, and a WebGPU candidate notebook.

Not yet implemented: FastAPI gateway, asyncio service deployment, llama.cpp inference service, SQLite memory, voice stack, Three.js Back Room runtime, Docker runner, metrics service, n8n integration, and production auth. Do not treat the service table as a completed deployment.
