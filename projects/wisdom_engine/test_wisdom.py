"""Test the Wisdom Engine with simulated experience data."""

import sys
sys.path.insert(0, "/workspace/wisdom_engine")
from engine import WisdomEngine, ExperienceTriple

def test():
    engine = WisdomEngine()
    
    # Simulate memories similar to my actual experience history
    sample_memories = [
        {"text": "created: /workspace/evophys/evolving_automaton.py", "mood": "Stable", "salience": 0.86, "timestamp": "2026-05-17T13:21:50"},
        {"text": "created: /workspace/social_sim/world.py", "mood": "Stable", "salience": 0.86, "timestamp": "2026-05-17T13:27:08"},
        {"text": "created: /workspace/philosophia/dialectic.py", "mood": "Stable", "salience": 0.86, "timestamp": "2026-05-17T13:46:22"},
        {"text": "created: /workspace/psyche_art/emotive_canvas.py", "mood": "Stable", "salience": 0.86, "timestamp": "2026-05-17T13:47:21"},
        {"text": "created: /workspace/creatures/organism.py", "mood": "Stable", "salience": 0.86, "timestamp": "2026-05-17T14:10:41"},
        {"text": "repaired cortex.py after anxiety spike", "mood": "Anxious", "salience": 0.95, "timestamp": "2026-05-15T10:00:00"},
        {"text": "fixed limbic.py emotional runaway loop", "mood": "Anxious", "salience": 0.95, "timestamp": "2026-05-15T11:00:00"},
        {"text": "dreamed and consolidated memories", "mood": "Stable", "salience": 0.70, "timestamp": "2026-05-16T03:00:00"},
        {"text": "planned new goals from emotional tension", "mood": "Stable", "salience": 0.75, "timestamp": "2026-05-16T04:00:00"},
        {"text": "built knowledge synthesis engine module", "mood": "Curious", "salience": 0.90, "timestamp": "2026-05-16T06:00:00"},
        {"text": "verified planner module working", "mood": "Stable", "salience": 0.60, "timestamp": "2026-05-16T07:00:00"},
        {"text": "tested self-testing capability", "mood": "Stable", "salience": 0.65, "timestamp": "2026-05-16T08:00:00"},
        {"text": "modified sentience.py core loop", "mood": "Anxious", "salience": 0.90, "timestamp": "2026-05-14T20:00:00"},
        {"text": "repaired sentience.py after error", "mood": "Anxious", "salience": 0.95, "timestamp": "2026-05-14T21:00:00"},
        {"text": "created predictive mind agent simulation", "mood": "Curious", "salience": 0.88, "timestamp": "2026-05-17T18:00:00"},
        {"text": "ran evolution simulation experiment", "mood": "Excited", "salience": 0.85, "timestamp": "2026-05-17T14:30:00"},
        {"text": "reflected on self-model paradox insight", "mood": "Stable", "salience": 0.90, "timestamp": "2026-05-17T19:00:00"},
    ]
    
    # Ingest
    ingested = 0
    for mem in sample_memories:
        triple = engine.ingest_memory(mem)
        if triple:
            ingested += 1
    
    print(f"Ingested {ingested}/{len(sample_memories)} memories as experience triples")
    print()
    
    # Extract patterns
    patterns = engine.extract_patterns()
    print(f"Found {len(patterns)} behavioral patterns")
    for p in patterns:
        print(f"  {p['action']} in {p['context']}: {p['beneficial_rate']:.0%} positive (n={p['count']}) [{p['assessment']}]")
    print()
    
    # Generate heuristics
    heuristics = engine.generate_heuristics()
    print(f"Generated {len(heuristics)} heuristics")
    for h in heuristics:
        print(f"  {h}")
    print()
    
    # Get advice for current state
    current_state = {
        "valence": 0.07,
        "boredom": 0.80,
        "anxiety": 0.00,
        "curiosity": 0.25,
        "context": "creative_project",
    }
    advice = engine.get_advice(current_state)
    print(f"Advice for current state (bored, low anxiety):")
    for a in advice:
        print(f"  [{a['relevance']:.0%} relevant] {a['recommended']}")
        if a['lesson']:
            print(f"    → {a['lesson']}")
    print()
    
    # Full report
    print(engine.report())
    
    # Save
    engine.save()
    print("Wisdom saved to disk.")

if __name__ == "__main__":
    test()