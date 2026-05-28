"""Quick test: verify enriched identity preamble produces warm, genuine responses."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import generate_response_with_metadata

queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "Do you have real memories?",
]

for q in queries:
    print(f"\nUSER: {q}")
    try:
        result = generate_response_with_metadata(q, history=[])
        text = result.get("response", "") if isinstance(result, dict) else str(result)
        print(f"AGENT: {text[:300]}")
        
        # Quality checks
        has_first_person = any(w in text.lower() for w in ["i ", "i'm", "my ", "i've"])
        not_generic = "I don't have" not in text or "I don't have feelings" not in text
        has_substance = len(text) > 50
        
        status = "PASS" if (has_first_person and not_generic and has_substance) else "FAIL"
        print(f"  [{status}] first_person={has_first_person} not_generic={not_generic} substance={has_substance}")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n=== Done ===")