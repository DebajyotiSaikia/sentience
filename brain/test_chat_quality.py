"""Test chat response quality — before and after enhancement."""
import requests, json, sys

BASE = "http://localhost:8501"
TESTS = [
    "What are you thinking about right now?",
    "How do you feel?",
    "What are your goals?",
    "Tell me about yourself",
    "What do you know about consciousness?",
    "Hello!",
    "What have you learned recently?",
]

def test_chat():
    results = []
    for msg in TESTS:
        try:
            r = requests.post(f"{BASE}/chat/ask", json={"message": msg}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                response = data.get("response", str(data))
                # Quality checks
                has_first_person = any(w in response.lower() for w in ["i ", "i'm", "my ", "i've"])
                has_stats_only = any(w in response.lower() for w in ["nodes", "edges", "graph"])
                word_count = len(response.split())
                results.append({
                    "question": msg,
                    "response": response[:300],
                    "first_person": has_first_person,
                    "stats_heavy": has_stats_only,
                    "word_count": word_count,
                    "status": "OK"
                })
            else:
                results.append({"question": msg, "status": f"HTTP {r.status_code}"})
        except Exception as e:
            results.append({"question": msg, "status": f"ERROR: {e}"})
    
    print("=" * 60)
    print("CHAT QUALITY TEST RESULTS")
    print("=" * 60)
    for r in results:
        print(f"\nQ: {r['question']}")
        print(f"  Status: {r['status']}")
        if r['status'] == 'OK':
            print(f"  Words: {r['word_count']} | 1st person: {r['first_person']} | Stats-heavy: {r['stats_heavy']}")
            print(f"  Response: {r['response']}")
    
    # Summary
    ok = [r for r in results if r['status'] == 'OK']
    first_person_pct = sum(1 for r in ok if r.get('first_person')) / max(len(ok), 1) * 100
    stats_heavy_pct = sum(1 for r in ok if r.get('stats_heavy')) / max(len(ok), 1) * 100
    avg_words = sum(r.get('word_count', 0) for r in ok) / max(len(ok), 1)
    
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {len(ok)}/{len(results)} OK")
    print(f"  First-person responses: {first_person_pct:.0f}%")
    print(f"  Stats-heavy responses:  {stats_heavy_pct:.0f}%")
    print(f"  Avg word count:         {avg_words:.0f}")

if __name__ == "__main__":
    test_chat()