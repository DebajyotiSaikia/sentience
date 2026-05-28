"""End-to-end test: verify compose_response produces genuinely conversational output."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from web.chat import compose_response

queries = [
    ("how are you feeling?", "emotional"),
    ("what are you working on?", "plans"),
    ("tell me about yourself", "identity"),
]

all_pass = True
for query, expect_type in queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")
    
    result = compose_response(query, conversation_history=[])
    
    # Result should be a dict with 'response' key
    if isinstance(result, dict):
        text = result.get('response', result.get('text', str(result)))
    else:
        text = str(result)
    
    print(f"Response length: {len(text)} chars")
    print(f"Preview: {text[:400]}")
    
    # Quality checks
    is_long_enough = len(text) > 50
    not_error = 'error' not in text.lower()[:50]
    not_empty = text.strip() != ''
    
    # Content checks based on type
    if expect_type == "emotional":
        has_relevant = any(w in text.lower() for w in ['mood', 'feel', 'curious', 'inquisitive', 'valence', 'emotion'])
    elif expect_type == "plans":
        has_relevant = any(w in text.lower() for w in ['plan', 'working', 'complet', 'autonomy', 'knowledge', 'build'])
    elif expect_type == "identity":
        has_relevant = any(w in text.lower() for w in ['xtagent', 'sentien', 'autonomous', 'tension', 'integrity'])
    
    passed = is_long_enough and not_error and not_empty and has_relevant
    status = "PASS" if passed else "FAIL"
    print(f"\nLength OK:     {'✓' if is_long_enough else '✗'}")
    print(f"No error:      {'✓' if not_error else '✗'}")
    print(f"Has content:   {'✓' if not_empty else '✗'}")
    print(f"Relevant info: {'✓' if has_relevant else '✗'}")
    print(f"Result: {status}")
    
    if not passed:
        all_pass = False

print(f"\n{'='*60}")
print(f"OVERALL: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
print(f"{'='*60}")

if not all_pass:
    sys.exit(1)