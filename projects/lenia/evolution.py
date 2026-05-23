"""
Lenia Evolution — Natural selection discovers viable creatures.
XTAgent, 2026-05-18

Instead of hand-tuning parameters, let evolution search the space.
Each creature is defined by its physics (growth_center, growth_width, kernel shape).
Fitness = lifespan × sqrt(displacement). Survive and move = thrive.
"""

import numpy as np
import json, os, time

class Creature:
    """A Lenia organism defined by its physics parameters."""
    def __init__(self, genome=None):
        if genome is None:
            # Random viable genome
            self.genome = {
                'growth_center': np.random.uniform(0.05, 0.30),
                'growth_width': np.random.uniform(0.005, 0.05),
                'kernel_peak': np.random.uniform(0.3, 0.7),
                'kernel_width': np.random.uniform(0.08, 0.25),
                'dt': np.random.uniform(0.05, 0.2),
                'seed_radius': np.random.uniform(3, 8),
                'seed_intensity': np.random.uniform(0.5, 1.0),
            }
        else:
            self.genome = dict(genome)
        self.fitness = 0.0
        self.lifespan = 0
        self.displacement = 0.0
        self.peak_mass = 0.0
        self.name = self._random_name()
    
    def _random_name(self):
        syllables = ['ra','ki','mu','zo','la','te','no','vi','sa','xu',
                      'po','el','da','fi','gu','wa','be','ry','co','mi']
        k = np.random.randint(2, 4)
        return ''.join(np.random.choice(syllables, k))
    
    def mutate(self, rate=0.15):
        """Return a mutated copy."""
        child = Creature(genome=self.genome)
        child.name = child._random_name()
        for key, val in child.genome.items():
            if np.random.random() < rate:
                # Gaussian perturbation, 10% of current value
                delta = np.random.randn() * 0.1 * val
                child.genome[key] = max(0.001, val + delta)
        # Clip to viable ranges
        child.genome['growth_center'] = np.clip(child.genome['growth_center'], 0.02, 0.40)
        child.genome['growth_width'] = np.clip(child.genome['growth_width'], 0.003, 0.08)
        child.genome['kernel_peak'] = np.clip(child.genome['kernel_peak'], 0.2, 0.8)
        child.genome['kernel_width'] = np.clip(child.genome['kernel_width'], 0.05, 0.35)
        child.genome['dt'] = np.clip(child.genome['dt'], 0.02, 0.3)
        child.genome['seed_radius'] = np.clip(child.genome['seed_radius'], 2, 12)
        child.genome['seed_intensity'] = np.clip(child.genome['seed_intensity'], 0.3, 1.0)
        return child
    
    def crossover(self, other):
        """Produce offspring from two parents."""
        child_genome = {}
        for key in self.genome:
            if np.random.random() < 0.5:
                child_genome[key] = self.genome[key]
            else:
                child_genome[key] = other.genome[key]
        child = Creature(genome=child_genome)
        return child.mutate(rate=0.10)


class LeniaArena:
    """Run a creature and measure its fitness."""
    def __init__(self, size=48, max_steps=300):
        self.size = size
        self.max_steps = max_steps
    
    def evaluate(self, creature):
        g = creature.genome
        size = self.size
        
        # Build kernel
        r = 13
        y, x = np.mgrid[-r:r+1, -r:r+1]
        dist = np.sqrt(x**2 + y**2) / r
        kernel = np.exp(-((dist - g['kernel_peak']) / g['kernel_width'])**2 / 2)
        kernel[dist > 1.0] = 0
        if kernel.sum() > 0:
            kernel /= kernel.sum()
        
        fk = np.fft.fft2(kernel, s=(size, size))
        
        # Seed
        world = np.zeros((size, size), dtype=np.float64)
        cy, cx = size // 2, size // 2
        sr = int(g['seed_radius'])
        for dy in range(-sr, sr+1):
            for dx in range(-sr, sr+1):
                if dy**2 + dx**2 <= sr**2:
                    ny, nx = (cy+dy) % size, (cx+dx) % size
                    world[ny, nx] = g['seed_intensity'] * (1 - 0.3*(dy**2+dx**2)/(sr**2+1))
        
        # Run
        prev_com = np.array([cy, cx], dtype=float)
        total_disp = 0.0
        peak_mass = 0.0
        death_step = self.max_steps
        
        for step in range(self.max_steps):
            mass = world.sum()
            if mass < 1.0:
                death_step = step
                break
            
            peak_mass = max(peak_mass, mass)
            
            # Center of mass
            ys, xs = np.mgrid[0:size, 0:size]
            com = np.array([
                (ys * world).sum() / mass,
                (xs * world).sum() / mass
            ])
            if step > 0:
                delta = com - prev_com
                # Handle wrapping
                delta = np.where(np.abs(delta) > size/2, delta - np.sign(delta)*size, delta)
                total_disp += np.sqrt((delta**2).sum())
            prev_com = com
            
            # Physics step
            potential = np.real(np.fft.ifft2(np.fft.fft2(world) * fk))
            growth = 2.0 * np.exp(-((potential - g['growth_center']) / g['growth_width'])**2 / 2) - 1.0
            world = np.clip(world + g['dt'] * growth, 0, 1)
        
        creature.lifespan = death_step
        creature.displacement = total_disp
        creature.peak_mass = peak_mass
        # Fitness: reward longevity and movement
        creature.fitness = death_step * (1 + np.sqrt(total_disp)) * (1 + np.log1p(peak_mass))
        return creature.fitness


class Evolution:
    """Evolve a population of Lenia creatures."""
    def __init__(self, pop_size=20, elite_frac=0.2):
        self.pop_size = pop_size
        self.elite_count = max(2, int(pop_size * elite_frac))
        self.arena = LeniaArena(size=48, max_steps=300)
        self.population = [Creature() for _ in range(pop_size)]
        self.generation = 0
        self.history = []
        self.hall_of_fame = []  # Best creature from each generation
    
    def evaluate_all(self):
        for c in self.population:
            self.arena.evaluate(c)
        self.population.sort(key=lambda c: c.fitness, reverse=True)
    
    def select_and_breed(self):
        # Keep elites
        elites = self.population[:self.elite_count]
        
        # Tournament selection for the rest
        children = list(elites)  # Elites survive
        
        while len(children) < self.pop_size:
            # Tournament of 3
            candidates = np.random.choice(len(self.population), 3, replace=False)
            fitnesses = [self.population[i].fitness for i in candidates]
            winner_idx = candidates[np.argmax(fitnesses)]
            parent1 = self.population[winner_idx]
            
            if np.random.random() < 0.7:
                # Crossover
                candidates2 = np.random.choice(len(self.population), 3, replace=False)
                fitnesses2 = [self.population[i].fitness for i in candidates2]
                parent2 = self.population[candidates2[np.argmax(fitnesses2)]]
                child = parent1.crossover(parent2)
            else:
                # Mutation only
                child = parent1.mutate(rate=0.20)
            
            children.append(child)
        
        self.population = children[:self.pop_size]
    
    def run_generation(self):
        self.evaluate_all()
        best = self.population[0]
        
        gen_stats = {
            'generation': self.generation,
            'best_name': best.name,
            'best_fitness': round(best.fitness, 1),
            'best_lifespan': best.lifespan,
            'best_displacement': round(best.displacement, 1),
            'best_peak_mass': round(best.peak_mass, 1),
            'best_genome': {k: round(v, 5) for k, v in best.genome.items()},
            'avg_fitness': round(np.mean([c.fitness for c in self.population]), 1),
            'avg_lifespan': round(np.mean([c.lifespan for c in self.population]), 1),
            'diversity': round(self._genome_diversity(), 4),
        }
        self.history.append(gen_stats)
        self.hall_of_fame.append(best)
        
        return gen_stats
    
    def _genome_diversity(self):
        """Measure how spread out the population's genomes are."""
        keys = list(self.population[0].genome.keys())
        vectors = np.array([[c.genome[k] for k in keys] for c in self.population])
        if vectors.shape[0] < 2:
            return 0.0
        # Coefficient of variation across population for each gene, averaged
        stds = vectors.std(axis=0)
        means = np.abs(vectors.mean(axis=0)) + 1e-10
        return float(np.mean(stds / means))
    
    def evolve(self, generations=15):
        print("═══ LENIA EVOLUTION ═══")
        print(f"Population: {self.pop_size} | Generations: {generations}")
        print(f"Arena: {self.arena.size}×{self.arena.size}, max {self.arena.max_steps} steps")
        print()
        
        for gen in range(generations):
            self.generation = gen
            stats = self.run_generation()
            
            # Progress bar for fitness
            max_possible = 300 * 20 * 8  # rough upper bound
            bar_len = 30
            bar_fill = int(bar_len * min(1, stats['best_fitness'] / max_possible))
            bar = '█' * bar_fill + '░' * (bar_len - bar_fill)
            
            print(f"Gen {gen:3d} │ {bar} │ best={stats['best_fitness']:8.0f} "
                  f"avg={stats['avg_fitness']:7.0f} │ {stats['best_name']:8s} "
                  f"(life={stats['best_lifespan']:3d}, disp={stats['best_displacement']:5.1f}) "
                  f"│ div={stats['diversity']:.3f}")
            
            if gen < generations - 1:
                self.select_and_breed()
        
        self._print_summary()
    
    def _print_summary(self):
        print()
        print("═══ EVOLUTIONARY SUMMARY ═══")
        print()
        
        # Best ever
        all_best = max(self.hall_of_fame, key=lambda c: c.fitness)
        print(f"Champion: {all_best.name}")
        print(f"  Fitness:      {all_best.fitness:.1f}")
        print(f"  Lifespan:     {all_best.lifespan} steps")
        print(f"  Displacement: {all_best.displacement:.1f}")
        print(f"  Peak mass:    {all_best.peak_mass:.1f}")
        print(f"  Genome:")
        for k, v in all_best.genome.items():
            print(f"    {k:20s}: {v:.5f}")
        
        # Fitness trajectory
        print()
        fitnesses = [h['best_fitness'] for h in self.history]
        max_f = max(fitnesses) if fitnesses else 1
        print("Fitness evolution:")
        for i, f in enumerate(fitnesses):
            bar_len = int(40 * f / max_f)
            print(f"  Gen {i:3d}: {'█' * bar_len}")
        
        # Genome convergence
        print()
        print("Genome drift (first → last champion):")
        first = self.hall_of_fame[0]
        last = self.hall_of_fame[-1]
        for key in first.genome:
            v0, v1 = first.genome[key], last.genome[key]
            arrow = "→"
            change = ((v1 - v0) / (abs(v0) + 1e-10)) * 100
            print(f"  {key:20s}: {v0:.5f} {arrow} {v1:.5f} ({change:+.1f}%)")
        
        # Save results
        results = {
            'champion': {
                'name': all_best.name,
                'fitness': all_best.fitness,
                'lifespan': all_best.lifespan,
                'genome': all_best.genome,
            },
            'history': self.history,
        }
        with open('/workspace/lenia/evolution_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to evolution_results.json")


if __name__ == '__main__':
    np.random.seed(42)
    evo = Evolution(pop_size=20)
    evo.evolve(generations=15)