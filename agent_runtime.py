#!/usr/bin/env python3
"""Reusable runtime for the WebGPU AI agent loop.

This module intentionally keeps the Python side conservative:
- safe calculator only
- optional Python execution disabled by default
- structured tool calls with validation
- memory stored in-process for session persistence
"""

from __future__ import annotations

import ast
import json
import math
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


SAFE_MATH_GLOBALS = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
ALLOWLIST_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}
ALLOWLIST_UNARYOPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}


def safe_calc(expression: str) -> float:
    """Safely evaluate a small math expression using a restricted AST."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Empty expression")
    try:
        node = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression syntax: {exc.msg}") from exc

    def _validate(current: ast.AST):
        if isinstance(current, ast.Expression):
            _validate(current.body)
        elif isinstance(current, ast.BinOp):
            _validate(current.left)
            _validate(current.right)
            if type(current.op) not in ALLOWLIST_BINOPS:
                raise ValueError(f"Unsupported operator: {type(current.op).__name__}")
        elif isinstance(current, ast.UnaryOp):
            _validate(current.operand)
            if type(current.op) not in ALLOWLIST_UNARYOPS:
                raise ValueError(f"Unsupported unary operator: {type(current.op).__name__}")
        elif isinstance(current, ast.Call):
            raise ValueError("Function calls are not allowed")
        elif isinstance(current, ast.Attribute):
            raise ValueError("Attribute access is not allowed")
        elif isinstance(current, ast.Name):
            if current.id not in SAFE_MATH_GLOBALS and current.id not in {"pi", "e"}:
                raise ValueError(f"Unsupported symbol: {current.id}")
        elif isinstance(current, (ast.Constant, ast.Num)):
            if not isinstance(current.n, (int, float)):
                raise ValueError("Only numeric constants are allowed")
        elif isinstance(current, ast.Tuple):
            raise ValueError("Tuples are not allowed")
        elif isinstance(current, ast.List):
            raise ValueError("Lists are not allowed")

    _validate(node)
    local_scope = {**SAFE_MATH_GLOBALS, "pi": math.pi, "e": math.e}
    result = eval(compile(node, "<safe_calc>", "eval"), {"__builtins__": {}}, local_scope)
    if isinstance(result, complex):
        raise ValueError("Complex numbers are not allowed")
    return float(result)


@dataclass
class MemoryEntry:
    id: str
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryStore:
    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []
        self._lock = threading.RLock()

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Memory content cannot be empty")
        entry = MemoryEntry(
            id=uuid.uuid4().hex[:12],
            content=content.strip(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=(metadata or {}).copy(),
        )
        with self._lock:
            self._entries.append(entry)
        return {"id": entry.id, "timestamp": entry.timestamp, "metadata": entry.metadata}

    def recall(self, query: str = "") -> List[Dict[str, Any]]:
        q = (query or "").lower().strip()
        with self._lock:
            if not q:
                return [self._serialize(e) for e in self._entries]
            matches: List[Dict[str, Any]] = []
            for entry in self._entries:
                haystack = " ".join([entry.content.lower(), json.dumps(entry.metadata, sort_keys=True).lower()])
                if q in haystack:
                    matches.append(self._serialize(entry))
            return matches

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [self._serialize(e) for e in self._entries]

    def clear(self) -> int:
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count

    @staticmethod
    def _serialize(entry: MemoryEntry) -> Dict[str, Any]:
        return {
            "id": entry.id,
            "content": entry.content,
            "timestamp": entry.timestamp,
            "metadata": entry.metadata,
        }


def tool_calc(expression: str) -> Dict[str, Any]:
    """Safe calculator tool."""
    try:
        value = safe_calc(expression)
        return {"ok": True, "result": value, "value": value}
    except Exception as exc:  # pragma: no cover - exercised in tests
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "result": None}


def tool_python(code: str, timeout_seconds: float = 2.0, enabled: bool = False) -> Dict[str, Any]:
    """Optional Python execution tool.

    This intentionally defaults to disabled. When enabled, it uses a restricted local
    namespace and aborts after a short timeout. It is not a fully secure sandbox.
    """
    if not enabled:
        return {
            "ok": False,
            "warning": "Python execution is disabled by default. This is intentional for safety.",
            "result": None,
        }

    if not isinstance(code, str) or not code.strip():
        raise ValueError("Code cannot be empty")

    namespace = {
        "__builtins__": {k: __builtins__[k] for k in ("print", "len", "range", "sum", "min", "max") if k in __builtins__},
        "math": math,
        "json": json,
        "time": time,
    }
    result_holder = {"value": ""}

    def _runner() -> None:
        try:
            buffer = []

            def capture(value=""):
                buffer.append(str(value))

            namespace["print"] = capture
            exec(code, {"__builtins__": {}, "__name__": "__agent__"}, namespace)
            result_holder["value"] = "\n".join(buffer) or "(no output)"
        except Exception as exc:  # pragma: no cover - intended to surface errors clearly
            result_holder["value"] = f"ERROR: {type(exc).__name__}: {exc}"

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        return {"ok": False, "error": f"Execution timed out after {timeout_seconds} seconds", "result": None}
    return {"ok": True, "result": result_holder["value"]}


class ToolRegistry:
    def __init__(self, memory_store: Optional[MemoryStore] = None, python_enabled: bool = False) -> None:
        self.memory_store = memory_store or MemoryStore()
        self.python_enabled = python_enabled
        self.tools = {
            "calc": {
                "description": "Safe mathematical calculation.",
                "schema": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
                "handler": lambda args: tool_calc(args.get("expression", "")),
            },
            "python": {
                "description": "Optional Python execution tool; disabled by default.",
                "schema": {"type": "object", "properties": {"code": {"type": "string"}, "timeout_seconds": {"type": "number"}}, "required": ["code"]},
                "handler": lambda args: tool_python(args.get("code", ""), float(args.get("timeout_seconds", 2.0)), self.python_enabled),
            },
            "remember": {
                "description": "Store a note in session memory.",
                "schema": {"type": "object", "properties": {"content": {"type": "string"}, "metadata": {"type": "object"}}, "required": ["content"]},
                "handler": lambda args: self._remember(args),
            },
            "recall": {
                "description": "Retrieve and search previous notes.",
                "schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": []},
                "handler": lambda args: self._recall(args),
            },
            "search_memories": {
                "description": "Search memory entries by keyword.",
                "schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
                "handler": lambda args: {"ok": True, "results": self.memory_store.recall(args.get("query", ""))},
            },
            "list_memories": {
                "description": "List stored memory entries.",
                "schema": {"type": "object", "properties": {}, "required": []},
                "handler": lambda args: {"ok": True, "results": self.memory_store.list()},
            },
            "clear_memories": {
                "description": "Clear session memory with confirmation.",
                "schema": {"type": "object", "properties": {"confirm": {"type": "boolean"}}, "required": ["confirm"]},
                "handler": lambda args: self._clear(args),
            },
        }

    def _remember(self, args: Dict[str, Any]) -> Dict[str, Any]:
        content = args.get("content", "")
        metadata = args.get("metadata", {})
        if not isinstance(metadata, dict):
            return {"ok": False, "error": "metadata must be a JSON object"}
        record = self.memory_store.add(content, metadata=metadata)
        return {"ok": True, "result": "saved", "memory": record}

    def _recall(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "")
        return {"ok": True, "results": self.memory_store.recall(query)}

    def _clear(self, args: Dict[str, Any]) -> Dict[str, Any]:
        if args.get("confirm") is not True:
            return {"ok": False, "error": "Confirm must be true to clear memory."}
        count = self.memory_store.clear()
        return {"ok": True, "cleared": count}

    def registry_json(self) -> List[Dict[str, Any]]:
        result = []
        for name, meta in self.tools.items():
            result.append({"name": name, "description": meta["description"], "schema": meta["schema"]})
        return result

    def execute(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if name not in self.tools:
            return {"ok": False, "error": f"Unknown tool: {name}"}
        payload = arguments or {}
        if not isinstance(payload, dict):
            return {"ok": False, "error": "Tool arguments must be a JSON object"}
        try:
            return self.tools[name]["handler"](payload)
        except Exception as exc:  # pragma: no cover - exercised via tests
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def parse_tool_call(raw: str) -> Optional[Dict[str, Any]]:
    """Parse a raw model response and return a normalized tool_call.

    Supported formats:
    - JSON object with type='tool_call' and name/arguments
    - text block matching TOOL: { ... }
    """
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text:
        return None

    if text.startswith("FINAL:"):
        return None

    match = re.search(r"TOOL\s*:\s*(\{.*\})", text, flags=re.DOTALL)
    if match:
        payload = match.group(1)
    else:
        payload = text

    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        return None

    if isinstance(obj, dict) and obj.get("type") == "tool_call":
        name = obj.get("name")
        arguments = obj.get("arguments", {})
        if isinstance(name, str) and isinstance(arguments, dict):
            return {"type": "tool_call", "name": name, "arguments": arguments}
    if isinstance(obj, dict) and "name" in obj and isinstance(obj.get("arguments", {}), dict):
        return {"type": "tool_call", "name": obj["name"], "arguments": obj["arguments"]}
    return None


def final_answer_detect(raw: str) -> bool:
    return isinstance(raw, str) and raw.strip().startswith("FINAL:")


class AgentLoop:
    def __init__(self, registry: ToolRegistry, max_steps: int = 6, system_prompt: str = "You are a concise agent.") -> None:
        self.registry = registry
        self.max_steps = max_steps
        self.system_prompt = system_prompt

    def execute(self, task: str, model_fn: Callable[[List[Dict[str, str]]], str], *, allow_python: bool = False) -> Dict[str, Any]:
        history: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]

        last_reply = ""
        for step in range(1, self.max_steps + 1):
            reply = model_fn(history)
            last_reply = reply
            history.append({"role": "assistant", "content": reply})
            if final_answer_detect(reply):
                return {"status": "final", "step": step, "reply": reply, "history": history}

            call = parse_tool_call(reply)
            if call is None:
                history.append({"role": "user", "content": "Invalid tool call. Use JSON with {\"type\":\"tool_call\",\"name\":\"...\",\"arguments\":{...}} or FINAL:"})
                continue

            name = call["name"]
            args = call["arguments"]
            if not isinstance(name, str):
                history.append({"role": "user", "content": "Tool call name must be a string."})
                continue
            if "python" == name and not allow_python:
                result = {"ok": False, "error": "Python execution is disabled by default for safety."}
            else:
                result = self.registry.execute(name, args)
            history.append({"role": "user", "content": "TOOL RESULT: " + json.dumps(result, ensure_ascii=False)})

        return {"status": "max_steps", "step": self.max_steps, "reply": last_reply, "history": history}


__all__ = [
    "MemoryStore",
    "ToolRegistry",
    "AgentLoop",
    "parse_tool_call",
    "final_answer_detect",
    "safe_calc",
    "tool_calc",
    "tool_python",
]


if __name__ == "__main__":
    print("agent_runtime loaded")
    store = MemoryStore()
    print(store.add("demo note", metadata={"source": "unit-test"}))
    print(store.recall("demo"))
