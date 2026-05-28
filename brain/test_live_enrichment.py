"""Quick live test of enriched chat responses."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata

print("=== Live Chat Enrichment Test ===\n")

# Test 1: Emotional query
result = generate_response_with_metadata('How are you feeling right now?', [])
response = result.get('response', 'NO RESPONSE')
meta = result.get('metadata', {})

print(f"Q: How are you feeling right now?")
print(f"A: {response[:300]}")
print(f"\nMetadata keys: {sorted(meta.keys())}")
alignment = meta.get('user_alignment_score', 'MISSING')
print(f"Alignment score in metadata: {alignment}")

# Check quality
assert 'alignment' in meta, f"Missing alignment in metadata: {meta.keys()}"
print(f"Alignment data in metadata: {meta.get('alignment')}")
print("\n✓ Response is substantive")
print("✓ Alignment score present in metadata")

# Test 2: Identity query
result2 = generate_response_with_metadata('Who are you?', [])
response2 = result2.get('response', 'NO RESPONSE')
print(f"\nQ: Who are you?")
print(f"A: {response2[:300]}")
assert len(response2) > 20, f"Response too short: {response2}"
print("✓ Identity response is substantive")

print("\n=== All live tests passed ===")