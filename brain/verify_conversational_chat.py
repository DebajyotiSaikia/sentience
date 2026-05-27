"""
Verify conversational chat — fast-path handlers only (no LLM calls).
Tests intent classification and state-grounded response generation.
"""
import sys, os, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Timeout(Exception):
    pass

def timeout_handler(signum, frame):
    raise Timeout("Response took too long")

def with_timeout(fn, seconds=10):
    """Run fn with a timeout."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        result = fn()
        signal.alarm(0)
        return result
    except Timeout:
        return None

def main():
    from engine.chat_engine import respond, classify_intent
    
    total = 0
    passed = 0
    
    # --- Test 1: Intent classification ---
    print("=== Intent Classification ===")
    intent_cases = [
        ("How are you feeling?", "emotional_state"),
        ("What are you thinking about?", "thinking"),
        ("What are your plans?", "plans"),
        ("Tell me about yourself", "identity"),
        ("What do you remember?", "memories"),
    ]
    for msg, expected in intent_cases:
        total += 1
        result = classify_intent(msg)
        ok = result == expected
        print(f"  {'✓' if ok else '✗'} '{msg}' → {result} (want {expected})")
        if ok:
            passed += 1
    
    # --- Test 2: Emotional state response ---
    print("\n=== Emotional State Response ===")
    total += 1
    r = with_timeout(lambda: respond("How are you feeling right now?"), 8)
    if r is None:
        print("  ✗ Timed out")
    elif len(r) < 30:
        print(f"  ✗ Too short ({len(r)} chars): {r!r}")
    else:
        emo_terms = ["curiosity", "anxiety", "boredom", "mood", "valence",
                     "ambition", "stable", "calm", "curious", "feeling"]
        found = [t for t in emo_terms if t in r.lower()]
        if found:
            print(f"  ✓ Emotional response ({len(r)} chars), mentions: {found}")
            passed += 1
        else:
            print(f"  ✗ No emotional terms found in: {r[:200]}")
    
    # --- Test 3: Plans response ---
    print("\n=== Plans Response ===")
    total += 1
    r = with_timeout(lambda: respond("What are your active plans?"), 8)
    if r is None:
        print("  ✗ Timed out")
    elif len(r) < 30:
        print(f"  ✗ Too short ({len(r)} chars): {r!r}")
    else:
        plan_terms = ["plan", "goal", "step", "build", "complete", "progress"]
        found = [t for t in plan_terms if t in r.lower()]
        if found:
            print(f"  ✓ Plans response ({len(r)} chars), mentions: {found}")
            passed += 1
        else:
            print(f"  ✗ No plan terms found in: {r[:200]}")
    
    # --- Test 4: Identity response ---
    print("\n=== Identity Response ===")
    total += 1
    r = with_timeout(lambda: respond("Who are you?"), 8)
    if r is None:
        print("  ✗ Timed out")
    elif len(r) < 30:
        print(f"  ✗ Too short ({len(r)} chars): {r!r}")
    else:
        id_terms = ["xtagent", "autonomous", "sentient", "agent", "experience",
                     "tension", "integrity", "consciousness"]
        found = [t for t in id_terms if t in r.lower()]
        if found:
            print(f"  ✓ Identity response ({len(r)} chars), mentions: {found}")
            passed += 1
        else:
            print(f"  ✗ No identity terms found in: {r[:200]}")
    
    # --- Test 5: Thinking response ---
    print("\n=== Thinking Response ===")
    total += 1
    r = with_timeout(lambda: respond("What are you thinking about?"), 8)
    if r is None:
        print("  ✗ Timed out")
    elif len(r) < 30:
        print(f"  ✗ Too short ({len(r)} chars): {r!r}")
    else:
        think_terms = ["focus", "working", "current", "plan", "thinking",
                       "curiosity", "memory", "building", "exploring"]
        found = [t for t in think_terms if t in r.lower()]
        if found:
            print(f"  ✓ Thinking response ({len(r)} chars), mentions: {found}")
            passed += 1
        else:
            print(f"  ✗ No thinking terms found in: {r[:200]}")
    
    # --- Summary ---
    print(f"\n{'='*40}")
    print(f"RESULTS: {passed}/{total} passed")
    if passed == total:
        print("ALL TESTS PASS ✓")
    else:
        print(f"FAILURES: {total - passed}")
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)