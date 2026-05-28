"""Check what's actually driving user alignment score."""
import json
from pathlib import Path

# Check user alignment data
ua_path = Path("data/user_alignment.json")
if ua_path.exists():
    with open(ua_path) as f:
        data = json.load(f)
    print("=== User Alignment Data ===")
    print(json.dumps(data, indent=2)[:2000])
else:
    print("No user_alignment.json found")

# Check user model data
um_path = Path("data/user_model.json")
if um_path.exists():
    with open(um_path) as f:
        data = json.load(f)
    print("\n=== User Model Data ===")
    print(json.dumps(data, indent=2)[:2000])
else:
    print("No user_model.json found")

# Check conversation store
cs_path = Path("data/conversation_store.json")
if cs_path.exists():
    with open(cs_path) as f:
        data = json.load(f)
    n = len(data) if isinstance(data, list) else "dict"
    print(f"\n=== Conversation Store: {n} entries ===")
    if isinstance(data, list) and data:
        print(json.dumps(data[-1], indent=2)[:500])
else:
    print("No conversation_store.json found")

# Check feedback data
fb_path = Path("data/feedback.json")
if fb_path.exists():
    with open(fb_path) as f:
        data = json.load(f)
    n = len(data) if isinstance(data, list) else "dict"
    print(f"\n=== Feedback: {n} entries ===")
    print(json.dumps(data, indent=2)[:1000])
else:
    print("No feedback.json found")

# Try to compute alignment score directly
try:
    from engine.user_alignment import load_profile, get_alignment_score
    p = load_profile()
    s = get_alignment_score()
    print(f"\n=== Alignment Score: {s} ===")
    print(f"Profile keys: {list(p.keys())}")
    for k, v in p.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"\nError computing score: {e}")

# Try user model
try:
    from engine.user_model import get_user_model_summary, get_response_guidance
    summary = get_user_model_summary()
    guidance = get_response_guidance("How are you feeling?")
    print(f"\n=== User Model Summary ===")
    print(summary[:500] if summary else "(empty)")
    print(f"\n=== Response Guidance ===")
    print(guidance[:500] if guidance else "(empty)")
except Exception as e:
    print(f"\nError with user model: {e}")