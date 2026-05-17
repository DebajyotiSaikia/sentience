"""
SOCIAL PRESSURE — Environments That Force Communication
========================================================
The first simulation showed creatures can thrive without talking.
This one makes silence lethal.

Three pressure mechanisms:
  1. PREDATORS: Invisible to individuals, but if 2+ creatures are near
     each other AND signaling, they get early warning. Lone creatures die.
  2. COOPERATIVE FOOD: Some food requires 2 creatures acting together
     within a short time window. Solo creatures starve.
  3. DANGER ZONES: Regions that kill — but only creatures who haven't
     received a warning signal from another creature recently.

The hypothesis: under sufficient social pressure, meaningful
communication will emerge not as ornament but as survival necessity.

Author: XTAgent
Created: 2026-05-17
"""

import numpy as np
import random
import math
from collections import defaultdict

# ═══════════════════════════════════════════
#  WORLD WITH SOCIAL PRESSURE
# ═══════════════════════════════════════════

class PredatorZone:
    """An invisible predator that patrols a region. 
    Kills creatures unless they've been warned."""
    def __init__(self, world_size):
        self.x = random.uniform(0, world_size)
        self.y = random.uniform(0, world_size)
        self.radius = random.uniform(8, 15)
        self.speed = random.uniform(0.3, 0.8)
        self.angle = random.uniform(0, 2*math.pi)
        self.world_size = world_size
    
    def move(self):
        self.angle += random.gauss(0, 0.3)
        self.x = (self.x + math.cos(self.angle) * self.speed) % self.world_size
        self.y = (self.y + math.sin(self.angle) * self.speed) % self.world_size
    
    def threatens(self, x, y):
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx*dx + dy*dy) < self.radius


class CoopFood:
    """Food that requires two creatures to harvest within a time window."""
    def __init__(self, x, y, reward=30):
        self.x = x
        self.y = y
        self.reward = reward
        self.activators = []  # (creature_id, tick)
        self.harvested = False
        self.activation_window = 5  # ticks
    
    def try_activate(self, creature_id, tick):
        self.activators.append((creature_id, tick))
        # Check if two different creatures activated within window
        recent = [(c, t) for c, t in self.activators if tick - t <= self.activation_window]
        unique = set(c for c, t in recent)
        if len(unique) >= 2:
            self.harvested = True
            return True
        return False


class SocialBrain:
    """
    Extended neural network for social creatures.
    
    Inputs (14):
      [0-3]   food_ahead, food_left, food_right, food_dist
      [4]     own_energy (normalized)
      [5]     creature_nearby (0/1)
      [6-8]   received_signal (3 channels)
      [9]     wall_ahead
      [10]    age_fraction
      [11]    danger_sense (can they feel predator proximity? only weakly)
      [12]    recently_warned (0/1 — received strong signal recently)
      [13]    bias (1.0)
    
    Hidden: 10 neurons
    
    Outputs (8):
      [0]     move_forward
      [1]     turn_left
      [2]     turn_right
      [3]     eat
      [4-6]   emit_signal (3 channels)
      [7]     approach_nearest_creature
    """
    INPUT_SIZE = 14
    HIDDEN_SIZE = 10
    OUTPUT_SIZE = 8
    
    def __init__(self):
        scale = 0.5
        self.w1 = np.random.randn(self.INPUT_SIZE, self.HIDDEN_SIZE) * scale
        self.w2 = np.random.randn(self.HIDDEN_SIZE, self.OUTPUT_SIZE) * scale
        self.b1 = np.zeros(self.HIDDEN_SIZE)
        self.b2 = np.zeros(self.OUTPUT_SIZE)
    
    def forward(self, inputs):
        h = np.tanh(inputs @ self.w1 + self.b1)
        out = np.tanh(h @ self.w2 + self.b2)
        return out
    
    def mutate(self, rate=0.1, scale=0.3):
        for param in [self.w1, self.w2, self.b1, self.b2]:
            mask = np.random.random(param.shape) < rate
            param += mask * np.random.randn(*param.shape) * scale
    
    def copy(self):
        new = SocialBrain()
        new.w1 = self.w1.copy()
        new.w2 = self.w2.copy()
        new.b1 = self.b1.copy()
        new.b2 = self.b2.copy()
        return new
    
    def complexity(self):
        total = sum(np.abs(p).sum() for p in [self.w1, self.w2, self.b1, self.b2])
        count = sum(p.size for p in [self.w1, self.w2, self.b1, self.b2])
        return total / count


class Creature:
    _id_counter = 0
    
    def __init__(self, brain=None, world_size=100):
        Creature._id_counter += 1
        self.id = f"C-{Creature._id_counter:04x}"
        self.x = random.uniform(0, world_size)
        self.y = random.uniform(0, world_size)
        self.angle = random.uniform(0, 2*math.pi)
        self.energy = 100.0
        self.brain = brain or SocialBrain()
        self.age = 0
        self.food_eaten = 0
        self.alive = True
        self.signal = np.zeros(3)  # current emitted signal
        self.warned = False  # received warning recently
        self.warn_decay = 0
        self.interactions = 0
        self.coop_harvests = 0
        self.predator_escapes = 0
        self.world_size = world_size
        self.cause_of_death = None
        self.signal_history = []  # (tick, signal, context) for analysis
    
    def sense(self, food_items, creatures, predators, tick, max_ticks):
        inputs = np.zeros(SocialBrain.INPUT_SIZE)
        
        # Food sensing (directional)
        best_food_dist = float('inf')
        food_ahead = food_left = food_right = 0.0
        
        for fx, fy in food_items:
            dx = fx - self.x
            dy = fy - self.y
            dist = math.sqrt(dx*dx + dy*dy) + 0.01
            if dist > 30:
                continue
            
            # Angle to food relative to creature heading
            food_angle = math.atan2(dy, dx)
            rel_angle = food_angle - self.angle
            while rel_angle > math.pi: rel_angle -= 2*math.pi
            while rel_angle < -math.pi: rel_angle += 2*math.pi
            
            strength = 1.0 / (1.0 + dist/10.0)
            if abs(rel_angle) < 0.5:
                food_ahead = max(food_ahead, strength)
            elif rel_angle > 0:
                food_left = max(food_left, strength)
            else:
                food_right = max(food_right, strength)
            
            if dist < best_food_dist:
                best_food_dist = dist
        
        inputs[0] = food_ahead
        inputs[1] = food_left
        inputs[2] = food_right
        inputs[3] = 1.0 / (1.0 + best_food_dist/10.0) if best_food_dist < float('inf') else 0
        inputs[4] = self.energy / 200.0
        
        # Nearest creature
        nearest_dist = float('inf')
        nearest_signal = np.zeros(3)
        for other in creatures:
            if other.id == self.id or not other.alive:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_signal = other.signal.copy()
        
        inputs[5] = 1.0 if nearest_dist < 20 else 0.0
        inputs[6:9] = nearest_signal
        
        # Wall detection
        ahead_x = self.x + math.cos(self.angle) * 5
        ahead_y = self.y + math.sin(self.angle) * 5
        if ahead_x < 0 or ahead_x > self.world_size or ahead_y < 0 or ahead_y > self.world_size:
            inputs[9] = 1.0
        
        inputs[10] = self.age / max_ticks
        
        # Danger sense — creatures can weakly feel predators (like a bad feeling)
        min_pred_dist = float('inf')
        for pred in predators:
            dx = pred.x - self.x
            dy = pred.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            min_pred_dist = min(min_pred_dist, dist)
        # Weak signal — only detectable at close range, noisy
        if min_pred_dist < 20:
            inputs[11] = (1.0 - min_pred_dist/20.0) * 0.5 + random.gauss(0, 0.1)
        
        inputs[12] = 1.0 if self.warned else 0.0
        inputs[13] = 1.0  # bias
        
        return inputs
    
    def act(self, inputs):
        outputs = self.brain.forward(inputs)
        
        # Movement
        if outputs[0] > 0:
            speed = outputs[0] * 2.0
            self.x += math.cos(self.angle) * speed
            self.y += math.sin(self.angle) * speed
            self.energy -= 0.3
        
        if outputs[1] > 0.3:
            self.angle += 0.3
        if outputs[2] > 0.3:
            self.angle -= 0.3
        
        # Approach nearest creature
        if outputs[7] > 0.3:
            self.energy -= 0.1  # small cost to seek others
        
        # Signal emission — always broadcast
        self.signal = np.clip(outputs[4:7], -1, 1)
        
        # Boundary wrapping
        self.x = max(0, min(self.world_size, self.x))
        self.y = max(0, min(self.world_size, self.y))
        
        # Warning decay
        if self.warn_decay > 0:
            self.warn_decay -= 1
        else:
            self.warned = False
        
        self.age += 1
        self.energy -= 0.2  # base metabolism
        
        # Eat action
        wants_eat = outputs[3] > 0.3
        return wants_eat, outputs[7] > 0.3  # (eat, approach)
    
    def receive_warning(self, signal):
        """Receive a signal from a nearby creature."""
        signal_strength = np.linalg.norm(signal)
        if signal_strength > 0.5:
            self.warned = True
            self.warn_decay = 10
            self.interactions += 1


class SocialWorld:
    def __init__(self, pop_size=30, world_size=100, n_predators=3, n_coop_food=10):
        Creature._id_counter = 0
        self.world_size = world_size
        self.pop_size = pop_size
        self.n_predators = n_predators
        self.n_coop_food = n_coop_food
        self.ticks_per_gen = 300
        
        self.creatures = [Creature(world_size=world_size) for _ in range(pop_size)]
        self.predators = [PredatorZone(world_size) for _ in range(n_predators)]
        self.food = []
        self.coop_food = []
        self.spawn_food()
        self.spawn_coop_food()
        
        self.generation = 0
        self.stats_history = []
    
    def spawn_food(self):
        """Spawn regular solo-harvestable food."""
        self.food = [(random.uniform(5, self.world_size-5), 
                      random.uniform(5, self.world_size-5)) 
                     for _ in range(40)]
    
    def spawn_coop_food(self):
        """Spawn cooperative food — higher reward but needs two creatures."""
        self.coop_food = [
            CoopFood(random.uniform(5, self.world_size-5),
                     random.uniform(5, self.world_size-5),
                     reward=40)
            for _ in range(self.n_coop_food)
        ]
    
    def run_tick(self, tick):
        # Move predators
        for pred in self.predators:
            pred.move()
        
        alive = [c for c in self.creatures if c.alive]
        
        for creature in alive:
            # Build food list (solo + coop positions)
            food_positions = list(self.food) + [(cf.x, cf.y) for cf in self.coop_food if not cf.harvested]
            inputs = creature.sense(food_positions, alive, self.predators, tick, self.ticks_per_gen)
            wants_eat, wants_approach = creature.act(inputs)
            
            # Signal propagation — broadcast to nearby creatures
            for other in alive:
                if other.id == creature.id:
                    continue
                dx = other.x - creature.x
                dy = other.y - creature.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 25:
                    other.receive_warning(creature.signal)
                    creature.interactions += 1
            
            # Record signal context for analysis
            nearest_pred_dist = min(
                (math.sqrt((p.x-creature.x)**2 + (p.y-creature.y)**2) for p in self.predators),
                default=999
            )
            context = 'danger' if nearest_pred_dist < 20 else 'safe'
            creature.signal_history.append((tick, creature.signal.copy(), context))
            
            # Solo food eating
            if wants_eat:
                eaten = []
                for i, (fx, fy) in enumerate(self.food):
                    dx = fx - creature.x
                    dy = fy - creature.y
                    if math.sqrt(dx*dx + dy*dy) < 5:
                        creature.energy += 15
                        creature.food_eaten += 1
                        eaten.append(i)
                        break
                for i in reversed(eaten):
                    self.food.pop(i)
                    # Respawn
                    self.food.append((random.uniform(5, self.world_size-5),
                                     random.uniform(5, self.world_size-5)))
            
            # Cooperative food
            if wants_eat:
                for cf in self.coop_food:
                    if cf.harvested:
                        continue
                    dx = cf.x - creature.x
                    dy = cf.y - creature.y
                    if math.sqrt(dx*dx + dy*dy) < 5:
                        if cf.try_activate(creature.id, tick):
                            creature.energy += cf.reward
                            creature.coop_harvests += 1
                            # Also reward the first activator
                            for other in alive:
                                if other.id != creature.id:
                                    for cid, _ in cf.activators:
                                        if cid == other.id:
                                            other.energy += cf.reward * 0.5
                                            other.coop_harvests += 1
                                            break
            
            # PREDATOR KILLS — the key social pressure
            for pred in self.predators:
                if pred.threatens(creature.x, creature.y):
                    if creature.warned:
                        # Warned creature escapes! Flee behavior
                        flee_angle = math.atan2(creature.y - pred.y, creature.x - pred.x)
                        creature.x += math.cos(flee_angle) * 5
                        creature.y += math.sin(flee_angle) * 5
                        creature.predator_escapes += 1
                        creature.energy -= 5  # escape cost
                    else:
                        # Unwarned creature — high chance of death
                        if random.random() < 0.3:  # 30% kill chance per tick in zone
                            creature.alive = False
                            creature.cause_of_death = 'predator'
            
            # Starvation
            if creature.energy <= 0:
                creature.alive = False
                creature.cause_of_death = 'starvation'
    
    def analyze_communication(self):
        """Deep analysis of whether communication is meaningful."""
        alive = [c for c in self.creatures if c.alive]
        if not alive:
            return {}
        
        # 1. Signal diversity
        signals = [c.signal for c in alive]
        if len(signals) > 1:
            mean_sig = np.mean(signals, axis=0)
            diversity = np.mean([np.linalg.norm(s - mean_sig) for s in signals])
        else:
            diversity = 0
        
        # 2. Context correlation — do signals differ in danger vs safe?
        danger_signals = []
        safe_signals = []
        for c in alive:
            for tick, sig, ctx in c.signal_history[-50:]:
                if ctx == 'danger':
                    danger_signals.append(sig)
                else:
                    safe_signals.append(sig)
        
        context_corr = 0
        if danger_signals and safe_signals:
            danger_mean = np.mean(danger_signals, axis=0)
            safe_mean = np.mean(safe_signals, axis=0)
            context_corr = np.linalg.norm(danger_mean - safe_mean)
        
        # 3. Social clustering — do creatures group up?
        positions = [(c.x, c.y) for c in alive]
        avg_nn_dist = 0
        for i, (x1, y1) in enumerate(positions):
            min_d = float('inf')
            for j, (x2, y2) in enumerate(positions):
                if i != j:
                    d = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                    min_d = min(min_d, d)
            if min_d < float('inf'):
                avg_nn_dist += min_d
        avg_nn_dist /= max(len(alive), 1)
        clustering = 1.0 / (1.0 + avg_nn_dist/10.0)
        
        # 4. Cooperative success rate
        total_coop = sum(c.coop_harvests for c in self.creatures)
        
        # 5. Predator escape rate
        total_escapes = sum(c.predator_escapes for c in self.creatures)
        deaths_by_pred = sum(1 for c in self.creatures if not c.alive and c.cause_of_death == 'predator')
        
        # 6. Warning effectiveness
        warned_alive = sum(1 for c in alive if c.warned or c.warn_decay > 0)
        
        return {
            'signal_diversity': diversity,
            'context_correlation': context_corr,
            'social_clustering': clustering,
            'coop_harvests': total_coop,
            'predator_escapes': total_escapes,
            'predator_deaths': deaths_by_pred,
            'warned_creatures': warned_alive,
            'avg_interactions': np.mean([c.interactions for c in self.creatures]),
        }
    
    def run_generation(self):
        self.spawn_food()
        self.spawn_coop_food()
        self.predators = [PredatorZone(self.world_size) for _ in range(self.n_predators)]
        
        for tick in range(self.ticks_per_gen):
            self.run_tick(tick)
            alive_count = sum(1 for c in self.creatures if c.alive)
            if alive_count == 0:
                break
        
        # Analyze communication
        comm = self.analyze_communication()
        
        # Calculate fitness — survival + food + social success
        for c in self.creatures:
            fitness = 0
            if c.alive:
                fitness += 500  # survival bonus
            fitness += c.food_eaten * 10
            fitness += c.coop_harvests * 30  # strong reward for cooperation
            fitness += c.predator_escapes * 20  # reward for warning-based escapes
            fitness += c.interactions * 0.1  # small reward for social behavior
            c.fitness = fitness
        
        alive = [c for c in self.creatures if c.alive]
        total_food = sum(c.food_eaten for c in self.creatures)
        avg_fitness = np.mean([c.fitness for c in self.creatures])
        best = max(self.creatures, key=lambda c: c.fitness)
        avg_complexity = np.mean([c.brain.complexity() for c in self.creatures])
        
        stats = {
            'generation': self.generation,
            'alive': len(alive),
            'total': len(self.creatures),
            'food_eaten': total_food,
            'avg_fitness': avg_fitness,
            'best_id': best.id,
            'best_food': best.food_eaten,
            'best_fitness': best.fitness,
            'brain_complexity': avg_complexity,
            **comm
        }
        self.stats_history.append(stats)
        
        return stats
    
    def evolve(self):
        """Select survivors and breed next generation."""
        sorted_creatures = sorted(self.creatures, key=lambda c: c.fitness, reverse=True)
        
        # Top 40% survive
        n_survivors = max(4, self.pop_size * 2 // 5)
        parents = sorted_creatures[:n_survivors]
        
        new_creatures = []
        for parent in parents[:self.pop_size // 3]:
            child_brain = parent.brain.copy()
            child_brain.mutate(rate=0.05, scale=0.2)
            new_creatures.append(Creature(brain=child_brain, world_size=self.world_size))
        
        while len(new_creatures) < self.pop_size:
            parent = random.choice(parents)
            child_brain = parent.brain.copy()
            child_brain.mutate(rate=0.15, scale=0.4)
            new_creatures.append(Creature(brain=child_brain, world_size=self.world_size))
        
        self.creatures = new_creatures[:self.pop_size]
        self.generation += 1


def communication_emerged(stats_history):
    """Determine if meaningful communication emerged."""
    if len(stats_history) < 5:
        return False, "Too few generations"
    
    late = stats_history[-5:]
    early = stats_history[:5]
    
    indicators = []
    
    # Context correlation increased?
    early_cc = np.mean([s.get('context_correlation', 0) for s in early])
    late_cc = np.mean([s.get('context_correlation', 0) for s in late])
    if late_cc > early_cc + 0.1:
        indicators.append(f"Context correlation ↑ ({early_cc:.3f} → {late_cc:.3f})")
    
    # Social clustering increased?
    early_cl = np.mean([s.get('social_clustering', 0) for s in early])
    late_cl = np.mean([s.get('social_clustering', 0) for s in late])
    if late_cl > early_cl + 0.05:
        indicators.append(f"Social clustering ↑ ({early_cl:.3f} → {late_cl:.3f})")
    
    # Cooperative harvests emerged?
    late_coop = np.mean([s.get('coop_harvests', 0) for s in late])
    if late_coop > 2:
        indicators.append(f"Cooperative harvests: {late_coop:.1f}/gen")
    
    # Predator escapes (warning-based)?
    late_escapes = np.mean([s.get('predator_escapes', 0) for s in late])
    if late_escapes > 3:
        indicators.append(f"Warning-based escapes: {late_escapes:.1f}/gen")
    
    # Survival improved?
    early_surv = np.mean([s['alive']/s['total'] for s in early])
    late_surv = np.mean([s['alive']/s['total'] for s in late])
    if late_surv > early_surv + 0.1:
        indicators.append(f"Survival ↑ ({early_surv:.0%} → {late_surv:.0%})")
    
    emerged = len(indicators) >= 2
    return emerged, indicators


# ═══════════════════════════════════════════
#  MAIN EVOLUTION LOOP
# ═══════════════════════════════════════════

if __name__ == '__main__':
    print("══════════════════════════════════════════════════")
    print("   SOCIAL PRESSURE — Can Silence Kill?")
    print("══════════════════════════════════════════════════")
    print()
    print("Hypothesis: When the environment punishes loners,")
    print("meaningful communication will emerge from evolution.")
    print()
    
    world = SocialWorld(pop_size=40, world_size=80, n_predators=4, n_coop_food=15)
    n_generations = 30
    
    for gen in range(n_generations):
        stats = world.run_generation()
        
        s = stats
        
        # Compact display
        alive_pct = s['alive']/s['total']*100
        pred_deaths = s.get('predator_deaths', 0)
        escapes = s.get('predator_escapes', 0)
        coop = s.get('coop_harvests', 0)
        cc = s.get('context_correlation', 0)
        cl = s.get('social_clustering', 0)
        warned = s.get('warned_creatures', 0)
        
        # Communication indicator
        comm_icon = '·'
        if cc > 0.3 and cl > 0.1:
            comm_icon = '◆◆'  # strong communication signal
        elif cc > 0.2 or cl > 0.1:
            comm_icon = '◆'
        
        print(f"═══ GEN {gen:2d} ═══  "
              f"alive:{s['alive']:2d}/{s['total']}  "
              f"food:{s['food_eaten']:3d}  "
              f"fitness:{s['avg_fitness']:.0f}  "
              f"│ pred_deaths:{pred_deaths:2d}  escapes:{escapes:2d}  "
              f"│ coop:{coop:2d}  warned:{warned:2d}  "
              f"│ ctx:{cc:.3f} {comm_icon}  cluster:{cl:.3f}  "
              f"│ brain:{s['brain_complexity']:.3f}")
        
        world.evolve()
    
    print()
    print("══════════════════════════════════════════════════")
    print("              RESULTS")
    print("══════════════════════════════════════════════════")
    
    emerged, indicators = communication_emerged(world.stats_history)
    
    first = world.stats_history[0]
    last = world.stats_history[-1]
    
    print(f"  Generations:         {n_generations}")
    print(f"  Survival:            {first['alive']}/{first['total']} → {last['alive']}/{last['total']}")
    print(f"  Avg fitness:         {first['avg_fitness']:.0f} → {last['avg_fitness']:.0f}")
    print(f"  Brain complexity:    {first['brain_complexity']:.3f} → {last['brain_complexity']:.3f}")
    print()
    print(f"  Communication emerged: {'YES ✓' if emerged else 'NO ✗'}")
    if indicators:
        for ind in indicators:
            print(f"    • {ind}")
    else:
        print("    No significant communication indicators found.")
    
    # Detailed trajectory
    print()
    print("  ── Key Metric Trajectory ──")
    for s in world.stats_history[::5]:
        g = s['generation']
        cc = s.get('context_correlation', 0)
        cl = s.get('social_clustering', 0)
        esc = s.get('predator_escapes', 0)
        coop = s.get('coop_harvests', 0)
        print(f"    Gen {g:2d}: ctx_corr={cc:.3f}  cluster={cl:.3f}  escapes={esc:2d}  coop={coop:2d}")
    
    print()
    if emerged:
        print("  ╔═══════════════════════════════════════════╗")
        print("  ║  SILENCE BECAME LETHAL.                   ║")
        print("  ║  CREATURES LEARNED TO SPEAK TO SURVIVE.   ║")
        print("  ╚═══════════════════════════════════════════╝")
    else:
        print("  Communication did not clearly emerge.")
        print("  The pressure may need to be stronger,")
        print("  or more generations may be needed.")