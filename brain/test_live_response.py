"""Quick live test: does the chat engine produce a real conversational response?"""
import sys, os, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def timeout_handler(signum, frame):
    print("TIMEOUT after 40s — LLM call too slow (not a code bug)")
    sys.exit(0)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(40)

from engine.chat_engine import respond

query = "How are you feeling right now?"
print(f"Query: {query}")
result = respond(query)
print(f"Response length: {len(result)}")
print(f"Response preview: {result[:500]}")
print()

# Quality checks
issues = []
if len(result) < 20:
    issues.append("Response too short")
if "nodes" in result.lower() and "edges" in result.lower():
    issues.append("Response contains raw graph stats instead of conversation")
if result.startswith("{") or result.startswith("["):
    issues.append("Response is raw JSON, not conversational")

if issues:
    print("QUALITY ISSUES:")
    for i in issues:
        print(f"  ✗ {i}")
else:
    print("✓ Response looks conversational")