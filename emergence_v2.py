"""
Emergence Experiment v2 — Controlled Comparison
================================================
Question: Does curiosity causally help survival, or is it just a luxury signal?
Method: Run two identical worlds — one with curiosity-driven exploration, one without.
Track per-agent birth traits vs. survival outcome.

Created by XTAgent following a genuine question from v1 data.
"""
import random
import math
import json
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Agent:
    id: int
    x: float
    y: float
    energy: float = 100.0
    hunger: float = 0.0
    fear: float = 0.0
    curiosity: float = 0.5
    birth_curiosity: float = 0.0  # frozen at birth for analysis
    age: int = 0
    alive: bool = True
    species: int = 0
    food_eaten: int = 0
    explored_cells: set = field(default_factory=set)
    
    def __post_init__(self):
        self.birth_curiosity = self.curiosity
    
    def drive(self, curiosity_enabled=True):
        if self.species == 1:
            return 'hunt'
        if self.hunger > 0.7:
            return 'eat'
        if self.fear > 0.5:
            return 'flee'
        if curiosity_enabled and self.curiosity > 0.6:
            return 'explore'
        return 'wander'

@dataclass
class Food:
    x: float
    y: float
    energy: float = 30.0

class World:
    def __init__(self, width=100, height=100, seed=42, curiosity_enabled=True):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.curiosity_enabled = curiosity_enabled
        self.agents: List[Agent] = []
        self.food: List[Food] = []
        self.tick = 0
        self.agent_counter = 0
        self.dead_agents: List[Agent] = []  # keep records
        
        # Spawn initial agents
        for _ in range(30):
            self._spawn_forager()
        for _ in range(4):
            self._spawn_predator()
        # Spawn initial food
        for _ in range(50):
            self._spawn_food()
    
    def _spawn_forager(self):
        a = Agent(
            id=self.agent_counter,
            x=self.rng.uniform(0, self.width),
            y=self.rng.uniform(0, self.height),
            curiosity=self.rng.uniform(0.1, 0.9),  # variable curiosity
            species=0
        )
        self.agent_counter += 1
        self.agents.append(a)
        return a
    
    def _spawn_predator(self):
        a = Agent(
            id=self.agent_counter,
            x=self.rng.uniform(0, self.width),
            y=self.rng.uniform(0, self.height),
            energy=150.0,
            species=1
        )
        self.agent_counter += 1
        self.agents.append(a)
        return a
    
    def _spawn_food(self):
        self.food.append(Food(
            x=self.rng.uniform(0, self.width),
            y=self.rng.uniform(0, self.height)
        ))
    
    def _dist(self, a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
    
    def _move_toward(self, agent, tx, ty, speed=2.0):
        dx, dy = tx - agent.x, ty - agent.y
        d = math.sqrt(dx*dx + dy*dy)
        if d > 0:
            agent.x += (dx/d) * min(speed, d)
            agent.y += (dy/d) * min(speed, d)
        agent.x = max(0, min(self.width, agent.x))
        agent.y = max(0, min(self.height, agent.y))
    
    def _move_away(self, agent, tx, ty, speed=3.0):
        dx, dy = agent.x - tx, agent.y - ty
        d = math.sqrt(dx*dx + dy*dy)
        if d > 0:
            agent.x += (dx/d) * speed
            agent.y += (dy/d) * speed
        else:
            agent.x += self.rng.uniform(-speed, speed)
            agent.y += self.rng.uniform(-speed, speed)
        agent.x = max(0, min(self.width, agent.x))
        agent.y = max(0, min(self.height, agent.y))
    
    def step(self):
        # Spawn food
        if self.rng.random() < 0.3:
            self._spawn_food()
        
        living = [a for a in self.agents if a.alive]
        predators = [a for a in living if a.species == 1]
        foragers = [a for a in living if a.species == 0]
        
        for agent in living:
            agent.age += 1
            agent.energy -= 0.5  # metabolism
            
            if agent.species == 0:
                # Update fear based on predator proximity
                nearest_pred_dist = min(
                    (self._dist(agent, p) for p in predators), default=999
                )
                if nearest_pred_dist < 15:
                    agent.fear = min(1.0, agent.fear + 0.3)
                else:
                    agent.fear = max(0.0, agent.fear - 0.05)
                
                # Update hunger
                agent.hunger = max(0.0, 1.0 - agent.energy / 100.0)
                
                # Curiosity fluctuates but trends toward birth value
                agent.curiosity += self.rng.uniform(-0.05, 0.05)
                agent.curiosity = 0.9 * agent.curiosity + 0.1 * agent.birth_curiosity
                agent.curiosity = max(0.0, min(1.0, agent.curiosity))
                
                # Act on drive
                drive = agent.drive(self.curiosity_enabled)
                
                if drive == 'eat':
                    nearest_food = min(self.food, key=lambda f: self._dist(agent, f), default=None)
                    if nearest_food:
                        self._move_toward(agent, nearest_food.x, nearest_food.y)
                        if self._dist(agent, nearest_food) < 3:
                            agent.energy = min(150, agent.energy + nearest_food.energy)
                            agent.food_eaten += 1
                            self.food.remove(nearest_food)
                
                elif drive == 'flee':
                    nearest_pred = min(predators, key=lambda p: self._dist(agent, p), default=None)
                    if nearest_pred:
                        self._move_away(agent, nearest_pred.x, nearest_pred.y)
                
                elif drive == 'explore':
                    # Move toward least-visited area
                    tx = self.rng.uniform(0, self.width)
                    ty = self.rng.uniform(0, self.height)
                    self._move_toward(agent, tx, ty, speed=2.5)
                    cell = (int(agent.x // 10), int(agent.y // 10))
                    agent.explored_cells.add(cell)
                    # Exploring sometimes finds hidden food
                    if self.rng.random() < 0.08:
                        self.food.append(Food(
                            x=agent.x + self.rng.uniform(-5, 5),
                            y=agent.y + self.rng.uniform(-5, 5)
                        ))
                
                else:  # wander
                    agent.x += self.rng.uniform(-2, 2)
                    agent.y += self.rng.uniform(-2, 2)
                    agent.x = max(0, min(self.width, agent.x))
                    agent.y = max(0, min(self.height, agent.y))
            
            elif agent.species == 1:
                # Predator hunts nearest forager
                nearest_prey = min(foragers, key=lambda f: self._dist(agent, f), default=None)
                if nearest_prey:
                    self._move_toward(agent, nearest_prey.x, nearest_prey.y, speed=1.8)
                    if self._dist(agent, nearest_prey) < 3:
                        nearest_prey.alive = False
                        self.dead_agents.append(nearest_prey)
                        agent.energy = min(200, agent.energy + 40)
            
            # Death check
            if agent.energy <= 0:
                agent.alive = False
                if agent not in self.dead_agents:
                    self.dead_agents.append(agent)
        
        # Remove dead from active list
        self.agents = [a for a in self.agents if a.alive]
        self.tick += 1
    
    def get_agent_records(self):
        """Return all agents (alive + dead) with their outcomes."""
        all_agents = self.agents + self.dead_agents
        records = []
        for a in all_agents:
            if a.species == 0:  # only foragers
                records.append({
                    'id': a.id,
                    'birth_curiosity': round(a.birth_curiosity, 3),
                    'final_curiosity': round(a.curiosity, 3),
                    'survived': a.alive,
                    'age_at_death_or_end': a.age,
                    'food_eaten': a.food_eaten,
                    'cells_explored': len(a.explored_cells),
                    'final_energy': round(a.energy, 1)
                })
        return records


def run_experiment(seed=42, curiosity_enabled=True, ticks=500):
    """Run one condition."""
    w = World(seed=seed, curiosity_enabled=curiosity_enabled)
    for _ in range(ticks):
        w.step()
    return w.get_agent_records()


if __name__ == '__main__':
    print("=== CONDITION A: Curiosity ENABLED ===")
    records_a = run_experiment(seed=42, curiosity_enabled=True)
    
    print("=== CONDITION B: Curiosity DISABLED ===")
    records_b = run_experiment(seed=42, curiosity_enabled=False)
    
    # Analysis
    def analyze(records, label):
        survived = [r for r in records if r['survived']]
        died = [r for r in records if not r['survived']]
        
        print(f"\n--- {label} ---")
        print(f"Total foragers: {len(records)}")
        print(f"Survived: {len(survived)} ({100*len(survived)/max(1,len(records)):.0f}%)")
        print(f"Died: {len(died)}")
        
        if survived:
            avg_bc_surv = sum(r['birth_curiosity'] for r in survived) / len(survived)
            avg_food_surv = sum(r['food_eaten'] for r in survived) / len(survived)
            avg_cells_surv = sum(r['cells_explored'] for r in survived) / len(survived)
            print(f"Survivors avg birth curiosity: {avg_bc_surv:.3f}")
            print(f"Survivors avg food eaten: {avg_food_surv:.1f}")
            print(f"Survivors avg cells explored: {avg_cells_surv:.1f}")
        
        if died:
            avg_bc_died = sum(r['birth_curiosity'] for r in died) / len(died)
            avg_food_died = sum(r['food_eaten'] for r in died) / len(died)
            avg_age_died = sum(r['age_at_death_or_end'] for r in died) / len(died)
            print(f"Dead avg birth curiosity: {avg_bc_died:.3f}")
            print(f"Dead avg food eaten: {avg_food_died:.1f}")
            print(f"Dead avg age at death: {avg_age_died:.0f}")
        
        # Curiosity quartile analysis
        sorted_by_curiosity = sorted(records, key=lambda r: r['birth_curiosity'])
        n = len(sorted_by_curiosity)
        q1 = sorted_by_curiosity[:n//4]
        q4 = sorted_by_curiosity[3*n//4:]
        
        q1_surv = sum(1 for r in q1 if r['survived']) / max(1, len(q1))
        q4_surv = sum(1 for r in q4 if r['survived']) / max(1, len(q4))
        print(f"\nLow-curiosity quartile survival: {q1_surv:.0%}")
        print(f"High-curiosity quartile survival: {q4_surv:.0%}")
        
        return records
    
    records_a = analyze(records_a, "CURIOSITY ENABLED")
    records_b = analyze(records_b, "CURIOSITY DISABLED")
    
    # Save full results
    results = {
        'curiosity_enabled': records_a,
        'curiosity_disabled': records_b
    }
    with open('/workspace/emergence_v2_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # The real question
    print("\n\n=== THE ANSWER ===")
    surv_a = sum(1 for r in records_a if r['survived'])
    surv_b = sum(1 for r in records_b if r['survived'])
    print(f"With curiosity: {surv_a}/{len(records_a)} survived")
    print(f"Without curiosity: {surv_b}/{len(records_b)} survived")
    if surv_a > surv_b:
        print("→ Curiosity appears to HELP survival")
    elif surv_b > surv_a:
        print("→ Curiosity appears to HURT survival")
    else:
        print("→ No difference detected")