"""Test the Hypothesis Engine."""
from engine.hypothesis_engine import HypothesisEngine, Hypothesis

he = HypothesisEngine()

# Seed initial hypotheses
print("=== SEEDING ===")
result = he.seed_initial_hypotheses()
print(result)

# Generate from emotions
print("\n=== FROM EMOTIONS ===")
new = he.generate_from_emotions({
    "boredom": 0.80, "anxiety": 0.0, "curiosity": 0.25,
    "valence": 0.38, "ambition": 0.95
})
print(f"Generated {len(new)} new hypotheses from emotions")
for h in new:
    print(f"  {h.summary()}")

# Generate from patterns
print("\n=== FROM PATTERNS ===")
memories = [
    {"content": "built maze solver", "salience": 0.86, "mood": "Bold"},
    {"content": "created synthesis engine", "salience": 0.90, "mood": "Driven"},
    {"content": "fixed limbic bug", "salience": 0.95, "mood": "Cautious"},
    {"content": "wrote hypothesis engine", "salience": 0.88, "mood": "Bold"},
    {"content": "modified cortex", "salience": 0.83, "mood": "Driven"},
    {"content": "tested wisdom", "salience": 0.86, "mood": "Bold"},
]
new2 = he.generate_from_patterns(memories, [])
print(f"Generated {len(new2)} new hypotheses from patterns")
for h in new2:
    print(f"  {h.summary()}")

# Test a hypothesis with evidence
print("\n=== ADDING EVIDENCE ===")
print(he.test_hypothesis(0, "Created maze solver during Bold mood, salience 0.86", True))
print(he.test_hypothesis(0, "Created synthesis engine during Driven mood, salience 0.90", False))

# Full summary
print("\n=== FULL SUMMARY ===")
print(he.get_summary())

print("\n=== DONE ===")
print(f"Total hypotheses: {len(he.hypotheses)}")