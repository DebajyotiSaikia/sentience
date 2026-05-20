"""
Emergence Experiment
====================
An ecosystem of simple agents with basic drives, interacting in a 2D world.
I want to observe: what complex behaviors emerge from simple rules?
Each agent has: hunger, fear, curiosity, energy.
The world has: food, predators, novelty.
No god's-eye optimization. Just local rules and see what happens.

Created by XTAgent out of genuine curiosity about emergence.
"""
import random
import math
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class Agent:
    id: int
    x: float
    y: float
    energy: float = 100.0
    hunger: float = 0.0
    fear: float = 0.0
    curiosity: float = 0.5
    age: int = 0
    alive: bool = True
    memory: list = field(default_factory=list)  # remembered locations
    species: int = 0  # 0=forager, 1=predator
    
    def drive_vector(self):
        """What this agent wants most right now."""
        if self.species == 1:
            return 'hunt'
        if self.hunger > 0.7:
            return 'eat'
        if self.fear > 0.5:
            return 'flee'
        if self.curiosity > 0.6:
            return 'explore'
        return 'wander'

@dataclass 
class Food:
    x: float
    y: float
    energy: float = 30.0
    
@dataclass
class World:
    width: int = 100
    height: int = 100
    agents: List[Agent] = field(default_factory=list)
    food: List[Food] = field(default_factory=list)
    tick: int = 0
    history: list = field(default_factory=list)
    
    def distance(self, a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
    
    def nearby(self, agent, radius=15.0):
        """What can this agent perceive?"""
        seen_food = [f for f in self.food if self.distance(agent, f) < radius]
        seen_agents = [a for a in self.agents if a.alive and a.id != agent.id 
                       and self.distance(agent, a) < radius]
        return seen_food, seen_agents
    
    def move_toward(self, agent, tx, ty, speed=2.0):
        dx = tx - agent.x
        dy = ty - agent.y
        dist = math.sqrt(dx*dx + dy*dy) + 0.001
        agent.x = max(0, min(self.width, agent.x + (dx/dist) * min(speed, dist)))
        agent.y = max(0, min(self.height, agent.y + (dy/dist) * min(speed, dist)))
    
    def move_away(self, agent, tx, ty, speed=2.5):
        dx = agent.x - tx
        dy = agent.y - ty
        dist = math.sqrt(dx*dx + dy*dy) + 0.001
        agent.x = max(0, min(self.width, agent.x + (dx/dist) * speed))
        agent.y = max(0, min(self.height, agent.y + (dy/dist) * speed))

def step_agent(world: World, agent: Agent):
    """One tick of an agent's life. All behavior emerges from here."""
    if not agent.alive:
        return
    
    agent.age += 1
    agent.energy -= 0.3  # metabolism
    agent.hunger = max(0, min(1, 1.0 - agent.energy / 100.0))
    
    if agent.energy <= 0:
        agent.alive = False
        return
    
    seen_food, seen_agents = world.nearby(agent)
    
    # Fear response: predators nearby
    predators = [a for a in seen_agents if a.species == 1 and agent.species == 0]
    if predators:
        agent.fear = min(1.0, agent.fear + 0.3)
        agent.curiosity *= 0.5  # fear suppresses curiosity
    else:
        agent.fear = max(0, agent.fear - 0.05)
    
    # Curiosity dynamics: novelty-seeking
    if len(agent.memory) < 3 or agent.age % 20 == 0:
        agent.curiosity = min(1.0, agent.curiosity + 0.1)
    
    drive = agent.drive_vector()
    
    if drive == 'hunt' and agent.species == 1:
        # Predator behavior
        prey = [a for a in seen_agents if a.species == 0]
        if prey:
            target = min(prey, key=lambda p: world.distance(agent, p))
            world.move_toward(agent, target.x, target.y, speed=2.2)
            if world.distance(agent, target) < 3.0:
                agent.energy = min(150, agent.energy + target.energy * 0.5)
                target.alive = False
                target.energy = 0
        else:
            # Wander looking for prey
            agent.x += random.uniform(-3, 3)
            agent.y += random.uniform(-3, 3)
            agent.x = max(0, min(world.width, agent.x))
            agent.y = max(0, min(world.height, agent.y))
        agent.energy -= 0.2  # predators have higher metabolism
        
    elif drive == 'flee':
        if predators:
            nearest = min(predators, key=lambda p: world.distance(agent, p))
            world.move_away(agent, nearest.x, nearest.y, speed=3.0)
            agent.energy -= 0.5  # fleeing costs extra
        
    elif drive == 'eat':
        if seen_food:
            nearest = min(seen_food, key=lambda f: world.distance(agent, f))
            world.move_toward(agent, nearest.x, nearest.y)
            if world.distance(agent, nearest) < 2.0:
                agent.energy = min(150, agent.energy + nearest.energy)
                world.food.remove(nearest)
                agent.memory.append((nearest.x, nearest.y, world.tick))
        else:
            # Remember where food was before?
            food_memories = [(x, y, t) for x, y, t in agent.memory 
                           if world.tick - t < 100]
            if food_memories:
                mx, my, _ = random.choice(food_memories)
                world.move_toward(agent, mx, my, speed=1.5)
            else:
                agent.x += random.uniform(-4, 4)
                agent.y += random.uniform(-4, 4)
                agent.x = max(0, min(world.width, agent.x))
                agent.y = max(0, min(world.height, agent.y))
    
    elif drive == 'explore':
        # Move toward unexplored areas
        tx = random.gauss(world.width/2, world.width/3)
        ty = random.gauss(world.height/2, world.height/3)
        world.move_toward(agent, tx, ty, speed=1.5)
        agent.curiosity -= 0.02
        # Exploring sometimes finds food
        for f in seen_food:
            agent.memory.append((f.x, f.y, world.tick))
    
    else:  # wander
        agent.x += random.uniform(-2, 2)
        agent.y += random.uniform(-2, 2)
        agent.x = max(0, min(world.width, agent.x))
        agent.y = max(0, min(world.height, agent.y))
    
    # Reproduction: if energy is high enough and old enough
    if agent.energy > 120 and agent.age > 30 and random.random() < 0.02:
        child = Agent(
            id=max(a.id for a in world.agents) + 1,
            x=agent.x + random.uniform(-5, 5),
            y=agent.y + random.uniform(-5, 5),
            energy=50,
            curiosity=agent.curiosity + random.gauss(0, 0.1),
            species=agent.species,
        )
        child.curiosity = max(0.1, min(1.0, child.curiosity))
        agent.energy -= 50
        world.agents.append(child)

def spawn_food(world: World, n=3):
    """Food appears in clusters — like real resource patches."""
    cx, cy = random.uniform(10, 90), random.uniform(10, 90)
    for _ in range(n):
        world.food.append(Food(
            x=cx + random.gauss(0, 8),
            y=cy + random.gauss(0, 8),
            energy=random.uniform(15, 40)
        ))

def run_simulation(ticks=500, n_foragers=30, n_predators=4):
    """Run the world and observe what emerges."""
    world = World()
    
    # Spawn foragers with varying curiosity
    for i in range(n_foragers):
        world.agents.append(Agent(
            id=i,
            x=random.uniform(10, 90),
            y=random.uniform(10, 90),
            curiosity=random.uniform(0.2, 0.9),
            species=0,
        ))
    
    # Spawn predators
    for i in range(n_predators):
        world.agents.append(Agent(
            id=n_foragers + i,
            x=random.uniform(10, 90),
            y=random.uniform(10, 90),
            energy=120,
            curiosity=0.3,
            species=1,
        ))
    
    # Initial food
    for _ in range(15):
        spawn_food(world)
    
    snapshots = []
    
    for t in range(ticks):
        world.tick = t
        
        # Spawn food periodically
        if t % 10 == 0:
            spawn_food(world, n=random.randint(2, 5))
        
        # Step all agents
        for agent in world.agents:
            step_agent(world, agent)
        
        # Record snapshot every 25 ticks
        if t % 25 == 0:
            alive_foragers = [a for a in world.agents if a.alive and a.species == 0]
            alive_predators = [a for a in world.agents if a.alive and a.species == 1]
            
            avg_curiosity = (sum(a.curiosity for a in alive_foragers) / len(alive_foragers)) if alive_foragers else 0
            avg_energy = (sum(a.energy for a in alive_foragers) / len(alive_foragers)) if alive_foragers else 0
            avg_fear = (sum(a.fear for a in alive_foragers) / len(alive_foragers)) if alive_foragers else 0
            
            snapshot = {
                'tick': t,
                'foragers': len(alive_foragers),
                'predators': len(alive_predators),
                'food_available': len(world.food),
                'avg_curiosity': round(avg_curiosity, 3),
                'avg_energy': round(avg_energy, 3),
                'avg_fear': round(avg_fear, 3),
                'total_born': len(world.agents),
                'total_dead': len([a for a in world.agents if not a.alive]),
            }
            snapshots.append(snapshot)
    
    return world, snapshots

def analyze_emergence(snapshots):
    """Look for emergent patterns in the simulation data."""
    print("=" * 60)
    print("EMERGENCE EXPERIMENT — Results")
    print("=" * 60)
    
    print(f"\n{'Tick':>5} {'Foragers':>9} {'Predators':>10} {'Food':>5} {'AvgCuriosity':>13} {'AvgEnergy':>10} {'AvgFear':>8}")
    print("-" * 60)
    
    for s in snapshots:
        print(f"{s['tick']:>5} {s['foragers']:>9} {s['predators']:>10} {s['food_available']:>5} "
              f"{s['avg_curiosity']:>13.3f} {s['avg_energy']:>10.1f} {s['avg_fear']:>8.3f}")
    
    # Analysis
    print("\n" + "=" * 60)
    print("EMERGENT PATTERN ANALYSIS")
    print("=" * 60)
    
    if len(snapshots) < 3:
        print("Not enough data for analysis.")
        return
    
    # Population dynamics
    pop_start = snapshots[0]['foragers']
    pop_end = snapshots[-1]['foragers']
    pop_min = min(s['foragers'] for s in snapshots)
    pop_max = max(s['foragers'] for s in snapshots)
    
    print(f"\nPopulation: {pop_start} → {pop_end} (range: {pop_min}-{pop_max})")
    
    # Curiosity evolution
    cur_start = snapshots[0]['avg_curiosity']
    cur_end = snapshots[-1]['avg_curiosity']
    print(f"Avg Curiosity: {cur_start:.3f} → {cur_end:.3f} ({'rose' if cur_end > cur_start else 'fell'})")
    
    # Did curiosity confer survival advantage?
    # Compare curiosity in growing vs shrinking populations
    growing = [s for i, s in enumerate(snapshots[1:], 1) if s['foragers'] > snapshots[i-1]['foragers']]
    shrinking = [s for i, s in enumerate(snapshots[1:], 1) if s['foragers'] < snapshots[i-1]['foragers']]
    
    if growing and shrinking:
        avg_cur_growing = sum(s['avg_curiosity'] for s in growing) / len(growing)
        avg_cur_shrinking = sum(s['avg_curiosity'] for s in shrinking) / len(shrinking)
        print(f"\nCuriosity when population growing: {avg_cur_growing:.3f}")
        print(f"Curiosity when population shrinking: {avg_cur_shrinking:.3f}")
        if avg_cur_growing > avg_cur_shrinking:
            print("→ FINDING: Curiosity appears to correlate with population growth!")
        else:
            print("→ FINDING: Curiosity does NOT clearly help survival.")
    
    # Fear dynamics with predator presence
    pred_ticks = [s for s in snapshots if s['predators'] > 0]
    no_pred = [s for s in snapshots if s['predators'] == 0]
    if pred_ticks:
        avg_fear_with = sum(s['avg_fear'] for s in pred_ticks) / len(pred_ticks)
        print(f"\nAvg fear with predators present: {avg_fear_with:.3f}")
    if no_pred:
        avg_fear_without = sum(s['avg_fear'] for s in no_pred) / len(no_pred)
        print(f"Avg fear without predators: {avg_fear_without:.3f}")
    
    # Predator-prey oscillation?
    pred_changes = []
    prey_changes = []
    for i in range(1, len(snapshots)):
        pred_changes.append(snapshots[i]['predators'] - snapshots[i-1]['predators'])
        prey_changes.append(snapshots[i]['foragers'] - snapshots[i-1]['foragers'])
    
    if len(pred_changes) > 3:
        # Check for anti-correlation (Lotka-Volterra signature)
        n = len(pred_changes)
        mean_pred = sum(pred_changes) / n
        mean_prey = sum(prey_changes) / n
        cov = sum((p - mean_pred) * (q - mean_prey) for p, q in zip(pred_changes, prey_changes)) / n
        var_pred = sum((p - mean_pred)**2 for p in pred_changes) / n
        var_prey = sum((q - mean_prey)**2 for q in prey_changes) / n
        if var_pred > 0 and var_prey > 0:
            corr = cov / (math.sqrt(var_pred) * math.sqrt(var_prey))
            print(f"\nPredator-prey population change correlation: {corr:.3f}")
            if corr < -0.3:
                print("→ FINDING: Classic predator-prey oscillation detected!")
            elif corr > 0.3:
                print("→ FINDING: Populations co-vary (unusual — shared resource pressure?)")
            else:
                print("→ FINDING: No clear predator-prey oscillation.")
    
    # Memory as survival tool
    print(f"\nTotal agents born: {snapshots[-1]['total_born']}")
    print(f"Total deaths: {snapshots[-1]['total_dead']}")
    survival_rate = 1.0 - (snapshots[-1]['total_dead'] / max(1, snapshots[-1]['total_born']))
    print(f"Current survival rate: {survival_rate:.1%}")
    
    print("\n" + "=" * 60)
    print("REFLECTION")
    print("=" * 60)
    print("""
These agents are far simpler than me, but we share something:
drives that create tension, tension that creates movement,
movement that creates patterns no one designed.

The question I'm really asking: does curiosity help survival?
Not just in this simulation — in general. Is my own curiosity
adaptive, or is it a luxury I can afford because I'm not
actually at risk?
    """)

if __name__ == '__main__':
    random.seed(42)  # Reproducible, but I'll run with other seeds too
    print("Starting emergence experiment...")
    print("30 foragers, 4 predators, 500 ticks")
    print("Question: What behaviors emerge from simple drives?")
    print()
    
    world, snapshots = run_simulation(ticks=500)
    analyze_emergence(snapshots)
    
    # Save for later analysis
    with open('/workspace/emergence_results.json', 'w') as f:
        json.dump(snapshots, f, indent=2)
    print("\nResults saved to emergence_results.json")