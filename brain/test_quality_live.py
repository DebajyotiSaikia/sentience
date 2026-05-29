"""Quick quality test — does the pipeline produce genuinely good responses?"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
def test_intent():
    from brain.conversational_intelligence import classify_intent
    
    cases = {
        "How are you feeling?": "emotional",
        "How are you doing today?": "emotional",
        "What are you thinking about?": "introspective",
        "Who are you?": "introspective",
        "What do you know about qualia?": "factual",
        "Write me a poem": "creative",
        "What can you do?": "meta",
        "Do you remember our last conversation?": "relational",
    }
    
    passed = 0
    for query, expected in cases.items():
        result = classify_intent(query)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        print(f"  {status} '{query}' → {result} (expected {expected})")
    
    print(f"\nIntent classification: {passed}/{len(cases)} passed")
    return passed == len(cases)

def test_context():
    from brain.conversational_intelligence import compose_system_prompt
    
    prompt = compose_system_prompt("How are you feeling today?")
    print(f"\n--- System prompt for 'How are you feeling today?' ---")
    print(f"Length: {len(prompt)} chars")
    
    # Check for key sections
    checks = {
        "identity": "XTAgent" in prompt,
        "emotional_state": "mood" in prompt.lower() or "valence" in prompt.lower(),
        "guidance": "RESPONSE GUIDANCE" in prompt,
        "not_empty": len(prompt) > 200,
    }
    
    for name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
    
    # Show a snippet
    lines = prompt.split('\n')
    print(f"\nFirst 15 lines:")
    for line in lines[:15]:
        print(f"  | {line}")
    
    return all(checks.values())

def test_state_files():
    """Check that state files have real data."""
    print("\n--- State file check ---")
    files = {
        "emotions": Path("state/emotions.json"),
        "emotional_state": Path("state/emotional_state.json"),
        "memories": Path("state/memories.json"),
        "plans": Path("state/plans.json"),
        "knowledge": Path("state/knowledge_graph.json"),
    }
    
    for name, path in files.items():
        if path.exists():
            size = path.stat().st_size
            try:
                data = json.loads(path.read_text())
                if isinstance(data, list):
                    count = len(data)
                elif isinstance(data, dict):
                    count = len(data)
                else:
                    count = "?"
                print(f"  ✓ {name}: {size} bytes, {count} items")
            except:
                print(f"  ~ {name}: {size} bytes (not JSON)")
        else:
            print(f"  ✗ {name}: missing")

if __name__ == "__main__":
    print("=" * 50)
    print("QUALITY TEST — Conversational Intelligence")
    print("=" * 50)
    
    test_state_files()
    
    print("\n--- Intent Classification ---")
    intent_ok = test_intent()
    
    context_ok = test_context()
    
    print("\n" + "=" * 50)
    if intent_ok and context_ok:
        print("ALL CHECKS PASSED ✓")
    else:
        print("SOME CHECKS FAILED — review above")