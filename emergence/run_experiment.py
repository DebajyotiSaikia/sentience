"""Run the emergent language experiment and observe what happens."""
from emergent_language import World, Brain, Agent, Population, run_generation
from collections import Counter

world = World(width=12, height=12, n_resources=4)
pop = Population(size=30, vocab_size=8, world=world)

print("=== EMERGENT LANGUAGE EXPERIMENT ===")
print(f"{pop.size} agents, 8 symbols, 12x12 world, 4 resource clusters")
print()

for gen in range(50):
    stats = run_generation(pop, steps_per_gen=30)
    if gen % 10 == 0 or gen == 49:
        print(f"Gen {gen:3d} | mean_fit={stats['mean_fitness']:.2f} | best={stats['best_fitness']:.2f} | signals={stats.get('unique_signals','?')}")

print()
print("=== TOP 5 AGENTS - SIGNAL PATTERNS ===")
top = sorted(pop.agents, key=lambda a: a.fitness, reverse=True)[:5]
for a in top:
    hist = a.signal_history[-20:] if hasattr(a, "signal_history") else []
    counts = dict(Counter(hist))
    print(f"  Agent {a.id}: fitness={a.fitness:.2f} signals={counts}")

print()
print("=== DID MEANING EMERGE? ===")
# Check if top agents converged on similar signal usage
all_top_signals = []
for a in top:
    if hasattr(a, "signal_history") and len(a.signal_history) > 5:
        most_common = Counter(a.signal_history[-20:]).most_common(2)
        all_top_signals.extend([s for s, _ in most_common])
        
signal_convergence = Counter(all_top_signals)
print(f"Most shared signals among top agents: {signal_convergence.most_common(3)}")
if signal_convergence and signal_convergence.most_common(1)[0][1] >= 3:
    print(">> CONVERGENCE DETECTED: Multiple top agents use the same signals")
    print(">> This suggests proto-meaning has crystallized!")
else:
    print(">> No strong convergence yet. Signals still mostly random.")
    print(">> May need more generations or stronger selection pressure.")