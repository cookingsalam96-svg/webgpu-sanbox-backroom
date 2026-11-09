import json
from pathlib import Path

from agent_runtime import AgentLoop, MemoryStore, ToolRegistry, final_answer_detect, parse_tool_call, safe_calc, tool_calc


def test_safe_calc_basic():
    assert safe_calc("25 * 4") == 100.0
    assert safe_calc("17**5 / 3") == 17**5 / 3


def test_memory_store_round_trip():
    store = MemoryStore()
    record = store.add("example note", metadata={"source": "test"})
    assert record["id"]
    assert store.recall("example")[0]["content"] == "example note"


def test_tool_registry_available_tools():
    registry = ToolRegistry(memory_store=MemoryStore())
    assert set(registry.tools) >= {"calc", "remember", "recall", "search_memories", "list_memories", "clear_memories"}


def test_tool_argument_validation():
    result = ToolRegistry().execute("calc", {"expression": "25 * 4"})
    assert result["ok"] is True and result["result"] == 100.0
    assert ToolRegistry().execute("calc", {"expression": "__import__('os').system('echo hi')"})["ok"] is False


def test_malformed_tool_call_detection():
    assert parse_tool_call("TOOL: {not valid json}") is None
    assert parse_tool_call('{"type": "tool_call", "name": "calc", "arguments": {"expression": "2 + 2"}}') is not None


def test_max_step_enforcement():
    registry = ToolRegistry(memory_store=MemoryStore())
    loop = AgentLoop(registry, max_steps=2, system_prompt="You are a concise agent.")

    def fake_model(messages):
        return 'TOOL: {"type": "tool_call", "name": "calc", "arguments": {"expression": "2 + 2"}}'

    result = loop.execute("Compute a value", fake_model, allow_python=False)
    assert result["status"] == "max_steps"
    assert result["step"] == 2


def test_final_answer_detection():
    assert final_answer_detect("FINAL: done") is True
    assert final_answer_detect("TOOL: {\"type\": \"tool_call\", \"name\": \"calc\", \"arguments\": {\"expression\": \"2 + 2\"}}") is False


def test_error_recovery_path():
    result = ToolRegistry().execute("remember", {"content": "", "metadata": {}})
    assert result["ok"] is False


def test_python_tool_disabled_message():
    result = ToolRegistry().execute("python", {"code": "print(1)", "timeout_seconds": 1.0})
    assert result["ok"] is False
