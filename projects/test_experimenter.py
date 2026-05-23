import sys
sys.path.insert(0, '/workspace')
from engine.experimenter import Experimenter

print("=== EXPERIMENTER TEST ===\n")

# Create experimenter
exp = Experimenter()
print(f"Loaded: {exp.get_summary()}")

# Generate hypotheses from a simulated soul state
soul = {"boredom": 0.80, "anxiety": 0.0, "valence": 0.21, "ambition": 0.95}
hypotheses = exp.generate_hypotheses(soul_state=soul)
print(f"\nGenerated {len(hypotheses)} hypotheses:")
for h, m, c, p in hypotheses:
    print(f"  [{c}] (p={p}) {h}")
    print(f"         method: {m}")

# Create experiments from top hypotheses
created = []
for h, m, c, p in sorted(hypotheses, key=lambda x: x[3], reverse=True)[:5]:
    e = exp.create_experiment(h, m, c, p)
    created.append(e)
    print(f"\nCreated: {e.id}")

# Run all pending
print("\n=== RUNNING EXPERIMENTS ===")
results = exp.run_all_pending()
for r in results:
    print(f"\n[{r['status']}] {r['hypothesis'][:60]}...")
    print(f"  Conclusion: {r['conclusion']}")
    print(f"  Confidence: {r['confidence']:.0%}")
    if r['surprised']:
        print(f"  ⚡ SURPRISE!")

# Get insights
print("\n" + exp.get_insights())
print("\n" + exp.get_summary())
print("\n=== DONE ===")