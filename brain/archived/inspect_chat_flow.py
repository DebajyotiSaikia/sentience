import sys
sys.path.insert(0, '/workspace')

# 1. Test what generate_response actually returns
from engine.chat_engine import generate_response, classify_intent as ce_classify
from engine.conversation_intelligence import classify_intent as ci_classify

queries = [
    "How are you feeling?",
    "What are your plans?",
    "What are you thinking about?",
    "Tell me about consciousness",
    "Hello!",
]

print("=== Intent comparison ===")
for q in queries:
    ce = ce_classify(q)
    ci = ci_classify(q)
    print(f"  '{q}'\n    chat_engine: {ce}\n    conv_intel:  {ci}\n")

print("=== Response test ===")
for q in queries[:2]:
    try:
        resp = generate_response(q)
        if isinstance(resp, dict):
            print(f"  '{q}' -> keys: {list(resp.keys())}")
            for k, v in resp.items():
                val_str = str(v)[:120]
                print(f"    {k}: {val_str}")
        else:
            print(f"  '{q}' -> type={type(resp).__name__}, len={len(str(resp))}")
            print(f"    {str(resp)[:200]}")
    except Exception as e:
        print(f"  '{q}' -> ERROR: {e}")
    print()