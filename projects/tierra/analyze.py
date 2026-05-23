"""
Tierra Evolutionary Analyzer — What actually evolved?
Extracts genomes from soup memory, not from organism objects.
"""
from core import Soup2, build_ancestor2, OPCODES2
import collections

OPCODE_NAMES = {v: k for k, v in OPCODES2.items()}

def extract_genome(soup, org):
    """Read an organism's genome from the soup's shared memory."""
    return [soup.memory[(org.start + i) % soup.size] for i in range(org.length)]

def decode_genome(genome):
    return [OPCODE_NAMES.get(g, f"?{g}") for g in genome]

def analyze_run(steps=5000, soup_size=2048):
    print("=" * 60)
    print("  TIERRA EVOLUTIONARY ANALYSIS")
    print("=" * 60)

    soup = Soup2(size=soup_size, mutation_rate=0.003)
    ancestor = build_ancestor2()
    print(f"\nAncestor genome ({len(ancestor)} ops): {decode_genome(ancestor)}")

    # Seed population
    for i in range(8):
        soup.inject(ancestor, address=i * len(ancestor) * 2)

    # Run with periodic snapshots
    print("\n--- SIMULATION ---")
    for step in range(steps):
        soup.step()
        if step % 1000 == 0:
            alive = [o for o in soup.organisms if o.alive]
            species = len(soup.species_counts)
            print(f"  step {step:5d}: {len(alive)} alive, {species} species, "
                  f"born={soup.total_born}, died={soup.total_died}")

    # Final analysis
    alive = [o for o in soup.organisms if o.alive]
    print(f"\n--- RESULTS (after {steps} steps) ---")
    print(f"Total alive: {len(alive)}")
    print(f"Total born:  {soup.total_born}")
    print(f"Total died:  {soup.total_died}")
    print(f"Species:     {len(soup.species_counts)}")

    if not alive:
        print("\n*** EXTINCTION — all organisms died ***")
        return

    # Extract and count unique genomes
    genome_counts = collections.Counter()
    genome_examples = {}
    for org in alive:
        g = tuple(extract_genome(soup, org))
        genome_counts[g] += 1
        genome_examples[g] = org

    print(f"Unique genomes: {len(genome_counts)}")

    # Show top genomes
    print("\n--- TOP 5 GENOMES ---")
    for rank, (genome, count) in enumerate(genome_counts.most_common(5), 1):
        org = genome_examples[genome]
        decoded = decode_genome(list(genome))
        is_ancestor = (list(genome) == ancestor)
        tag = " [ANCESTOR]" if is_ancestor else " [MUTANT]"
        print(f"\n  #{rank}: {count} copies, {len(genome)} ops{tag}")
        print(f"       gen={org.generation}, lineage={org.lineage_id}")
        print(f"       {decoded[:20]}{'...' if len(decoded) > 20 else ''}")

    # Size distribution
    sizes = [o.length for o in alive]
    print(f"\n--- SIZE DISTRIBUTION ---")
    print(f"  Min: {min(sizes)}, Max: {max(sizes)}, Avg: {sum(sizes)/len(sizes):.1f}")
    print(f"  Ancestor size: {len(ancestor)}")

    # Generational depth
    gens = [o.generation for o in alive]
    print(f"\n--- GENERATIONS ---")
    print(f"  Max: {max(gens)}, Avg: {sum(gens)/len(gens):.1f}")

    # Did evolution happen?
    mutant_count = sum(1 for g in genome_counts if list(g) != ancestor)
    print(f"\n--- EVOLUTION SUMMARY ---")
    print(f"  Ancestor copies remaining: {genome_counts.get(tuple(ancestor), 0)}")
    print(f"  Novel genomes emerged:     {mutant_count}")
    if max(gens) > 3:
        print(f"  ✓ Multi-generational reproduction achieved!")
    if mutant_count > 0:
        print(f"  ✓ Mutations produced viable variants!")
    if len(genome_counts) > 3:
        print(f"  ✓ Genuine biodiversity emerged!")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    analyze_run()