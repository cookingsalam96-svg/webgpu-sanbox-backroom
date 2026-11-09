# webgpu-sanbox-backroom

This repository contains a browser-side WebGPU AI agent prototype for Google Colab. It is intentionally conservative: the browser performs model inference locally, while the Python runtime remains the orchestration and tool layer.

## Quick start

1. Open the notebook in Google Colab.
2. Run the cells in order.
3. Click `Load Model` in the browser UI.
4. Enter a task and press `Run Loop`.
5. If the browser has no WebGPU support, the UI will display a clear error and stop.

## Files

- `webgpu_ai_loop.ipynb` — main Google Colab notebook.
- `agent_runtime.py` — shared Python runtime for tool validation and memory.
- `tests/test_agent.py` — agent loop tests.
- `tests/test_tools.py` — tool and validation tests.
- `docs/ARCHITECTURE.md` — architecture overview.

## Model compatibility and defaults

Default model:
- `LiquidAI/LFM2-8B-A1B-ONNX`

Small fallback:
- `LiquidAI/LFM2-1.2B-ONNX`

These model IDs are intentionally treated as candidates that must be validated at runtime. The browser implementation checks for WebGPU support and attempts to load the selected model through Transformers.js. There is no hidden fallback to unsupported execution providers. If the selected Hub configuration cannot be loaded, the UI surfaces the diagnostic message and stops.

## Known limitations

- Real WebGPU inference depends on a supported browser and GPU driver.
- Transformers.js compatibility changes over time; use the pinned `TJS_VERSION` in the notebook.
- The browser is not a secure sandbox; Python execution is kept disabled by default.
- Large models may require substantial browser memory and download time.

## Troubleshooting

- No WebGPU: use desktop Chrome or Edge, not Safari or unsupported browsers.
- Model download fails: verify the Hub model ID and a compatible Transformers.js wheel.
- Browser memory exhausted: unload the model, restart, or switch to the lighter fallback.
- Tool errors: check the JSON tool-call format and the limit of safe operations.

## Security model

- Python tool execution is disabled by default.
- Model-generated tool calls are treated as untrusted input.
- The notebook never exposes secrets or API keys to browser JavaScript.
- Unrestricted filesystem access is not granted through the agent tools.
