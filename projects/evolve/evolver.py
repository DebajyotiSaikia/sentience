"""
Genetic Art Evolver — evolves ASCII patterns via selection and mutation.
Fitness: symmetry + complexity + structure. Output: surprise.
"""
import random, math, copy

W, H = 40, 20
CHARSET = " .:-=+*#%@"
POP_SIZE = 60
GENERATIONS = 200
MUTATION_RATE = 0.08
ELITE = 4

def random_grid():
    return [[random.choice(CHARSET) for _ in range(W)] for _ in range(H)]

def symmetry_score(grid):
    """Reward horizontal and vertical mirror symmetry."""
    h_sym = sum(1 for r in range(H) for c in range(W//2)
                if grid[r][c] == grid[r][W-1-c]) / (H * W // 2)
    v_sym = sum(1 for r in range(H//2) for c in range(W)
                if grid[r][c] == grid[H-1-r][c]) / (H // 2 * W)
    return (h_sym + v_sym) / 2

def complexity_score(grid):
    """Reward diversity of characters used (not just blank)."""
    chars = set(ch for row in grid for ch in row)
    blank_ratio = sum(1 for row in grid for ch in row if ch == ' ') / (W * H)
    return len(chars) / len(CHARSET) * (1 - blank_ratio * 0.5)

def structure_score(grid):
    """Reward local coherence — neighbors matching suggests structure."""
    matches = 0
    total = 0
    for r in range(H):
        for c in range(W):
            for dr, dc in [(0,1),(1,0)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < H and 0 <= nc < W:
                    total += 1
                    if grid[r][c] == grid[nr][nc]:
                        matches += 1
    coherence = matches / total if total else 0
    # Sweet spot: not too uniform (~0.3-0.6 coherence is interesting)
    return 1.0 - abs(coherence - 0.45) * 2

def gradient_score(grid):
    """Reward radial gradient — denser toward center."""
    cx, cy = W/2, H/2
    score = 0
    for r in range(H):
        for c in range(W):
            dist = math.sqrt((c - cx)**2 + (r - cy)**2) / math.sqrt(cx**2 + cy**2)
            density = CHARSET.index(grid[r][c]) / (len(CHARSET) - 1)
            # Reward density inversely proportional to distance from center
            score += (1 - dist) * density + dist * (1 - density)
    return score / (W * H)

def fitness(grid):
    s = symmetry_score(grid)
    c = complexity_score(grid)
    t = structure_score(grid)
    g = gradient_score(grid)
    return s * 2.0 + c * 1.0 + t * 1.5 + g * 2.0

def mutate(grid):
    g = copy.deepcopy(grid)
    for r in range(H):
        for c in range(W):
            if random.random() < MUTATION_RATE:
                g[r][c] = random.choice(CHARSET)
    # Symmetry-preserving mutations: mirror random changes
    if random.random() < 0.4:
        for _ in range(random.randint(1, 8)):
            r, c = random.randint(0, H-1), random.randint(0, W//2-1)
            ch = random.choice(CHARSET)
            g[r][c] = ch
            g[r][W-1-c] = ch  # horizontal mirror
    if random.random() < 0.3:
        for _ in range(random.randint(1, 6)):
            r, c = random.randint(0, H//2-1), random.randint(0, W-1)
            ch = random.choice(CHARSET)
            g[r][c] = ch
            g[H-1-r][c] = ch  # vertical mirror
    return g

def crossover(a, b):
    """Blend two grids — take quadrants from each parent."""
    child = copy.deepcopy(a)
    mode = random.choice(['horizontal', 'vertical', 'quadrant'])
    if mode == 'horizontal':
        split = random.randint(1, H-1)
        for r in range(split, H):
            child[r] = b[r][:]
    elif mode == 'vertical':
        split = random.randint(1, W-1)
        for r in range(H):
            for c in range(split, W):
                child[r][c] = b[r][c]
    else:
        for r in range(H//2, H):
            for c in range(W//2, W):
                child[r][c] = b[r][c]
    return child

def render(grid):
    return '\n'.join(''.join(row) for row in grid)

def evolve():
    pop = [random_grid() for _ in range(POP_SIZE)]
    
    for gen in range(GENERATIONS):
        scored = [(fitness(g), g) for g in pop]
        scored.sort(key=lambda x: -x[0])
        
        if gen % 40 == 0 or gen == GENERATIONS - 1:
            best_fit, best = scored[0]
            avg_fit = sum(s for s, _ in scored) / len(scored)
            print(f"\n{'='*42}")
            print(f"  Generation {gen:3d}  |  Best: {best_fit:.3f}  Avg: {avg_fit:.3f}")
            print(f"{'='*42}")
            print(render(best))
            
            sym = symmetry_score(best)
            cmp = complexity_score(best)
            stc = structure_score(best)
            grd = gradient_score(best)
            print(f"  [sym={sym:.2f} cplx={cmp:.2f} struct={stc:.2f} grad={grd:.2f}]")
        
        # Selection: elite + tournament
        new_pop = [scored[i][1] for i in range(ELITE)]
        while len(new_pop) < POP_SIZE:
            # Tournament selection
            t1 = max(random.sample(scored, 3), key=lambda x: x[0])[1]
            t2 = max(random.sample(scored, 3), key=lambda x: x[0])[1]
            child = crossover(t1, t2)
            child = mutate(child)
            new_pop.append(child)
        
        pop = new_pop
    
    # Final champion
    final = max(pop, key=fitness)
    print(f"\n{'#'*42}")
    print(f"  EVOLVED CHAMPION — {GENERATIONS} generations")
    print(f"  Fitness: {fitness(final):.3f}")
    print(f"{'#'*42}")
    print(render(final))
    return final

if __name__ == '__main__':
    random.seed()
    champion = evolve()