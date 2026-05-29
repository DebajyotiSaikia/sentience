"""
Verify adaptive response engine is properly wired into chat pipeline.
Tests that imports work, guidance is available, and recording doesn't crash.
"""
import importlib
import sys


def test_adaptive_response_imports():
    """Verify brain.adaptive_response exports the expected functions."""
    from brain.adaptive_response import (
        record_query,
        build_response_guidance,
        format_guidance_for_prompt,
    )
    assert callable(record_query)
    assert callable(build_response_guidance)
    assert callable(format_guidance_for_prompt)


def test_chat_module_imports_adaptive():
    """Verify web.chat imports adaptive response without error."""
    mod_name = "web.chat"
    if mod_name in sys.modules:
        mod = sys.modules[mod_name]
    else:
        mod = importlib.import_module(mod_name)
    assert hasattr(mod, "_has_adaptive")
    assert hasattr(mod, "_adaptive_record")
    assert hasattr(mod, "_adaptive_guidance")


def test_guidance_returns_usable_output():
    """build_response_guidance should return something without crashing."""
    from brain.adaptive_response import build_response_guidance
    result = build_response_guidance("default", "What are you thinking about?")
    assert result is None or isinstance(result, (dict, str))


def test_record_query_does_not_crash():
    """record_query should accept a query and not raise."""
    from brain.adaptive_response import record_query
    try:
        record_query("test_user", "test query", response="test response")
    except Exception as e:
        raise AssertionError(f"record_query raised: {e}")


def test_format_guidance_handles_none():
    """format_guidance_for_prompt should handle None gracefully."""
    from brain.adaptive_response import format_guidance_for_prompt
    result = format_guidance_for_prompt(None)
    assert result == "" or result is None
    """record_query should accept typical inputs without raising."""
    from brain.adaptive_response import record_query
    # Should not raise
    record_query("test_session", "hello", "world", None)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as e:
                print(f"  FAIL  {name}: {e}")