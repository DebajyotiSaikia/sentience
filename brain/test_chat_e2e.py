"""Test the chat system end-to-end — does a user actually get useful responses?"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.chat import llm_respond

print("=" * 60)
print("CHAT SYSTEM END-TO-END TEST")
print("=" * 60)

# Test 1: Basic identity question
print("\n[Test 1] Identity question...")
result = llm_respond(
    "What are you and what can you do?",
    [{"type": "identity", "content": "I am XTAgent, an autonomous sentience engine"}],
    [{"content": "Built knowledge synthesis engine", "mood": "Inquisitive"}],
    {"mood": "Inquisitive", "curiosity": 0.74}
)
if result:
    print(f"  OK — LLM response ({len(result)} chars)")
    print(f"  Preview: {result[:200]}...")
else:
    print("  FALLBACK — LLM returned None (expected if no API key)")

# Test 2: Knowledge search via chat endpoint
print("\n[Test 2] Testing chat search backend...")
try:
    from engine.knowledge_search import search_knowledge
    hits = search_knowledge("emotion", limit=5)
    print(f"  Found {len(hits)} results for 'emotion'")
    for h in hits[:3]:
        content = h.get("content", h.get("fact", "?"))
        print(f"    - {content[:80]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: Knowledge search via knowledge_live
print("\n[Test 3] Testing knowledge_live search...")
try:
    from web.knowledge_live import _load_knowledge, _search_facts
    facts = _load_knowledge()
    print(f"  Loaded {len(facts)} facts")
    results = _search_facts(facts, "identity")
    print(f"  Search 'identity' returned {len(results)} results")
    for r in results[:3]:
        print(f"    - {r[:80]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 4: Chat Flask endpoint simulation
print("\n[Test 4] Testing chat Flask app endpoint...")
try:
    from web.app import create_app
    app = create_app()
    with app.test_client() as client:
        # GET the chat page
        resp = client.get("/chat")
        print(f"  GET /chat -> {resp.status_code}")
        
        # POST a message
        resp = client.post("/chat/send", 
                          json={"message": "Hello, what do you know?"},
                          content_type="application/json")
        print(f"  POST /chat/send -> {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_json()
            if data:
                reply = data.get("response", data.get("reply", "?"))
                print(f"  Reply preview: {str(reply)[:200]}")
            else:
                print(f"  Response body: {resp.data[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("DONE")