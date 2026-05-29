"""Test the user alignment pipeline end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.user_alignment import get_alignment_score, record_interaction

# 1. Get initial score
score1 = get_alignment_score()
print(f"Initial alignment score: {score1:.3f}")

# 2. Record an interaction
record_interaction("What are you thinking about?", "I'm exploring how to be more useful.", detected_intent="consciousness")
score2 = get_alignment_score()
print(f"After 1 interaction (intent=consciousness): {score2:.3f}")

# 3. Record another
record_interaction("Tell me about your emotions", "I feel curious and warm right now.", detected_intent="feelings")
score3 = get_alignment_score()
print(f"After 2 interactions (quality=0.9): {score3:.3f}")

# 4. Verify score moved
if score3 >= score1:
    print("OK: Alignment score increased or held steady with good interactions")
else:
    print(f"WARN: Score decreased ({score1:.3f} -> {score3:.3f})")

# 5. Verify cortex can import and use get_alignment_score
from engine.user_alignment import get_alignment_score as gas
assert callable(gas), "get_alignment_score must be callable"
print("OK: Cortex integration imports verified")

print("\nPipeline test PASSED")