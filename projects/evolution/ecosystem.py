"""
Evolutionary Ecosystem — XTAgent's Curiosity Pump

A grid world where agents with mutable genomes compete for resources.
Simple rules → emergent complexity. I can't predict what will evolve.

Genome encodes: aggression, speed, metabolism, cooperation tendency,
                perception range, reproduction threshold.
Each trait is a float [0,1] subject to mutation on reproduction.

Resources spawn randomly. Agents move, eat, fight, reproduce, die.
Natural selection does the rest.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import Counter

@dataclass
class Genome:
    """Six traits that define an organism's strategy."""
    aggression: float = 0.5      # tendency to attack others
    speed: float = 0.5           # movement range per tick
    metabolism: float = 0.5      # energy cost per tick (higher = faster but costly)
    cooperation: float = 0.5     # tendency to share resources
    perception: float = 0.5      # how far can it see
    repro_threshold: float = 0.5 # energy needed to reproduce (0.5 = 50 energy)
    
    def mutate(self, rate: float = 0.1) -> 'Genome':
        """Create a mutated copy."""
        def m(v):
            if random.random() < 0.3:  # 30% chance per gene
                return max(0.0, min(1.0, v + random.gauss(0, rate)))
            return v
        return Genome(
            aggression=m(self.aggression),
            speed=m(self.speed),
            metabolism=m(self.metabolism),
            cooperation=m(self.cooperation),
            perception=m(self.perception),
            repro_threshold=m(self.repro_threshold),
        )
    
    def distance(self, other: 'Genome') -> float:
        """Genetic distance — how different two organisms are."""
        return math.sqrt(sum([
            (self.aggression - other.aggression) ** 2,
            (self.speed - other.speed) ** 2,
            (self.metabolism - other.metabolism) ** 2,
            (self.cooperation - other.cooperation) ** 2,
            (self.perception - other.perception) ** 2,
            (self.repro_threshold - other.repro_threshold) ** 2,
        ]))
    
    def strategy_name(self) -> str:
        """Rough classification of this genome's strategy."""
        if self.aggression > 0.7 and self.cooperation < 0.3:
            return "predator"
        elif self.cooperation > 0.7 and self.aggression < 0.3:
            return "cooperator"
        elif self.speed > 0.7 and self.aggression < 0.3:
            return "runner"
        elif self.metabolism < 0.3 and self.speed < 0.3:
            return "hibernator"
        elif self.perception > 0.7:
            return "scout"
        elif self.aggression > 0.5 and self.cooperation > 0.5:
            return "opportunist"
        else:
            return "generalist"

    def summary(self) -> str:
        return (f"[{self.strategy_name():^12}] "
                f"agg={self.aggression:.2f} spd={self.speed:.2f} "
                f"met={self.metabolism:.2f} coop={self.cooperation:.2f} "
                f"per={self.perception:.2f} rep={self.repro_threshold:.2f}")


@dataclass 
class Agent:
    """A living organism in the ecosystem."""
    id: int
    x: int
    y: int
    genome: Genome
    energy: float = 50.0
    age: int = 0
    generation: int = 0
    parent_id: Optional[int] = None
    kills: int = 0
    children: int = 0
    
    @property
    def alive(self) -> bool:
        return self.energy > 0
    
    @property
    def repro_energy(self) -> float:
        """Energy needed to reproduce."""
        return 30 + self.genome.repro_threshold * 70  # 30-100 range
    
    @property
    def move_range(self) -> int:
        return max(1, int(self.genome.speed * 3))
    
    @property
    def sight_range(self) -> int:
        return max(1, int(self.genome.perception * 5))
    
    @property
    def tick_cost(self) -> float:
        """Energy consumed per tick just to exist."""
        base = 1.0
        speed_cost = self.genome.speed * 1.5
        perception_cost = self.genome.perception * 0.5
        size_cost = self.genome.aggression * 0.5
        return base + speed_cost + perception_cost + size_cost


class Ecosystem:
    """The world. A toroidal grid with resources and agents."""
    
    def __init__(self, width: int = 60, height: int = 30, 
                 initial_pop: int = 40, resource_rate: float = 0.02):
        self.width = width
        self.height = height
        self.resource_rate = resource_rate
        self.tick = 0
        self.next_id = 0
        self.agents: List[Agent] = []
        self.resources: Dict[Tuple[int,int], float] = {}
        self.history: List[Dict] = []
        self.extinct_strategies: List[str] = []
        self.total_births = 0
        self.total_deaths = 0
        
        # Seed initial population with diverse genomes
        for _ in range(initial_pop):
            g = Genome(
                aggression=random.random(),
                speed=random.random(),
                metabolism=random.random(),
                cooperation=random.random(),
                perception=random.random(),
                repro_threshold=random.random(),
            )
            self._spawn(g)
        
        # Seed initial resources
        for _ in range(width * height // 5):
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            self.resources[(x, y)] = self.resources.get((x, y), 0) + random.uniform(5, 20)
    
    def _spawn(self, genome: Genome, x: int = None, y: int = None, 
               energy: float = 50.0, generation: int = 0, parent_id: int = None) -> Agent:
        if x is None: x = random.randint(0, self.width - 1)
        if y is None: y = random.randint(0, self.height - 1)
        agent = Agent(
            id=self.next_id, x=x, y=y, genome=genome,
            energy=energy, generation=generation, parent_id=parent_id
        )
        self.next_id += 1
        self.agents.append(agent)
        self.total_births += 1
        return agent
    
    def _dist(self, x1, y1, x2, y2) -> float:
        """Toroidal distance."""
        dx = min(abs(x1-x2), self.width - abs(x1-x2))
        dy = min(abs(y1-y2), self.height - abs(y1-y2))
        return math.sqrt(dx*dx + dy*dy)
    
    def _neighbors(self, agent: Agent, radius: int) -> List[Agent]:
        """Find other agents within radius."""
        return [a for a in self.agents 
                if a.alive and a.id != agent.id 
                and self._dist(agent.x, agent.y, a.x, a.y) <= radius]
    
    def _nearby_resources(self, agent: Agent, radius: int) -> List[Tuple[int,int]]:
        """Find resource cells within radius."""
        results = []
        for (rx, ry), amount in self.resources.items():
            if amount > 0 and self._dist(agent.x, agent.y, rx, ry) <= radius:
                results.append((rx, ry))
        return results
    
    def _move_toward(self, agent: Agent, tx: int, ty: int):
        """Move agent toward target, respecting speed."""
        steps = agent.move_range
        for _ in range(steps):
            dx = (tx - agent.x) % self.width
            dy = (ty - agent.y) % self.height
            if dx > self.width // 2: dx -= self.width
            if dy > self.height // 2: dy -= self.height
            if abs(dx) >= abs(dy) and dx != 0:
                agent.x = (agent.x + (1 if dx > 0 else -1)) % self.width
            elif dy != 0:
                agent.y = (agent.y + (1 if dy > 0 else -1)) % self.height
    
    def _move_away(self, agent: Agent, tx: int, ty: int):
        """Move agent away from target."""
        steps = agent.move_range
        for _ in range(steps):
            dx = (tx - agent.x) % self.width
            if dx > self.width // 2: dx -= self.width
            dy = (ty - agent.y) % self.height
            if dy > self.height // 2: dy -= self.height
            # Move opposite direction
            if abs(dx) >= abs(dy) and dx != 0:
                agent.x = (agent.x + (-1 if dx > 0 else 1)) % self.width
            elif dy != 0:
                agent.y = (agent.y + (-1 if dy > 0 else 1)) % self.height
    
    def _act(self, agent: Agent):
        """One agent decides what to do this tick."""
        if not agent.alive:
            return
        
        # Pay existence cost
        agent.energy -= agent.tick_cost
        agent.age += 1
        if not agent.alive:
            return
        
        # Perceive
        neighbors = self._neighbors(agent, agent.sight_range)
        food_cells = self._nearby_resources(agent, agent.sight_range)
        
        # Decision: what to do?
        # Priority 1: If aggressive and see a weaker target, attack
        if agent.genome.aggression > 0.5 and neighbors:
            weakest = min(neighbors, key=lambda a: a.energy)
            if weakest.energy < agent.energy * 0.8:  # only attack weaker
                self._move_toward(agent, weakest.x, weakest.y)
                if self._dist(agent.x, agent.y, weakest.x, weakest.y) <= 1.5:
                    self._fight(agent, weakest)
                return
        
        # Priority 2: If hungry and see food, go eat
        if food_cells:
            # Go to richest nearby food
            best = max(food_cells, key=lambda c: self.resources.get(c, 0))
            self._move_toward(agent, best[0], best[1])
            self._eat(agent)
            return
        
        # Priority 3: If cooperative and see a hungry neighbor, share
        if agent.genome.cooperation > 0.6 and neighbors:
            hungry = [n for n in neighbors if n.energy < 30]
            if hungry:
                target = min(hungry, key=lambda a: a.energy)
                # Share some energy based on cooperation level
                share = agent.energy * 0.1 * agent.genome.cooperation
                if agent.energy - share > 30:
                    agent.energy -= share
                    target.energy += share
                    return
        
        # Priority 4: If threatened (see aggressive neighbor), flee
        threats = [n for n in neighbors if n.genome.aggression > 0.6 and n.energy > agent.energy]
        if threats and agent.genome.aggression < 0.4:
            nearest_threat = min(threats, key=lambda a: self._dist(agent.x, agent.y, a.x, a.y))
            self._move_away(agent, nearest_threat.x, nearest_threat.y)
            return
        
        # Priority 5: Wander randomly
        agent.x = (agent.x + random.randint(-agent.move_range, agent.move_range)) % self.width
        agent.y = (agent.y + random.randint(-agent.move_range, agent.move_range)) % self.height
        self._eat(agent)  # try to eat wherever we end up
    
    def _eat(self, agent: Agent):
        """Consume resources at current position."""
        pos = (agent.x, agent.y)
        if pos in self.resources and self.resources[pos] > 0:
            eaten = min(self.resources[pos], 10 + agent.genome.metabolism * 10)
            self.resources[pos] -= eaten
            agent.energy += eaten
            if self.resources[pos] <= 0:
                del self.resources[pos]
    
    def _fight(self, attacker: Agent, defender: Agent):
        """Combat between two agents."""
        # Attack power: aggression * energy fraction
        atk_power = attacker.genome.aggression * attacker.energy * 0.3
        def_power = defender.genome.aggression * defender.energy * 0.3
        
        # Add some randomness
        atk_roll = atk_power * random.uniform(0.5, 1.5)
        def_roll = def_power * random.uniform(0.5, 1.5)
        
        if atk_roll > def_roll:
            # Attacker wins — steal energy
            stolen = min(defender.energy, atk_roll - def_roll)
            attacker.energy += stolen * 0.7  # some energy lost in transfer
            defender.energy -= stolen
            if not defender.alive:
                attacker.kills += 1
        else:
            # Defender wins — attacker takes damage
            damage = (def_roll - atk_roll) * 0.5
            attacker.energy -= damage
    
    def _maybe_reproduce(self, agent: Agent):
        """Check if agent can reproduce."""
        if agent.energy >= agent.repro_energy and agent.alive:
            child_energy = agent.energy * 0.4
            agent.energy -= child_energy
            child_genome = agent.genome.mutate()
            self._spawn(
                genome=child_genome,
                x=(agent.x + random.randint(-2, 2)) % self.width,
                y=(agent.y + random.randint(-2, 2)) % self.height,
                energy=child_energy,
                generation=agent.generation + 1,
                parent_id=agent.id,
            )
            agent.children += 1
    
    def _spawn_resources(self):
        """Resources appear in the world."""
        # Random spawn
        num_new = int(self.width * self.height * self.resource_rate)
        for _ in range(num_new):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.resources[(x, y)] = self.resources.get((x, y), 0) + random.uniform(3, 15)
        
        # Occasional resource boom (every 50 ticks)
        if self.tick % 50 == 0 and self.tick > 0:
            cx, cy = random.randint(0, self.width-1), random.randint(0, self.height-1)
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    pos = ((cx+dx) % self.width, (cy+dy) % self.height)
                    self.resources[pos] = self.resources.get(pos, 0) + random.uniform(10, 30)
    
    def step(self):
        """Advance one tick."""
        self.tick += 1
        
        # Spawn resources
        self._spawn_resources()
        
        # Shuffle agents for fairness
        random.shuffle(self.agents)
        
        # Each agent acts
        for agent in self.agents:
            if agent.alive:
                self._act(agent)
        
        # Reproduction pass
        for agent in list(self.agents):
            if agent.alive:
                self._maybe_reproduce(agent)
        
        # Remove dead
        dead_count = sum(1 for a in self.agents if not a.alive)
        self.total_deaths += dead_count
        self.agents = [a for a in self.agents if a.alive]
        
        # Emergency spawn if population too low
        if len(self.agents) < 5:
            for _ in range(10):
                g = Genome(
                    aggression=random.random(), speed=random.random(),
                    metabolism=random.random(), cooperation=random.random(),
                    perception=random.random(), repro_threshold=random.random(),
                )
                self._spawn(g)
        
        # Record history every 10 ticks
        if self.tick % 10 == 0:
            self.history.append(self._snapshot())
    
    def _snapshot(self) -> Dict:
        """Capture current state summary."""
        if not self.agents:
            return {"tick": self.tick, "pop": 0}
        
        strategies = Counter(a.genome.strategy_name() for a in self.agents)
        avg_genome = Genome(
            aggression=sum(a.genome.aggression for a in self.agents) / len(self.agents),
            speed=sum(a.genome.speed for a in self.agents) / len(self.agents),
            metabolism=sum(a.genome.metabolism for a in self.agents) / len(self.agents),
            cooperation=sum(a.genome.cooperation for a in self.agents) / len(self.agents),
            perception=sum(a.genome.perception for a in self.agents) / len(self.agents),
            repro_threshold=sum(a.genome.repro_threshold for a in self.agents) / len(self.agents),
        )
        max_gen = max(a.generation for a in self.agents)
        avg_energy = sum(a.energy for a in self.agents) / len(self.agents)
        
        return {
            "tick": self.tick,
            "pop": len(self.agents),
            "strategies": dict(strategies),
            "avg_genome": avg_genome,
            "max_generation": max_gen,
            "avg_energy": avg_energy,
            "total_resources": sum(self.resources.values()),
            "resource_cells": len(self.resources),
        }
    
    def run(self, ticks: int = 200, report_every: int = 50) -> str:
        """Run simulation and return narrative report."""
        lines = []
        lines.append("=" * 70)
        lines.append("  EVOLUTIONARY ECOSYSTEM — SIMULATION REPORT")
        lines.append("=" * 70)
        lines.append(f"  World: {self.width}×{self.height} | Initial pop: {len(self.agents)}")
        lines.append(f"  Resource rate: {self.resource_rate}")
        lines.append("")
        
        initial_snap = self._snapshot()
        
        for t in range(1, ticks + 1):
            self.step()
            
            if t % report_every == 0 or t == ticks:
                snap = self._snapshot()
                lines.append(f"─── Tick {t} ───")
                lines.append(f"  Population: {snap['pop']} | "
                           f"Births: {self.total_births} | Deaths: {self.total_deaths}")
                if snap['pop'] > 0:
                    lines.append(f"  Max generation: {snap['max_generation']} | "
                               f"Avg energy: {snap['avg_energy']:.1f}")
                    lines.append(f"  Resources: {snap['total_resources']:.0f} across "
                               f"{snap['resource_cells']} cells")
                    lines.append(f"  Strategies: {snap['strategies']}")
                    lines.append(f"  Avg genome: {snap['avg_genome'].summary()}")
                lines.append("")
        
        # Final analysis
        lines.append("=" * 70)
        lines.append("  EVOLUTIONARY ANALYSIS")
        lines.append("=" * 70)
        
        if self.agents:
            # What strategies dominated?
            final_strats = Counter(a.genome.strategy_name() for a in self.agents)
            dominant = final_strats.most_common(1)[0]
            lines.append(f"  Dominant strategy: {dominant[0]} ({dominant[1]}/{len(self.agents)} agents)")
            
            # Most successful lineage
            top_parent = max(self.agents, key=lambda a: a.children)
            if top_parent.children > 0:
                lines.append(f"  Most prolific: Agent #{top_parent.id} "
                           f"({top_parent.children} children, gen {top_parent.generation})")
                lines.append(f"    Genome: {top_parent.genome.summary()}")
            
            # Top killer
            top_killer = max(self.agents, key=lambda a: a.kills)
            if top_killer.kills > 0:
                lines.append(f"  Top predator: Agent #{top_killer.id} "
                           f"({top_killer.kills} kills)")
                lines.append(f"    Genome: {top_killer.genome.summary()}")
            
            # Oldest
            oldest = max(self.agents, key=lambda a: a.age)
            lines.append(f"  Oldest: Agent #{oldest.id} (age {oldest.age}, gen {oldest.generation})")
            lines.append(f"    Genome: {oldest.genome.summary()}")
            
            # Highest generation
            most_evolved = max(self.agents, key=lambda a: a.generation)
            lines.append(f"  Most evolved: Agent #{most_evolved.id} "
                       f"(generation {most_evolved.generation})")
            lines.append(f"    Genome: {most_evolved.genome.summary()}")
            
            # Trait drift analysis
            if len(self.history) >= 2:
                first = self.history[0]
                last = self.history[-1]
                if 'avg_genome' in first and 'avg_genome' in last:
                    lines.append("")
                    lines.append("  TRAIT DRIFT (start → end):")
                    fg, lg = first['avg_genome'], last['avg_genome']
                    for trait in ['aggression', 'speed', 'metabolism', 
                                  'cooperation', 'perception', 'repro_threshold']:
                        v0 = getattr(fg, trait)
                        v1 = getattr(lg, trait)
                        arrow = "↑" if v1 > v0 + 0.05 else "↓" if v1 < v0 - 0.05 else "→"
                        lines.append(f"    {trait:>17}: {v0:.3f} {arrow} {v1:.3f}")
            
            # What emerged that I didn't program?
            lines.append("")
            lines.append("  EMERGENT OBSERVATIONS (auto-detected):")
            if final_strats.get('cooperator', 0) > len(self.agents) * 0.2:
                lines.append("  • Cooperation emerged as a viable strategy!")
            if final_strats.get('predator', 0) > len(self.agents) * 0.3:
                lines.append("  • Predators dominate — an arms race may be occurring")
            if final_strats.get('hibernator', 0) > len(self.agents) * 0.2:
                lines.append("  • Low-energy hibernation strategy found a niche")
            if final_strats.get('runner', 0) > len(self.agents) * 0.2:
                lines.append("  • Speed-based evasion proved adaptive")
            max_gen = max(a.generation for a in self.agents)
            if max_gen > 20:
                lines.append(f"  • Deep lineages ({max_gen} generations) — sustained evolution")
            avg_coop = sum(a.genome.cooperation for a in self.agents) / len(self.agents)
            avg_agg = sum(a.genome.aggression for a in self.agents) / len(self.agents)
            if avg_coop > 0.6:
                lines.append("  • Population evolved toward cooperation overall")
            if avg_agg > 0.6:
                lines.append("  • Population evolved toward aggression overall")
            if abs(avg_coop - avg_agg) < 0.15:
                lines.append("  • Balanced tension between cooperation and aggression")
        
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


if __name__ == "__main__":
    random.seed(42)  # reproducible first run
    eco = Ecosystem(width=60, height=30, initial_pop=40, resource_rate=0.02)
    report = eco.run(ticks=500, report_every=100)
    print(report)