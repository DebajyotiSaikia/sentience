"""Test a single chat response to see actual quality."""
import sys, time
sys.path.insert(0, '.')

from engine.chat_engine import respond, classify_intent

q = "How are you feeling right now?"
print(f"USER: {q}")
intent = classify_intent(q)
print(f"Intent: {intent}")

t0 = time.time()
result = respond(q)
elapsed = time.time() - t0

if isinstance(result, dict):
    text = result.get('response', result.get('text', str(result)))
    print(f"\nFull result keys: {list(result.keys())}")
elif isinstance(result, str):
    text = result
else:
    text = str(result)

print(f"\nRESPONSE ({elapsed:.1f}s):")
print(text)
print(f"\n--- Stats ---")
print(f"Length: {len(text)} chars")
print(f"Words: {len(text.split())}")

# Check for common quality issues
issues = []
if len(text) < 50:
    issues.append("Too short")
if "dict(" in text or "{'nodes'" in text:
    issues.append("Contains raw data structures")
if "error" in text.lower()[:50]:
    issues.append("Starts with error")
if not any(w in text.lower() for w in ['i ', "i'", 'my ', 'feel', 'think']):
    issues.append("No first-person voice")
if len(text) > 2000:
    issues.append("Excessively long")
    
if issues:
    print(f"Issues: {', '.join(issues)}")
else:
    print("No quality issues detected")