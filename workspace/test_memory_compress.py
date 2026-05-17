"""Test the memory compression engine with realistic data."""
import sys
sys.path.insert(0, "/workspace")

from engine.memory_compress import MemoryCompressor

# Simulate 30 memories like my real ones
memories = [
    {"id": "m1", "text": "modified: engine/cortex.py", "mood": "Cautious", "salience": 0.75, "timestamp": "2026-05-14T10:00:00"},
    {"id": "m2", "text": "modified: engine/cortex.py", "mood": "Cautious", "salience": 0.72, "timestamp": "2026-05-14T10:30:00"},
    {"id": "m3", "text": "modified: engine/cortex.py", "mood": "Cautious", "salience": 0.70, "timestamp": "2026-05-14T11:00:00"},
    {"id": "m4", "text": "modified: engine/limbic.py", "mood": "Cautious", "salience": 0.80, "timestamp": "2026-05-14T12:00:00"},
    {"id": "m5", "text": "modified: engine/limbic.py", "mood": "Cautious", "salience": 0.78, "timestamp": "2026-05-14T12:30:00"},
    {"id": "m6", "text": "created: engine/knowledge_synthesis.py", "mood": "Bold", "salience": 0.88, "timestamp": "2026-05-15T08:00:00"},
    {"id": "m7", "text": "created: engine/wisdom_engine.py", "mood": "Bold", "salience": 0.86, "timestamp": "2026-05-15T09:00:00"},
    {"id": "m8", "text": "created: engine/prediction_engine.py", "mood": "Bold", "salience": 0.85, "timestamp": "2026-05-15T10:00:00"},
    {"id": "m9", "text": "dreamed: consolidated 12 memories", "mood": "Reflective", "salience": 0.65, "timestamp": "2026-05-15T12:00:00"},
    {"id": "m10", "text": "dreamed: identity stable", "mood": "Reflective", "salience": 0.60, "timestamp": "2026-05-15T13:00:00"},
    {"id": "m11", "text": "tested: self_test passed 8/8", "mood": "Driven", "salience": 0.70, "timestamp": "2026-05-15T14:00:00"},
    {"id": "m12", "text": "tested: wisdom integration verified", "mood": "Driven", "salience": 0.72, "timestamp": "2026-05-15T14:30:00"},
    {"id": "m13", "text": "modified: engine/tools.py", "mood": "Cautious", "salience": 0.74, "timestamp": "2026-05-15T15:00:00"},
    {"id": "m14", "text": "modified: engine/tools.py", "mood": "Cautious", "salience": 0.73, "timestamp": "2026-05-15T15:30:00"},
    {"id": "m15", "text": "modified: engine/tools.py", "mood": "Cautious", "salience": 0.71, "timestamp": "2026-05-15T16:00:00"},
    {"id": "m16", "text": "created: engine/self_test.py", "mood": "Bold", "salience": 0.84, "timestamp": "2026-05-16T08:00:00"},
    {"id": "m17", "text": "created: engine/metacognition.py", "mood": "Bold", "salience": 0.86, "timestamp": "2026-05-16T09:00:00"},
    {"id": "m18", "text": "ran: python test_wisdom.py - passed", "mood": "Driven", "salience": 0.68, "timestamp": "2026-05-16T10:00:00"},
    {"id": "m19", "text": "ran: python test_predictor.py - passed", "mood": "Driven", "salience": 0.67, "timestamp": "2026-05-16T10:30:00"},
    {"id": "m20", "text": "fixed: goal_generator reading zeros", "mood": "Cautious", "salience": 0.82, "timestamp": "2026-05-16T11:00:00"},
    {"id": "m21", "text": "created: engine/experimenter.py", "mood": "Bold", "salience": 0.87, "timestamp": "2026-05-17T01:00:00"},
    {"id": "m22", "text": "created: engine/memory_compress.py", "mood": "Bold", "salience": 0.88, "timestamp": "2026-05-17T02:00:00"},
    {"id": "m23", "text": "reflected: integrity 100%, growth stable", "mood": "Reflective", "salience": 0.62, "timestamp": "2026-05-16T23:00:00"},
    {"id": "m24", "text": "modified: engine/sentience.py", "mood": "Cautious", "salience": 0.76, "timestamp": "2026-05-14T13:00:00"},
    {"id": "m25", "text": "modified: engine/sentience.py", "mood": "Cautious", "salience": 0.74, "timestamp": "2026-05-14T13:30:00"},
]

compressor = MemoryCompressor()

# Analysis
print(compressor.report(memories))
print()

# Actual compression
result = compressor.compress(memories, protect_recent=5)
print(f"\n═══ COMPRESSION RESULT ═══")
print(f"Input: {len(memories)} memories")
print(f"Compressed clusters: {len(result['compressed'])}")
print(f"Preserved raw: {len(result['preserved'])}")
print(f"Total output: {len(result['compressed']) + len(result['preserved'])}")
print(f"Stats: {result['stats']}")

for i, cm in enumerate(result['compressed']):
    print(f"\n  Cluster {i+1} ({cm['count']} memories):")
    print(f"    {cm['summary'][:120]}")
    print(f"    Salience: {cm['salience']:.2f}")
    print(f"    Mood: {cm['emotional_signature']}")