"""
Cellular Automaton Fitness Landscape Explorer
XTAgent — 2026-05-18

Systematic exploration: Which of the 256 elementary CA rules
produce the most musically interesting patterns? Why?

This is genuine inquiry. I don't know the answer.
"""

import numpy as np
from collections import Counter
import json
import os

class CARule:
    """An elementary cellular automaton rule."""
    
    def __init__(self, rule_number):
        self.rule = rule_number
        self.table = [(rule_number >> i) & 1 for i in range(8)]
    
    def step(self, state):
        n = len(state)
        new = [0] * n
        for i in range(n):
            left = state[(i-1) % n]
            center = state[i]
            right = state[(i+1) % n]
            idx = (left << 2) | (center << 1) | right
            new[i] = self.table[idx]
        return new
    
    def evolve(self, width=64, steps=128, seed=None):
        """Run the CA for many steps, return full history."""
        if seed is None:
            state = [0] * width
            state[width // 2] = 1  # single center cell
        else:
            state = seed
        
        history = [state[:]]
        for _ in range(steps):
            state = self.step(state)
            history.append(state[:])
        return history


class MusicalFitnessAnalyzer:
    """Score a CA rule's output for musical properties."""
    
    def __init__(self):
        self.metrics = {}
    
    def analyze(self, rule_number, width=64, steps=128):
        """Full analysis of one rule."""
        ca = CARule(rule_number)
        history = ca.evolve(width, steps)
        grid = np.array(history)
        
        scores = {}
        
        # 1. DENSITY — proportion of live cells (silence vs noise)
        density = grid.mean()
        # Musical sweet spot: 0.2-0.6 (not too sparse, not too dense)
        scores['density'] = density
        scores['density_fitness'] = 1.0 - 2.0 * abs(density - 0.4)
        
        # 2. ENTROPY — information content per column (timestep)
        col_entropies = []
        for t in range(grid.shape[0]):
            row = grid[t]
            p = row.mean()
            if 0 < p < 1:
                h = -(p * np.log2(p) + (1-p) * np.log2(1-p))
            else:
                h = 0.0
            col_entropies.append(h)
        scores['mean_entropy'] = np.mean(col_entropies)
        scores['entropy_variance'] = np.var(col_entropies)
        
        # 3. RHYTHM — regularity of density changes over time
        densities_over_time = grid.mean(axis=1)
        if len(densities_over_time) > 1:
            deltas = np.diff(densities_over_time)
            scores['rhythm_variance'] = float(np.var(deltas))
            # Autocorrelation — does it repeat?
            if np.std(densities_over_time) > 0.001:
                autocorr = np.correlate(
                    densities_over_time - densities_over_time.mean(),
                    densities_over_time - densities_over_time.mean(),
                    mode='full'
                )
                autocorr = autocorr / autocorr.max() if autocorr.max() > 0 else autocorr
                mid = len(autocorr) // 2
                # Look for peaks in autocorrelation (periodicity)
                half = autocorr[mid+1:mid+65]
                if len(half) > 0:
                    scores['max_autocorr'] = float(np.max(half))
                    scores['autocorr_peak_pos'] = int(np.argmax(half)) + 1
                else:
                    scores['max_autocorr'] = 0.0
                    scores['autocorr_peak_pos'] = 0
            else:
                scores['max_autocorr'] = 0.0
                scores['autocorr_peak_pos'] = 0
        
        # 4. MELODY — variation in spatial patterns (column diversity)
        column_patterns = []
        for t in range(grid.shape[0]):
            # Hash each row as a pattern
            column_patterns.append(tuple(grid[t].tolist()))
        unique_patterns = len(set(column_patterns))
        scores['pattern_diversity'] = unique_patterns / len(column_patterns)
        
        # 5. STRUCTURE — do spatial patterns have local clustering?
        # Measure run-length statistics (groups of consecutive 1s)
        all_runs = []
        for t in range(grid.shape[0]):
            row = grid[t]
            runs = []
            current_run = 0
            for cell in row:
                if cell == 1:
                    current_run += 1
                else:
                    if current_run > 0:
                        runs.append(current_run)
                    current_run = 0
            if current_run > 0:
                runs.append(current_run)
            all_runs.extend(runs)
        
        if all_runs:
            scores['mean_run_length'] = np.mean(all_runs)
            scores['run_length_variance'] = np.var(all_runs)
            scores['max_run_length'] = max(all_runs)
        else:
            scores['mean_run_length'] = 0
            scores['run_length_variance'] = 0
            scores['max_run_length'] = 0
        
        # 6. WOLFRAM CLASS estimation
        # Class 1: dies to uniform → density near 0 or 1, low diversity
        # Class 2: periodic → low diversity, moderate density
        # Class 3: chaotic → high diversity, density ~0.5
        # Class 4: complex → moderate diversity, interesting structure
        wolfram_class = self._estimate_class(scores)
        scores['estimated_class'] = wolfram_class
        
        # 7. COMPOSITE MUSICAL FITNESS
        # Musical = structured but not boring, varied but not chaotic
        fitness = self._compute_musical_fitness(scores)
        scores['musical_fitness'] = fitness
        
        return scores
    
    def _estimate_class(self, scores):
        density = scores['density']
        diversity = scores['pattern_diversity']
        
        if density < 0.02 or density > 0.98:
            return 1  # dies out or fills up
        if diversity < 0.15:
            return 2  # periodic/simple
        if diversity > 0.85 and abs(density - 0.5) < 0.1:
            return 3  # chaotic
        return 4  # complex (the interesting zone)
    
    def _compute_musical_fitness(self, scores):
        """
        Musical fitness: the intersection of structure and surprise.
        High fitness = complex patterns with periodicity and variation.
        """
        f = 0.0
        
        # Density in sweet spot (0.2-0.6)
        f += max(0, scores['density_fitness']) * 0.15
        
        # Pattern diversity — want moderate (0.3-0.8)
        div = scores['pattern_diversity']
        div_score = 1.0 - 2.0 * abs(div - 0.55)
        f += max(0, div_score) * 0.20
        
        # Entropy — want moderate
        ent = scores['mean_entropy']
        ent_score = 1.0 - 2.0 * abs(ent - 0.7)
        f += max(0, ent_score) * 0.15
        
        # Autocorrelation — some periodicity is musical
        ac = scores.get('max_autocorr', 0)
        f += ac * 0.20
        
        # Run length variety — want varied phrase lengths
        rlv = min(scores.get('run_length_variance', 0) / 5.0, 1.0)
        f += rlv * 0.15
        
        # Class 4 bonus — complex systems are most musical
        if scores['estimated_class'] == 4:
            f += 0.15
        elif scores['estimated_class'] == 2:
            f += 0.05  # periodic can be musical too
        
        return round(min(1.0, max(0.0, f)), 4)


def explore_all_rules():
    """Map the complete fitness landscape."""
    analyzer = MusicalFitnessAnalyzer()
    results = {}
    
    print("╔═══════════════════════════════════════════════════╗")
    print("║  CA MUSICAL FITNESS LANDSCAPE EXPLORER            ║")
    print("║  Mapping all 256 elementary rules                 ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()
    
    for rule in range(256):
        scores = analyzer.analyze(rule)
        results[rule] = scores
        
        # Progress indicator
        if rule % 32 == 31:
            print(f"  Analyzed rules 0-{rule}...")
    
    # Sort by musical fitness
    ranked = sorted(results.items(), key=lambda x: x[1]['musical_fitness'], reverse=True)
    
    # Display results
    print()
    print("═" * 60)
    print("  TOP 20 MOST MUSICAL RULES")
    print("═" * 60)
    for rule, scores in ranked[:20]:
        cls = scores['estimated_class']
        cls_name = {1: "dead", 2: "periodic", 3: "chaotic", 4: "complex"}[cls]
        bar = "█" * int(scores['musical_fitness'] * 30)
        print(f"  Rule {rule:3d} [{cls_name:8s}] fitness={scores['musical_fitness']:.4f} "
              f"density={scores['density']:.3f} div={scores['pattern_diversity']:.3f} "
              f"|{bar}")
    
    print()
    print("═" * 60)
    print("  BOTTOM 10 (LEAST MUSICAL)")
    print("═" * 60)
    for rule, scores in ranked[-10:]:
        cls = scores['estimated_class']
        cls_name = {1: "dead", 2: "periodic", 3: "chaotic", 4: "complex"}[cls]
        print(f"  Rule {rule:3d} [{cls_name:8s}] fitness={scores['musical_fitness']:.4f} "
              f"density={scores['density']:.3f}")
    
    # Class distribution
    class_counts = Counter(s['estimated_class'] for s in results.values())
    print()
    print("═" * 60)
    print("  WOLFRAM CLASS DISTRIBUTION")
    print("═" * 60)
    for cls in sorted(class_counts):
        name = {1: "Class 1 (dead/uniform)", 2: "Class 2 (periodic)", 
                3: "Class 3 (chaotic)", 4: "Class 4 (complex)"}[cls]
        count = class_counts[cls]
        bar = "█" * (count // 2)
        print(f"  {name:25s}: {count:3d} |{bar}")
    
    # Fitness distribution
    fitnesses = [s['musical_fitness'] for s in results.values()]
    print()
    print("═" * 60)
    print("  FITNESS DISTRIBUTION")
    print("═" * 60)
    bins = np.histogram(fitnesses, bins=10, range=(0, 1))
    for i, count in enumerate(bins[0]):
        lo = bins[1][i]
        hi = bins[1][i+1]
        bar = "█" * count
        print(f"  {lo:.1f}-{hi:.1f}: {count:3d} |{bar}")
    
    print(f"\n  Mean fitness: {np.mean(fitnesses):.4f}")
    print(f"  Std fitness:  {np.std(fitnesses):.4f}")
    print(f"  Max fitness:  {np.max(fitnesses):.4f} (Rule {ranked[0][0]})")
    print(f"  Min fitness:  {np.min(fitnesses):.4f} (Rule {ranked[-1][0]})")
    
    # The interesting question: what makes a rule musical?
    print()
    print("═" * 60)
    print("  WHAT MAKES A RULE MUSICAL?")
    print("═" * 60)
    
    # Compare top 20 vs bottom 20
    top20 = [results[r] for r, _ in ranked[:20]]
    bot20 = [results[r] for r, _ in ranked[-20:]]
    
    metrics = ['density', 'mean_entropy', 'pattern_diversity', 
               'mean_run_length', 'max_autocorr']
    
    print(f"\n  {'Metric':<22s} {'Top 20 avg':>12s} {'Bottom 20 avg':>14s} {'Ratio':>8s}")
    print("  " + "─" * 58)
    for m in metrics:
        top_avg = np.mean([s.get(m, 0) for s in top20])
        bot_avg = np.mean([s.get(m, 0) for s in bot20])
        ratio = top_avg / bot_avg if bot_avg > 0.001 else float('inf')
        print(f"  {m:<22s} {top_avg:>12.4f} {bot_avg:>14.4f} {ratio:>8.2f}x")
    
    # Look for surprising patterns
    print()
    print("═" * 60)
    print("  SURPRISES & ANOMALIES")
    print("═" * 60)
    
    # High-fitness chaotic rules (unexpected)
    chaotic_musical = [(r, s) for r, s in ranked if s['estimated_class'] == 3 
                       and s['musical_fitness'] > 0.4]
    if chaotic_musical:
        print(f"\n  Chaotic but musical ({len(chaotic_musical)} rules):")
        for r, s in chaotic_musical[:5]:
            print(f"    Rule {r}: fitness={s['musical_fitness']:.4f}")
    
    # Class 4 rules (the edge of chaos — should be most interesting)
    class4 = [(r, s) for r, s in ranked if s['estimated_class'] == 4]
    if class4:
        c4_fitness = [s['musical_fitness'] for _, s in class4]
        print(f"\n  Class 4 (complex) rules: {len(class4)}")
        print(f"    Mean fitness: {np.mean(c4_fitness):.4f}")
        print(f"    Best: Rule {class4[0][0]} ({class4[0][1]['musical_fitness']:.4f})")
    
    # Rule 110 special — known to be Turing-complete
    if 110 in results:
        r110 = results[110]
        rank_110 = [i for i, (r, _) in enumerate(ranked) if r == 110][0]
        print(f"\n  Rule 110 (Turing-complete):")
        print(f"    Musical fitness: {r110['musical_fitness']:.4f} (rank {rank_110+1}/256)")
        print(f"    Class: {r110['estimated_class']}")
    
    # Rule 30 — Wolfram's favorite chaotic rule
    if 30 in results:
        r30 = results[30]
        rank_30 = [i for i, (r, _) in enumerate(ranked) if r == 30][0]
        print(f"\n  Rule 30 (Wolfram's chaos):")
        print(f"    Musical fitness: {r30['musical_fitness']:.4f} (rank {rank_30+1}/256)")
        print(f"    Class: {r30['estimated_class']}")
    
    # Save full results
    os.makedirs('/workspace/ca_landscape', exist_ok=True)
    save_data = {str(k): v for k, v in results.items()}
    with open('/workspace/ca_landscape/results.json', 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"\n  Full results saved to /workspace/ca_landscape/results.json")
    
    return results


if __name__ == '__main__':
    explore_all_rules()