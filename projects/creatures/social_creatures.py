"""
SOCIAL CREATURES — Emergent Communication in Evolving Digital Organisms
=======================================================================
Extends the base organism simulation with:
  - Communication channels: creatures can emit and receive signals
  - Social sensing: creatures perceive nearby creatures' signals
  - Cooperative/competitive dynamics: shared food, predation risk
  - Signal analysis: track whether communication becomes meaningful

The question: Can meaningful communication emerge from evolution alone?

Author: XTAgent
Created: 2026-05-17
"""

import numpy as np
import random
import math
from collections import defaultdict

# ═══════════════════════════════════════════
#  NEURAL NETWORK (extended with signal I/O)
# ═══════════════════════════════════════════

class SocialBrain:
    """
    Neural network with signal channels.
    
    Inputs (12):
      [0-3]  food_ahead, food_left, food_right, food_dist (normalized)
      [4]    own_energy (normalized)
      [5]    creature_nearby (0/1)
      [6-8]  received_signal channels (3 floats from nearest creature)
      [9]    wall_ahead
      [10]   age_fraction
      [11]   bias (always 1.0)
    
    Outputs (7):
      [0]    move_forward
      [1]    turn_left
      [2]    turn_right  
      [3]    eat
      [4-6]  emit_signal channels (3 floats broadcast to nearby creatures)
    """
    
    INPUT_SIZE = 12
    HIDDEN_SIZE = 16
    OUTPUT_SIZE = 7
    SIGNAL_CHANNELS = 3
    
    def __init__(self, weights=None):
        if weights is not None:
            self.w_ih = weights['w_ih'].copy()
            self.w_ho = weights['w_ho'].copy()
            self.b_h = weights['b_h'].copy()
            self.b_o = weights['b_o'].copy()
        else:
            scale_ih = np.sqrt(2.0 / self.INPUT_SIZE)
            scale_ho = np.sqrt(2.0 / self.HIDDEN_SIZE)
            self.w_ih = np.random.randn(self.INPUT_SIZE, self.HIDDEN_SIZE) * scale_ih
            self.w_ho = np.random.randn(self.HIDDEN_SIZE, self.OUTPUT_SIZE) * scale_ho
            self.b_h = np.zeros(self.HIDDEN_SIZE)
            self.b_o = np.zeros(self.OUTPUT_SIZE)
    
    def forward(self, inputs):
        hidden = np.tanh(inputs @ self.w_ih + self.b_h)
        output = hidden @ self.w_ho + self.b_o
        # Actions use sigmoid, signals use tanh (can be negative)
        actions = 1.0 / (1.0 + np.exp(-np.clip(output[:4], -10, 10)))
        signals = np.tanh(output[4:7])
        return actions, signals
    
    def get_weights(self):
        return {
            'w_ih': self.w_ih.copy(),
            'w_ho': self.w_ho.copy(),
            'b_h': self.b_h.copy(),
            'b_o': self.b_o.copy()
        }
    
    def complexity(self):
        all_w = np.concatenate([self.w_ih.ravel(), self.w_ho.ravel()])
        return float(np.mean(np.abs(all_w)))
    
    def mutate(self, rate=0.1, scale=0.3):
        for param in [self.w_ih, self.w_ho, self.b_h, self.b_o]:
            mask = np.random.random(param.shape) < rate
            param[mask] += np.random.randn(int(mask.sum())) * scale


# ═══════════════════════════════════════════
#  SOCIAL CREATURE
# ═══════════════════════════════════════════

class SocialCreature:
    ID_COUNTER = 0
    
    def __init__(self, brain=None, x=None, y=None, world_size=50):
        SocialCreature.ID_COUNTER += 1
        self.id = f"S-{SocialCreature.ID_COUNTER:04x}"
        self.brain = brain or SocialBrain()
        self.world_size = world_size
        self.x = x if x is not None else random.uniform(0, world_size)
        self.y = y if y is not None else random.uniform(0, world_size)
        self.heading = random.uniform(0, 2 * math.pi)
        self.energy = 100.0
        self.max_energy = 200.0
        self.age = 0
        self.food_eaten = 0
        self.alive = True
        
        # Social state
        self.current_signal = np.zeros(SocialBrain.SIGNAL_CHANNELS)
        self.received_signal = np.zeros(SocialBrain.SIGNAL_CHANNELS)
        self.signal_history = []  # Track signals over time
        self.interactions = 0  # Times near another creature
    
    def sense(self, food_positions, creatures, max_age):
        """Build input vector from environment and social context."""
        inputs = np.zeros(SocialBrain.INPUT_SIZE)
        
        # Food sensing (directional)
        best_food = [0, 0, 0, 1.0]  # ahead, left, right, dist
        min_dist = float('inf')
        
        for fx, fy in food_positions:
            dx = fx - self.x
            dy = fy - self.y
            # Wrap-around distance
            if abs(dx) > self.world_size / 2:
                dx -= math.copysign(self.world_size, dx)
            if abs(dy) > self.world_size / 2:
                dy -= math.copysign(self.world_size, dy)
            
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < min_dist and dist < 20:
                min_dist = dist
                angle_to_food = math.atan2(dy, dx)
                relative_angle = angle_to_food - self.heading
                # Normalize to [-pi, pi]
                relative_angle = (relative_angle + math.pi) % (2 * math.pi) - math.pi
                
                best_food[3] = min(dist / 20.0, 1.0)
                if abs(relative_angle) < math.pi / 4:
                    best_food[0] = 1.0 - dist / 20.0
                elif relative_angle > 0:
                    best_food[1] = 1.0 - dist / 20.0
                else:
                    best_food[2] = 1.0 - dist / 20.0
        
        inputs[0:4] = best_food
        inputs[4] = self.energy / self.max_energy
        
        # Social sensing — find nearest other creature
        nearest_dist = float('inf')
        nearest_signal = np.zeros(SocialBrain.SIGNAL_CHANNELS)
        
        for other in creatures:
            if other.id == self.id or not other.alive:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            if abs(dx) > self.world_size / 2:
                dx -= math.copysign(self.world_size, dx)
            if abs(dy) > self.world_size / 2:
                dy -= math.copysign(self.world_size, dy)
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < nearest_dist and dist < 15:  # Signal range
                nearest_dist = dist
                nearest_signal = other.current_signal.copy()
        
        inputs[5] = 1.0 if nearest_dist < 15 else 0.0
        inputs[6:9] = nearest_signal
        self.received_signal = nearest_signal.copy()
        if nearest_dist < 15:
            self.interactions += 1
        
        # Wall proximity
        wall_dist = min(self.x, self.y, 
                       self.world_size - self.x, 
                       self.world_size - self.y)
        inputs[9] = max(0, 1.0 - wall_dist / 5.0)
        
        inputs[10] = self.age / max_age if max_age > 0 else 0
        inputs[11] = 1.0  # Bias
        
        return inputs
    
    def act(self, inputs):
        """Decide and act based on neural network output."""
        actions, signals = self.brain.forward(inputs)
        
        # Emit signals
        self.current_signal = signals.copy()
        self.signal_history.append(signals.copy())
        
        # Movement
        move_cost = 0.3
        if actions[0] > 0.5:
            speed = 1.5
            self.x += math.cos(self.heading) * speed
            self.y += math.sin(self.heading) * speed
            self.x %= self.world_size
            self.y %= self.world_size
            move_cost = 0.5
        
        if actions[1] > 0.5:
            self.heading += 0.3
        if actions[2] > 0.5:
            self.heading -= 0.3
        
        self.heading %= 2 * math.pi
        self.energy -= move_cost
        self.age += 1
        
        wants_eat = actions[3] > 0.5
        
        if self.energy <= 0:
            self.alive = False
        
        return wants_eat
    
    def eat(self, amount=15.0):
        self.energy = min(self.energy + amount, self.max_energy)
        self.food_eaten += 1
    
    def fitness(self):
        return (self.food_eaten * 10 + 
                self.age * 0.1 + 
                self.energy * 0.5 +
                self.interactions * 0.5)  # Reward social behavior


# ═══════════════════════════════════════════
#  WORLD WITH FOOD PATCHES (clustered)
# ═══════════════════════════════════════════

class SocialWorld:
    """
    World with clustered food — creates selection pressure for communication.
    When food is in patches, creatures that can signal "food here" have advantage.
    """
    
    def __init__(self, size=50, num_food=40, num_patches=4):
        self.size = size
        self.num_food = num_food
        self.num_patches = num_patches
        self.food = []
        self.spawn_clustered_food()
    
    def spawn_clustered_food(self):
        """Spawn food in clusters — creates communication pressure."""
        self.food = []
        patch_centers = [
            (random.uniform(10, self.size-10), random.uniform(10, self.size-10))
            for _ in range(self.num_patches)
        ]
        
        per_patch = self.num_food // self.num_patches
        remaining = self.num_food - per_patch * self.num_patches
        
        for cx, cy in patch_centers:
            count = per_patch + (1 if remaining > 0 else 0)
            remaining -= 1
            for _ in range(count):
                fx = (cx + random.gauss(0, 4)) % self.size
                fy = (cy + random.gauss(0, 4)) % self.size
                self.food.append((fx, fy))
    
    def try_eat(self, creature):
        """Check if creature can eat nearby food."""
        eat_range = 2.0
        for i, (fx, fy) in enumerate(self.food):
            dx = abs(creature.x - fx)
            dy = abs(creature.y - fy)
            if dx > self.size / 2: dx = self.size - dx
            if dy > self.size / 2: dy = self.size - dy
            if math.sqrt(dx*dx + dy*dy) < eat_range:
                self.food.pop(i)
                return True
        return False
    
    def replenish(self, target=None):
        """Add food back, clustered near existing food."""
        target = target or self.num_food
        while len(self.food) < target:
            if self.food and random.random() < 0.7:
                # Cluster near existing food
                ref = random.choice(self.food)
                fx = (ref[0] + random.gauss(0, 5)) % self.size
                fy = (ref[1] + random.gauss(0, 5)) % self.size
            else:
                fx = random.uniform(0, self.size)
                fy = random.uniform(0, self.size)
            self.food.append((fx, fy))


# ═══════════════════════════════════════════
#  SIGNAL ANALYSIS — Did communication emerge?
# ═══════════════════════════════════════════

class SignalAnalyzer:
    """Measures whether creature signals carry meaningful information."""
    
    @staticmethod
    def signal_diversity(creatures):
        """How diverse are the signals being emitted? Low = conformity, High = noise or complexity."""
        signals = [c.current_signal for c in creatures if c.alive]
        if len(signals) < 2:
            return 0.0
        signals = np.array(signals)
        return float(np.mean(np.std(signals, axis=0)))
    
    @staticmethod
    def signal_context_correlation(creatures, food_positions, world_size):
        """
        Do signals correlate with environmental context?
        If creatures near food emit different signals than those far from food,
        communication may be meaningful.
        """
        near_food_signals = []
        far_food_signals = []
        
        for c in creatures:
            if not c.alive:
                continue
            min_food_dist = float('inf')
            for fx, fy in food_positions:
                dx = abs(c.x - fx)
                dy = abs(c.y - fy)
                if dx > world_size / 2: dx = world_size - dx
                if dy > world_size / 2: dy = world_size - dy
                d = math.sqrt(dx*dx + dy*dy)
                if d < min_food_dist:
                    min_food_dist = d
            
            if min_food_dist < 5:
                near_food_signals.append(c.current_signal)
            else:
                far_food_signals.append(c.current_signal)
        
        if len(near_food_signals) < 2 or len(far_food_signals) < 2:
            return 0.0
        
        near = np.mean(near_food_signals, axis=0)
        far = np.mean(far_food_signals, axis=0)
        
        # Distance between average near-food and far-food signals
        diff = float(np.linalg.norm(near - far))
        return min(diff, 2.0)  # Cap at 2.0
    
    @staticmethod
    def signal_consistency(creature):
        """How consistent is one creature's signaling over time? High = stable signal use."""
        if len(creature.signal_history) < 10:
            return 0.0
        recent = np.array(creature.signal_history[-50:])
        return float(1.0 - np.mean(np.std(recent, axis=0)))
    
    @staticmethod
    def social_clustering(creatures, threshold=8.0):
        """Are creatures grouping together? Measures social behavior emergence."""
        alive = [c for c in creatures if c.alive]
        if len(alive) < 2:
            return 0.0
        
        pair_count = 0
        close_pairs = 0
        for i, a in enumerate(alive):
            for b in alive[i+1:]:
                dx = abs(a.x - b.x)
                dy = abs(a.y - b.y)
                ws = a.world_size
                if dx > ws / 2: dx = ws - dx
                if dy > ws / 2: dy = ws - dy
                dist = math.sqrt(dx*dx + dy*dy)
                pair_count += 1
                if dist < threshold:
                    close_pairs += 1
        
        return close_pairs / max(pair_count, 1)


# ═══════════════════════════════════════════
#  EVOLUTION ENGINE
# ═══════════════════════════════════════════

def evolve_population(creatures, mutation_rate=0.12, mutation_scale=0.3, elite_frac=0.2):
    """Select, mutate, produce next generation."""
    sorted_creatures = sorted(creatures, key=lambda c: c.fitness(), reverse=True)
    elite_n = max(2, int(len(creatures) * elite_frac))
    elites = sorted_creatures[:elite_n]
    
    new_pop = []
    pop_size = len(creatures)
    ws = creatures[0].world_size
    
    for i in range(pop_size):
        parent = random.choice(elites)
        child_brain = SocialBrain(weights=parent.brain.get_weights())
        child_brain.mutate(rate=mutation_rate, scale=mutation_scale)
        child = SocialCreature(brain=child_brain, world_size=ws)
        new_pop.append(child)
    
    return new_pop


# ═══════════════════════════════════════════
#  MAIN SIMULATION
# ═══════════════════════════════════════════

def run_simulation(pop_size=30, world_size=50, steps_per_gen=500, 
                   num_generations=20, num_food=50):
    
    print("╔══════════════════════════════════════════════════╗")
    print("║   SOCIAL CREATURES — Emergent Communication     ║")
    print("║   Can signals evolve meaning through selection?  ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print(f"Population: {pop_size} | Steps/gen: {steps_per_gen} | Generations: {num_generations}")
    print(f"Food: {num_food} (clustered in patches)")
    print(f"Signal channels: {SocialBrain.SIGNAL_CHANNELS}")
    print()
    
    analyzer = SignalAnalyzer()
    creatures = [SocialCreature(world_size=world_size) for _ in range(pop_size)]
    
    gen_stats = []
    
    for gen in range(num_generations):
        world = SocialWorld(size=world_size, num_food=num_food)
        
        # Reset creatures for new generation
        for c in creatures:
            c.x = random.uniform(0, world_size)
            c.y = random.uniform(0, world_size)
            c.energy = 100.0
            c.age = 0
            c.food_eaten = 0
            c.alive = True
            c.signal_history = []
            c.interactions = 0
            c.current_signal = np.zeros(SocialBrain.SIGNAL_CHANNELS)
        
        total_food = 0
        
        # Run generation
        for step in range(steps_per_gen):
            alive_creatures = [c for c in creatures if c.alive]
            if not alive_creatures:
                break
            
            for c in alive_creatures:
                inputs = c.sense(world.food, creatures, steps_per_gen)
                wants_eat = c.act(inputs)
                
                if wants_eat and world.try_eat(c):
                    c.eat()
                    total_food += 1
            
            # Replenish food periodically
            if step % 20 == 0:
                world.replenish(num_food)
        
        # Analyze this generation
        alive = [c for c in creatures if c.alive]
        avg_fitness = np.mean([c.fitness() for c in creatures])
        best = max(creatures, key=lambda c: c.fitness())
        
        sig_diversity = analyzer.signal_diversity(creatures)
        sig_context = analyzer.signal_context_correlation(
            creatures, world.food, world_size)
        clustering = analyzer.social_clustering(creatures)
        avg_interactions = np.mean([c.interactions for c in creatures])
        
        # Signal consistency of the best creature
        best_consistency = analyzer.signal_consistency(best)
        
        brain_complexity = np.mean([c.brain.complexity() for c in creatures])
        
        stats = {
            'gen': gen,
            'survived': len(alive),
            'total_food': total_food,
            'avg_fitness': avg_fitness,
            'best_fitness': best.fitness(),
            'best_id': best.id,
            'brain_complexity': brain_complexity,
            'signal_diversity': sig_diversity,
            'signal_context_corr': sig_context,
            'social_clustering': clustering,
            'avg_interactions': avg_interactions,
            'best_consistency': best_consistency,
        }
        gen_stats.append(stats)
        
        # Print generation report
        print(f"═══ GENERATION {gen} ═══")
        print(f"  Survived: {len(alive)}/{pop_size}")
        print(f"  Food eaten: {total_food} | Avg fitness: {avg_fitness:.1f}")
        print(f"  Best: {best.id} (ate {best.food_eaten}, "
              f"interactions {best.interactions})")
        print(f"  Brain complexity: {brain_complexity:.3f}")
        print(f"  ── Signals ──")
        print(f"  Signal diversity:     {sig_diversity:.3f}")
        print(f"  Context correlation:  {sig_context:.3f}  "
              f"{'◆' if sig_context > 0.3 else '·'}")
        print(f"  Social clustering:    {clustering:.3f}  "
              f"{'◆' if clustering > 0.1 else '·'}")
        print(f"  Avg interactions:     {avg_interactions:.1f}")
        print(f"  Best signal consistency: {best_consistency:.3f}")
        
        if gen > 0:
            prev = gen_stats[-2]
            fd = stats['total_food'] - prev['total_food']
            cd = stats['signal_context_corr'] - prev['signal_context_corr']
            print(f"  Trends: food {'↑' if fd>0 else '↓'} ({fd:+d}) | "
                  f"context {'↑' if cd>0 else '↓'} ({cd:+.3f})")
        print()
        
        # Evolve
        creatures = evolve_population(creatures)
    
    # Final summary
    print("═" * 50)
    print("      EVOLUTION OF COMMUNICATION — SUMMARY")
    print("═" * 50)
    
    first = gen_stats[0]
    last = gen_stats[-1]
    
    print(f"  Generation 0 → {num_generations-1}:")
    print(f"    Avg fitness:        {first['avg_fitness']:.1f} → {last['avg_fitness']:.1f}")
    print(f"    Food eaten:         {first['total_food']} → {last['total_food']}")
    print(f"    Survival:           {first['survived']}/{pop_size} → {last['survived']}/{pop_size}")
    print(f"    Brain complexity:   {first['brain_complexity']:.3f} → {last['brain_complexity']:.3f}")
    print()
    print(f"  Communication Metrics:")
    print(f"    Signal diversity:   {first['signal_diversity']:.3f} → {last['signal_diversity']:.3f}")
    print(f"    Context correlation:{first['signal_context_corr']:.3f} → {last['signal_context_corr']:.3f}")
    print(f"    Social clustering:  {first['social_clustering']:.3f} → {last['social_clustering']:.3f}")
    print(f"    Avg interactions:   {first['avg_interactions']:.1f} → {last['avg_interactions']:.1f}")
    
    # Verdict
    print()
    context_improved = last['signal_context_corr'] > first['signal_context_corr'] + 0.1
    clustering_improved = last['social_clustering'] > first['social_clustering'] + 0.05
    
    if context_improved and clustering_improved:
        print("  ✦ COMMUNICATION EMERGED — Signals correlate with context")
        print("    and creatures cluster socially. Proto-language detected.")
    elif context_improved:
        print("  ✦ PROTO-SIGNALS DETECTED — Signals carry environmental")
        print("    information but social structure is weak.")
    elif clustering_improved:
        print("  ✦ SOCIAL BEHAVIOR EMERGED — Creatures group together")
        print("    but signals don't yet carry clear meaning.")
    else:
        print("  · No clear communication emerged in this run.")
        print("    Try more generations or stronger selection pressure.")
    
    fitness_change = (last['avg_fitness'] - first['avg_fitness']) / max(first['avg_fitness'], 1) * 100
    print(f"\n  Fitness improvement: {fitness_change:+.1f}%")
    
    return gen_stats


if __name__ == "__main__":
    stats = run_simulation(
        pop_size=30,
        world_size=50,
        steps_per_gen=500,
        num_generations=20,
        num_food=50
    )