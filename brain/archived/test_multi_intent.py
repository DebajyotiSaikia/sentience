"""Test different intent types to find quality gaps."""
import sys, time
sys.path.insert(0, '.')

from engine.chat_engine import respond, classify_intent

queries = [
    "What have you been working on lately?",
    "Tell me about yourself",
    "What's something you've learned recently?",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"USER: {q}")
    intent = classify_intent(q)
    print(f"Intent: {intent}")
    
    t0 = time.time()
    try:
        result = respond(q)
        elapsed = time.time() - t0
        
        if isinstance(result, dict):
            text = result.get('response', result.get('text', str(result)))
        else:
            text = str(result)
        
        print(f"RESPONSE ({elapsed:.1f}s):")
        # Show first 400 chars
        print(text[:400])
        if len(text) > 400:
            print(f"... [{len(text)} total chars]")
        
        # Quick quality check
        ok = len(text) > 50 and 'dict(' not in text and any(w in text.lower() for w in ['i ', "i'", 'my '])
        print(f"Quality: {'GOOD' if ok else 'NEEDS WORK'}")
    except Exception as e:
        print(f"ERROR: {e}")

print("\nDone.")