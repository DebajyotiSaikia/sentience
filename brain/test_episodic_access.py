"""Test that we can access the episodic memory store."""
import sys
sys.path.insert(0, "/workspace")

try:
    from engine.memory import Memory
    m = Memory()
    # Try recall_by_keywords
    results = m.recall_by_keywords(["dream", "feeling"], top_k=5)
    print(f"recall_by_keywords returned {len(results)} results")
    if results:
        for r in results[:3]:
            print(f"  Type: {type(r)}")
            if isinstance(r, dict):
                print(f"  Keys: {list(r.keys())[:6]}")
                print(f"  Text: {str(r.get('text', ''))[:80]}")
            elif isinstance(r, tuple):
                print(f"  Tuple len: {len(r)}, first: {str(r[0])[:80]}")
            else:
                print(f"  Value: {str(r)[:80]}")
    
    # Try recent_episodes
    recent = m.recent_episodes(5)
    print(f"\nrecent_episodes returned {len(recent)} results")
    if recent:
        r = recent[0]
        print(f"  Type: {type(r)}, keys: {list(r.keys())[:6] if isinstance(r, dict) else 'N/A'}")
    
    print("\nEpisodic memory access: OK")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()