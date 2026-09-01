from prompt_engine.builder import PromptBuilder, StablePrefix


def test_stable_prefix_hash_determinism():
    tools = [
        {"name": "tool_b", "desc": "B"},
        {"name": "tool_a", "desc": "A"}
    ]
    tools_reordered = [
        {"name": "tool_a", "desc": "A"},
        {"name": "tool_b", "desc": "B"}
    ]
    
    prefix1 = StablePrefix("sys", "pol", "org", tools)
    prefix2 = StablePrefix("sys", "pol", "org", tools_reordered)
    
    # Identical inputs (even with reordered tools) create identical prefix hashes
    assert prefix1.hash_prefix() == prefix2.hash_prefix()
    
    prefix3 = StablePrefix("sys_changed", "pol", "org", tools)
    assert prefix1.hash_prefix() != prefix3.hash_prefix()

def test_prompt_builder_structure():
    prefix = StablePrefix("sys", "pol", "org", [{"name": "tool_a"}])
    builder = PromptBuilder(prefix)
    
    messages = builder.build("hello", memory=[{"role": "user", "content": "prev"}])
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert "tool_a" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "prev"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "hello"
