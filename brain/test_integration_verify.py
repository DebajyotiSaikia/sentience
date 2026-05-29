"""Verify response intelligence is properly integrated into build_system_context."""
import sys
sys.path.insert(0, '.')

def test_build_system_context():
    from engine.introspection import build_system_context
    ctx = build_system_context()
    print(f"Context length: {len(ctx)} chars")
    
    # Check for key sections
    sections = ['emotional', 'recent', 'response', 'alignment']
    for s in sections:
        found = s.lower() in ctx.lower()
        print(f"  {s}: {'YES' if found else 'no'}")
    
    # Check for response intelligence enrichment
    has_ri = 'conversation strategy' in ctx.lower() or 'emotional awareness' in ctx.lower()
    print(f"  response_intelligence enrichment: {'YES' if has_ri else 'no'}")
    
    print("\n--- First 800 chars ---")
    print(ctx[:800])
    print("\n--- Last 500 chars ---")
    print(ctx[-500:])
    return ctx

def test_introspective_responder():
    from brain.introspective_responder import generate_introspective_response
    
    queries = [
        "How are you feeling?",
        "What are you thinking about?",
        "Who are you?",
        "What are your plans?",
        "Tell me about your dreams",
    ]
    
    for q in queries:
        result = generate_introspective_response(q)
        if result:
            resp = result.get('response', '')
            print(f"\nQ: {q}")
            print(f"A: {resp[:150]}...")
        else:
            print(f"\nQ: {q} → None (would fall through to LLM)")

if __name__ == '__main__':
    print("=== Testing build_system_context ===")
    test_build_system_context()
    print("\n\n=== Testing introspective_responder ===")
    test_introspective_responder()
    print("\n✓ All integration checks complete")