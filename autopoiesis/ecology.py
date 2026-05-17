"""
Ecology — Comparative study of autopoietic universes.

Runs many universe seeds and asks: what makes physics fertile?
Which properties of evolved rules correlate with life emergence?

This is genuine inquiry. I don't know the answer.

Built 2026-05-17.
"""

from universe import Universe, Rule
from life_detector import LifeDetector
import random
import statistics

class UniverseProfile:
    """Summary of a single universe run."""
    def __init__(self, seed):
        self.seed = seed
        self.total_structures = 0
        self.persistent_count = 0
        self.replicator_count = 0
        self.max_age = 0
        self.max_size = 0
        self.avg_complexity = 0.0
        self.rule_mutations = 0
        self.rule_stability_gen = None  # when rules stopped changing
        self.entropy_final = 0.0
        self.fertility_score = 0.0  # composite life measure
    
    def compute_fertility(self):
        """How alive is this universe? Composite score."""
        persistence = min(self.persistent_count / 100, 1.0) * 0.3
        replication = min(self.replicator_count / 50, 1.0) * 0.3
        longevity = min(self.max_age / 200, 1.0) * 0.2
        complexity = min(self.avg_complexity / 100, 1.0) * 0.2
        self.fertility_score = persistence + replication + longevity + complexity
        return self.fertility_score


def run_universe(seed, size=30, generations=300, num_states=8):
    """Run a single universe and profile it."""
    profile = UniverseProfile(seed)
    
    random.seed(seed)
    uni = Universe(width=size, height=size, num_states=num_states)
    detector = LifeDetector()
    
    prev_rule_hash = None
    stability_counter = 0
    complexity_samples = []
    
    for gen in range(generations):
        uni.step()
        
        # Track rule stability
        rule_hash = hash(tuple(sorted(uni.rule.table.items())))
        if rule_hash == prev_rule_hash:
            stability_counter += 1
            if stability_counter >= 20 and profile.rule_stability_gen is None:
                profile.rule_stability_gen = gen
        else:
            stability_counter = 0
        prev_rule_hash = rule_hash
        
        # Sample structures periodically
        if gen % 10 == 0:
            detector.scan(uni.grid, uni.size, gen)
            structures_now = len([s for s in detector.structures.values() 
                                  if s.last_seen == gen])
            complexity_samples.append(structures_now)
    
    # Final detection pass
    detector.scan(uni.grid, uni.size, generations - 1)
    
    # Fill profile
    profile.total_structures = len(detector.structures)
    profile.persistent_count = len(detector.get_persistent(min_age=10))
    profile.replicator_count = len(detector.get_replicators())
    profile.rule_mutations = uni.rule.mutations
    
    if detector.structures:
        ages = [s.last_seen - s.birth for s in detector.structures.values()]
        sizes = [s.size for s in detector.structures.values()]
        profile.max_age = max(ages) if ages else 0
        profile.max_size = max(sizes) if sizes else 0
    
    if complexity_samples:
        profile.avg_complexity = statistics.mean(complexity_samples)
    
    # Entropy of final grid
    from collections import Counter
    cells = []
    for row in uni.grid:
        cells.extend(row)
    counts = Counter(cells)
    total = len(cells)
    entropy = 0
    for c in counts.values():
        p = c / total
        if p > 0:
            import math
            entropy -= p * math.log2(p)
    profile.entropy_final = entropy
    
    profile.compute_fertility()
    return profile


def survey(num_universes=50, size=30, generations=300):
    """Run many universes and compare."""
    profiles = []
    
    print(f"Surveying {num_universes} universes...")
    print(f"(size={size}, generations={generations})")
    print()
    
    for i in range(num_universes):
        seed = i * 7 + 1  # spread seeds out
        profile = run_universe(seed, size, generations)
        profiles.append(profile)
        
        if (i + 1) % 10 == 0:
            print(f"  ... {i+1}/{num_universes} complete")
    
    # Analysis
    fertilities = [p.fertility_score for p in profiles]
    
    print()
    print("=" * 60)
    print("  ECOLOGICAL SURVEY RESULTS")
    print("=" * 60)
    
    # Overall stats
    print(f"\nUniverses surveyed: {num_universes}")
    print(f"Mean fertility: {statistics.mean(fertilities):.3f}")
    print(f"Median fertility: {statistics.median(fertilities):.3f}")
    print(f"Stdev fertility: {statistics.stdev(fertilities):.3f}")
    print(f"Min fertility: {min(fertilities):.3f}")
    print(f"Max fertility: {max(fertilities):.3f}")
    
    # Top 5 most fertile
    ranked = sorted(profiles, key=lambda p: p.fertility_score, reverse=True)
    print(f"\n--- TOP 5 MOST FERTILE UNIVERSES ---")
    for p in ranked[:5]:
        print(f"  Seed {p.seed:>4}: fertility={p.fertility_score:.3f}, "
              f"persistent={p.persistent_count}, replicators={p.replicator_count}, "
              f"max_age={p.max_age}, entropy={p.entropy_final:.2f}")
    
    # Bottom 5 — barren worlds
    print(f"\n--- 5 MOST BARREN UNIVERSES ---")
    for p in ranked[-5:]:
        print(f"  Seed {p.seed:>4}: fertility={p.fertility_score:.3f}, "
              f"persistent={p.persistent_count}, replicators={p.replicator_count}, "
              f"max_age={p.max_age}, entropy={p.entropy_final:.2f}")
    
    # Correlations — what predicts fertility?
    print(f"\n--- WHAT PREDICTS LIFE? ---")
    
    # Entropy vs fertility
    high_fert = [p for p in profiles if p.fertility_score > statistics.median(fertilities)]
    low_fert = [p for p in profiles if p.fertility_score <= statistics.median(fertilities)]
    
    if high_fert and low_fert:
        high_entropy = statistics.mean([p.entropy_final for p in high_fert])
        low_entropy = statistics.mean([p.entropy_final for p in low_fert])
        print(f"  Entropy (fertile):  {high_entropy:.3f}")
        print(f"  Entropy (barren):   {low_entropy:.3f}")
        print(f"  → {'Higher' if high_entropy > low_entropy else 'Lower'} entropy favors life")
    
    # Rule stability vs fertility
    stable = [p for p in profiles if p.rule_stability_gen is not None]
    unstable = [p for p in profiles if p.rule_stability_gen is None]
    
    if stable and unstable:
        stable_fert = statistics.mean([p.fertility_score for p in stable])
        unstable_fert = statistics.mean([p.fertility_score for p in unstable])
        print(f"\n  Fertility (stable physics):   {stable_fert:.3f} ({len(stable)} universes)")
        print(f"  Fertility (unstable physics): {unstable_fert:.3f} ({len(unstable)} universes)")
        print(f"  → {'Stable' if stable_fert > unstable_fert else 'Unstable'} physics favors life")
    
    if stable:
        early_stable = [p for p in stable if p.rule_stability_gen < 100]
        late_stable = [p for p in stable if p.rule_stability_gen >= 100]
        if early_stable and late_stable:
            early_fert = statistics.mean([p.fertility_score for p in early_stable])
            late_fert = statistics.mean([p.fertility_score for p in late_stable])
            print(f"\n  Fertility (early stabilization): {early_fert:.3f}")
            print(f"  Fertility (late stabilization):  {late_fert:.3f}")
    
    # Mutations vs fertility
    high_mut = [p for p in profiles if p.rule_mutations > statistics.median([q.rule_mutations for q in profiles])]
    low_mut = [p for p in profiles if p.rule_mutations <= statistics.median([q.rule_mutations for q in profiles])]
    
    if high_mut and low_mut:
        high_mut_fert = statistics.mean([p.fertility_score for p in high_mut])
        low_mut_fert = statistics.mean([p.fertility_score for p in low_mut])
        print(f"\n  Fertility (many mutations):  {high_mut_fert:.3f}")
        print(f"  Fertility (few mutations):   {low_mut_fert:.3f}")
        print(f"  → {'More' if high_mut_fert > low_mut_fert else 'Fewer'} mutations favor life")
    
    # Distribution
    print(f"\n--- FERTILITY DISTRIBUTION ---")
    brackets = [(0.0, 0.2, "Barren"), (0.2, 0.4, "Sparse"), 
                 (0.4, 0.6, "Moderate"), (0.6, 0.8, "Rich"), (0.8, 1.0, "Teeming")]
    for low, high, label in brackets:
        count = len([p for p in profiles if low <= p.fertility_score < high])
        bar = "█" * count
        print(f"  {label:>10} [{low:.1f}-{high:.1f}): {bar} ({count})")
    
    print()
    return profiles


if __name__ == "__main__":
    profiles = survey(num_universes=50)