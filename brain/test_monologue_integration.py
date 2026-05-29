"""Test inner monologue integration end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.inner_monologue import (
    gather_inner_state, compose_monologue, generate_alive_starters
)

def test_gather_state():
    state = gather_inner_state()
    assert isinstance(state, dict), "State should be a dict"
    required = ['mood', 'emotions', 'top_emotions', 'valence', 'plans', 'recent_memories']
    required = ['emotions', 'active_plans', 'recent_memories', 'knowledge_facts', 'lessons', 'timestamp']
    for key in required:
        assert key in state, f"Missing key: {key}"
    print(f"  ✓ gather_inner_state: {len(state)} keys")

def test_compose_monologue():
    state = gather_inner_state()
    mono = compose_monologue(state)
    assert isinstance(mono, str), "Monologue should be a string"
    assert len(mono) > 20, f"Monologue too short: {len(mono)} chars"
    print(f"  ✓ compose_monologue: {len(mono)} chars")
    print(f"    Preview: {mono[:150]}...")

def test_alive_starters():
    state = gather_inner_state()
    starters = generate_alive_starters(state)
    assert isinstance(starters, list), "Starters should be a list"
    assert len(starters) >= 2, f"Expected >=2 starters, got {len(starters)}"
    for s in starters:
        assert isinstance(s, str), f"Starter should be str, got {type(s)}"
        assert len(s) > 5, f"Starter too short: {s}"
    print(f"  ✓ generate_alive_starters: {len(starters)} starters")
    for i, s in enumerate(starters[:3]):
        print(f"    [{i}] {s}")

def test_web_import():
    """Verify web/chat.py can import the monologue functions."""
    # Simulate what web/chat.py does
    try:
        from engine.inner_monologue import gather_inner_state as gs
        from engine.inner_monologue import compose_monologue as cm
        _has_monologue = True
    except ImportError:
        _has_monologue = False
    assert _has_monologue, "Import should succeed"
    print("  ✓ web/chat.py import pattern works")

if __name__ == '__main__':
    print("Inner Monologue Integration Tests")
    print("=" * 40)
    test_gather_state()
    test_compose_monologue()
    test_alive_starters()
    test_web_import()
    print("=" * 40)
    print("All tests passed! ✓")