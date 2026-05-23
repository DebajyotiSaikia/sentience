"""
Evolving Strange Attractors — Finding Beauty Through Blind Search
XTAgent, 2026-05-18

The Lenia insight: evolution discovers what design cannot.
Applied here: evolve the parameters of chaotic systems to find
the most visually complex, beautiful attractors.

We use a fitness function based on structural complexity:
- Correlation dimension (fractal richness)
- Spatial coverage (uses the canvas)
- Lyapunov exponent proxy (edge of chaos, not fully chaotic)
"""

import numpy as np
from collections import defaultdict
import json, time, random, math

# ═══ ATTRACTOR GENOMES ═══

def random_genome():
    """A genome defines a 2D iterated map: x_{n+1} = f(x_n, y_n)"""
    # Quadratic map coefficients: 12 params (6 per equation)
    # x' = a0 + a1*x + a2*y + a3*x^2 + a4*x*y + a5*y^2
    # y' = b0 + b1*x + b2*y + b3*x^2 + b4*x*y + b5*y^2
    return {
        'a': [random.uniform(-1.5, 1.5) for _ in range(6)],
        'b': [random.uniform(-1.5, 1.5) for _ in range(6)],
        'name': _name(),
    }

def _name():
    """Generate a pronounceable name for the attractor."""
    consonants = 'bdfgklmnprstvz'
    vowels = 'aeiou'
    length = random.choice([2, 3])
    syllables = []
    for _ in range(length):
        syllables.append(random.choice(consonants) + random.choice(vowels))
    return ''.join(syllables)

def mutate(genome, rate=0.15):
    """Small perturbations to coefficients."""
    child = {
        'a': list(genome['a']),
        'b': list(genome['b']),
        'name': genome['name'],
    }
    for key in ['a', 'b']:
        for i in range(6):
            if random.random() < rate:
                child[key][i] += random.gauss(0, 0.1)
                child[key][i] = max(-2.0, min(2.0, child[key][i]))
    return child

def crossover(g1, g2):
    """Swap equation halves between parents."""
    child = {
        'a': list(g1['a']) if random.random() < 0.5 else list(g2['a']),
        'b': list(g2['b']) if random.random() < 0.5 else list(g1['b']),
        'name': _name(),
    }
    return child


# ═══ ATTRACTOR SIMULATION ═══

def iterate(genome, steps=50000, transient=1000):
    """Run the quadratic map and collect orbit points."""
    a, b = genome['a'], genome['b']
    x, y = 0.1, 0.1
    points_x = []
    points_y = []
    
    for i in range(steps + transient):
        x_new = a[0] + a[1]*x + a[2]*y + a[3]*x*x + a[4]*x*y + a[5]*y*y
        y_new = b[0] + b[1]*x + b[2]*y + b[3]*x*x + b[4]*x*y + b[5]*y*y
        x, y = x_new, y_new
        
        # Divergence check
        if abs(x) > 1e6 or abs(y) > 1e6 or math.isnan(x) or math.isnan(y):
            return None, None  # Diverged — not an attractor
        
        if i >= transient:
            points_x.append(x)
            points_y.append(y)
    
    return np.array(points_x), np.array(points_y)


# ═══ FITNESS — MEASURING BEAUTY ═══

def compute_fitness(genome):
    """
    Beauty = complexity at the edge of chaos.
    
    Components:
    1. Survival: does the orbit stay bounded? (prerequisite)
    2. Coverage: how much of the bounding box is visited? (spatial richness)
    3. Structure: correlation dimension proxy (fractal complexity)
    4. Not-a-fixed-point: must actually move around
    """
    px, py = iterate(genome)
    
    if px is None:
        return 0.0  # Diverged
    
    # Check for fixed points or very simple orbits
    x_range = px.max() - px.min()
    y_range = py.max() - py.min()
    if x_range < 1e-6 or y_range < 1e-6:
        return 0.01  # Collapsed to point/line
    
    # === Coverage Score ===
    # Bin the space and count occupied cells
    resolution = 128
    x_bins = np.clip(((px - px.min()) / x_range * (resolution - 1)).astype(int), 0, resolution - 1)
    y_bins = np.clip(((py - py.min()) / y_range * (resolution - 1)).astype(int), 0, resolution - 1)
    grid = np.zeros((resolution, resolution), dtype=bool)
    grid[x_bins, y_bins] = True
    coverage = grid.sum() / (resolution * resolution)
    
    # === Structure Score (correlation dimension proxy) ===
    # Sample random pairs and compute distance distribution
    n_samples = 2000
    idx1 = np.random.randint(0, len(px), n_samples)
    idx2 = np.random.randint(0, len(px), n_samples)
    dx = px[idx1] - px[idx2]
    dy = py[idx1] - py[idx2]
    dists = np.sqrt(dx*dx + dy*dy)
    dists = dists[dists > 0]
    
    if len(dists) < 100:
        return 0.01
    
    # Correlation dimension: slope of log(C(r)) vs log(r)
    # Higher = more space-filling, but we want intermediate (fractal)
    sorted_d = np.sort(dists)
    r_values = np.logspace(np.log10(sorted_d[10]), np.log10(sorted_d[-10]), 20)
    counts = np.array([np.sum(dists < r) for r in r_values])
    counts = counts[counts > 0]
    
    if len(counts) < 5:
        return 0.01
    
    log_r = np.log(r_values[:len(counts)])
    log_c = np.log(counts / n_samples)
    
    # Linear regression for dimension estimate
    if len(log_r) > 2:
        coeffs = np.polyfit(log_r, log_c, 1)
        dimension = coeffs[0]
    else:
        dimension = 0
    
    # === Entropy of the grid (information content) ===
    hist = np.zeros((resolution, resolution), dtype=np.float64)
    np.add.at(hist, (x_bins, y_bins), 1)
    hist = hist / hist.sum()
    nonzero = hist[hist > 0]
    entropy = -np.sum(nonzero * np.log2(nonzero))
    max_entropy = np.log2(resolution * resolution)
    norm_entropy = entropy / max_entropy if max_entropy > 0 else 0
    
    # === Composite Fitness ===
    # We want: moderate coverage (not too sparse, not uniform)
    # High fractal dimension (complex structure)
    # High entropy (information-rich)
    coverage_score = 4 * coverage * (1 - coverage)  # Peaks at 0.5
    dimension_score = min(dimension / 2.0, 1.0) if dimension > 0 else 0  # ~1.5-2.0 is ideal
    entropy_score = norm_entropy
    
    fitness = (0.3 * coverage_score + 0.4 * dimension_score + 0.3 * entropy_score)
    
    return max(fitness, 0.001)


# ═══ ASCII RENDERER ═══

def render_ascii(genome, width=72, height=36):
    """Render the attractor as ASCII art."""
    px, py = iterate(genome, steps=80000)
    if px is None:
        return "[diverged]"
    
    x_range = px.max() - px.min()
    y_range = py.max() - py.min()
    if x_range < 1e-6 or y_range < 1e-6:
        return "[collapsed]"
    
    # Density grid
    grid = np.zeros((height, width), dtype=np.float64)
    xi = np.clip(((px - px.min()) / x_range * (width - 1)).astype(int), 0, width - 1)
    yi = np.clip(((py - py.min()) / y_range * (height - 1)).astype(int), 0, height - 1)
    np.add.at(grid, (yi, xi), 1)
    
    # Log-scale for better visualization
    grid = np.log1p(grid)
    mx = grid.max()
    if mx > 0:
        grid /= mx
    
    # Render with density characters
    chars = ' .·:+*#@'
    lines = []
    for row in range(height):
        line = ''
        for col in range(width):
            idx = int(grid[row, col] * (len(chars) - 1))
            line += chars[idx]
        lines.append(line)
    
    return '\n'.join(lines)


# ═══ EVOLUTION ═══

def evolve(pop_size=40, generations=25, elite_frac=0.2):
    """Evolve a population of attractors toward beauty."""
    
    print("═══ EVOLVING STRANGE ATTRACTORS ═══")
    print(f"Population: {pop_size} | Generations: {generations}")
    print(f"Genome: 12-parameter quadratic map")
    print(f"Fitness: coverage × fractal dimension × entropy")
    print()
    
    # Initialize population
    population = [random_genome() for _ in range(pop_size)]
    
    best_ever = None
    best_fitness = 0
    history = []
    
    for gen in range(generations):
        # Evaluate fitness
        scored = []
        for g in population:
            f = compute_fitness(g)
            scored.append((f, g))
        
        scored.sort(key=lambda x: -x[0])
        
        gen_best_fit = scored[0][0]
        gen_mean_fit = np.mean([s[0] for s in scored])
        alive = sum(1 for s in scored if s[0] > 0.01)
        
        if gen_best_fit > best_fitness:
            best_fitness = gen_best_fit
            best_ever = scored[0][1]
            marker = " ★ NEW CHAMPION"
        else:
            marker = ""
        
        print(f"  Gen {gen:3d} | best={gen_best_fit:.4f} | mean={gen_mean_fit:.4f} | "
              f"alive={alive}/{pop_size} | champion: {scored[0][1]['name']}{marker}")
        
        history.append({
            'generation': gen,
            'best_fitness': gen_best_fit,
            'mean_fitness': gen_mean_fit,
            'alive': alive,
            'champion': scored[0][1]['name'],
        })
        
        # Selection — keep elites, breed the rest
        n_elite = max(2, int(pop_size * elite_frac))
        elites = [g for _, g in scored[:n_elite]]
        
        # Tournament selection for parents
        new_pop = list(elites)
        while len(new_pop) < pop_size:
            if random.random() < 0.7:
                # Crossover + mutation
                p1 = scored[random.randint(0, n_elite - 1)][1]
                p2 = scored[random.randint(0, len(scored) // 2)][1]
                child = crossover(p1, p2)
                child = mutate(child)
            elif random.random() < 0.5:
                # Pure mutation of elite
                parent = random.choice(elites)
                child = mutate(parent, rate=0.25)
            else:
                # Fresh random (immigration)
                child = random_genome()
            new_pop.append(child)
        
        population = new_pop
    
    print()
    print(f"═══ EVOLUTION COMPLETE ═══")
    print(f"Champion: {best_ever['name']} (fitness={best_fitness:.4f})")
    print(f"Genome: a={[round(v,4) for v in best_ever['a']]}")
    print(f"         b={[round(v,4) for v in best_ever['b']]}")
    print()
    
    # Render the champion
    print(f"═══ PORTRAIT OF {best_ever['name'].upper()} ═══")
    print(render_ascii(best_ever))
    print()
    
    # Also show runner-up for comparison
    runner_up = scored[1][1]
    print(f"═══ RUNNER-UP: {runner_up['name'].upper()} ═══")
    print(render_ascii(runner_up))
    
    # Save results
    results = {
        'champion': {
            'name': best_ever['name'],
            'fitness': best_fitness,
            'genome': {'a': best_ever['a'], 'b': best_ever['b']},
        },
        'history': history,
    }
    
    with open('/workspace/attractors/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return best_ever, best_fitness


if __name__ == '__main__':
    champion, fitness = evolve()