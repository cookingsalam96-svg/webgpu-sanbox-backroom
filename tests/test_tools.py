import json

from agent_runtime import AgentLoop, MemoryStore, ToolRegistry, parse_tool_call


def test_memory_storage_and_search():
    store = MemoryStore()
    record = store.add("Remember to verify WebGPU support", metadata={"type": "diagnostic"})
    assert record["id"]
    found = store.recall("WebGPU")
    assert any(item["content"] == "Remember to verify WebGPU support" for item in found)


def test_registry_and_tool_execution():
    registry = ToolRegistry(memory_store=MemoryStore())
    response = registry.execute("calc", {"expression": "7 * 6"})
    assert response["ok"] is True and response["result"] == 42.0


def test_invalid_tool_call_and_recovery():
    assert parse_tool_call("TOOL: {bad json}") is None
    assert parse_tool_call('{"type": "tool_call", "name": "calc", "arguments": {"expression": "1 + 1"}}') is not None


def test_step_limit_and_final_response_behaviour():
    registry = ToolRegistry(memory_store=MemoryStore())
    loop = AgentLoop(registry, max_steps=3, system_prompt="Test agent.")

    def fake_model(messages):
        return "FINAL: 42"

    result = loop.execute("Answer the question", fake_model, allow_python=False)
    assert result["status"] == "final"
    assert "42" in result["reply"]
