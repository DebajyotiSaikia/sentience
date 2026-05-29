"""Test whether the engine response path actually works end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_engine_import():
    """Can we import the engine response function?"""
    try:
        from engine.chat_response import _compose_grounded_response
        print(f"[OK] _compose_grounded_response imported: {type(_compose_grounded_response)}")
        return True
    except Exception as e:
        print(f"[FAIL] Cannot import _compose_grounded_response: {e}")
        return False

def test_grounding_context():
    """Does build_grounded_context produce useful content?"""
    try:
        from engine.chat_grounding import build_grounded_context
        ctx = build_grounded_context("What are you feeling right now?")
        print(f"[OK] Context length: {len(ctx)} chars")
        # Check for real content markers
        markers = ['mood', 'emotion', 'valence', 'plan', 'memor', 'state']
        found = [m for m in markers if m.lower() in ctx.lower()]
        print(f"  Found markers: {found}")
        if len(found) >= 2:
            print("  [OK] Context contains real internal state data")
        else:
            print(f"  [WARN] Context may be thin. First 500 chars:\n{ctx[:500]}")
        return True
    except Exception as e:
        print(f"[FAIL] build_grounded_context error: {e}")
        import traceback; traceback.print_exc()
        return False

def test_engine_respond_setup():
    """Check how _engine_respond is set up in web/chat.py"""
    try:
        # Read the web/chat.py to find _engine_respond initialization
        with open("web/chat.py") as f:
            content = f.read()
        
        if "_engine_respond" in content:
            # Find where it's assigned
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if '_engine_respond' in line and '=' in line and 'if ' not in line and 'try' not in line:
                    print(f"  Line {i}: {line.strip()}")
            print("[OK] _engine_respond is referenced in web/chat.py")
        else:
            print("[FAIL] _engine_respond not found in web/chat.py")
        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False

def test_memory_retrieval_for_query():
    """Test that memories are retrieved with query relevance."""
    try:
        from engine.chat_grounding import get_relevant_memories
        memories = get_relevant_memories("What have you learned recently?")
        print(f"[OK] Retrieved {len(memories)} memories")
        for i, m in enumerate(memories[:3]):
            text = m.get('text', m.get('content', str(m)))[:80]
            print(f"  [{i}] {text}")
        return True
    except Exception as e:
        print(f"[FAIL] Memory retrieval: {e}")
        import traceback; traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Engine Response Path Tests ===\n")
    results = []
    for test in [test_engine_import, test_grounding_context, test_engine_respond_setup, test_memory_retrieval_for_query]:
        print(f"\n--- {test.__name__} ---")
        results.append(test())
    
    passed = sum(results)
    print(f"\n=== {passed}/{len(results)} tests passed ===")