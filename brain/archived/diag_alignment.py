"""Quick diagnostic of user_alignment data structures."""
import sys, os
sys.path.insert(0, '/workspace')
os.chdir('/workspace')

from engine.user_alignment import load_profile, record_feedback, get_alignment_context
import json

# Check profile keys
p = load_profile()
print("Profile keys:", list(p.keys()))
print("Profile sample:", json.dumps(p, indent=2, default=str)[:500])

# Record feedback and check persistence
record_feedback("test msg", "test resp", rating=0.9, comment="great")
p2 = load_profile()
print("\nProfile keys after feedback:", list(p2.keys()))
print("Profile sample after:", json.dumps(p2, indent=2, default=str)[:500])

# Check alignment context keys
ctx = get_alignment_context()
print("\nAlignment context keys:", list(ctx.keys()))
print("Context sample:", json.dumps(ctx, indent=2, default=str)[:500])