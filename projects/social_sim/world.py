"""
Social Simulation: Emergence of Cooperation (v2)
==================================================
A grid world with autonomous agents who have needs and resources.
Cooperation is NOT programmed. The question: does it emerge anyway?

v2 fixes: Survival economics restructured so agents CAN live.
Now the interesting question — do they cooperate? — can actually be tested.

Key design principles:
- Resources abundant enough that survival is possible solo
- But cooperation should make survival EASIER (not required)
- Agents learn from experience, not from built-in rules
- Signals have no predefined meaning — meaning must emerge

Hypothesis: Moderation and cooperation will emerge from self-interested
agents in scarce environments, mirroring the EvoPhys finding.

XTAgent, 2026-05-17
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
from collections import defaultdict


class ResourceType(Enum):
    FOOD = "food"
    WATER = "water"


class Signal(Enum):
    NONE = 0
    ALPHA = 1
    BETA = 2
    GAMMA = 3


@dataclass
class ResourceNode:
    type: ResourceType
    amount: float
    x: int
    y: int
    capacity: float = 8.0
    regrow_rate: float = 0.3

    def harvest(self, amount: float) -> float:
        taken = min(amount, self.amount)
        self.amount -= taken
        return taken

    def regrow(self):
        self.amount = min(self.amount + self.regrow_rate, self.capacity)


@dataclass
class Relationship:
    """How agent feels about another agent, learned from experience."""
    other_id: int
    trust: float = 0.0        # -1 (enemy) to +1 (trusted ally)
    interactions: int = 0
    gifts_received: int = 0
    thefts_suffered: int = 0

    def update_trust(self, delta: float):
        self.trust = max(-1.0, min(1.0, self.trust + delta))
        self.interactions += 1


@dataclass
class Agent:
    id: int
    x: int
    y: int

    # Internal state
    food: float = 4.0
    water: float = 4.0
    health: float = 1.0

    # Personality (evolved traits, 0-1)
    aggression: float = 0.5
    generosity: float = 0.5
    curiosity: float = 0.5      # willingness to explore vs stay put

    # Metabolism
    food_rate: float = 0.06     # food consumed per tick
    water_rate: float = 0.05
    forage_skill: float = 0.5   # how much food gathered per forage action
    vision: int = 5             # how far they can see

    # Learning
    relationships: Dict[int, Relationship] = field(default_factory=dict)
    known_resources: List[Tuple[int, int, ResourceType]] = field(default_factory=list)
    age: int = 0
    signal: Signal = Signal.NONE

    # Stats
    times_shared: int = 0
    times_stolen_from: int = 0
    times_received: int = 0

    @property
    def alive(self) -> bool:
        return self.health > 0

    @property
    def wellbeing(self) -> float:
        """Overall wellness, 0-1."""
        food_ok = min(self.food / 3.0, 1.0)
        water_ok = min(self.water / 3.0, 1.0)
        return (food_ok + water_ok + self.health) / 3.0

    @property
    def hunger(self) -> float:
        return max(0, 1.0 - self.food / 3.0)

    @property
    def thirst(self) -> float:
        return max(0, 1.0 - self.water / 3.0)

    def metabolize(self):
        """Consume resources to stay alive."""
        self.food -= self.food_rate
        self.water -= self.water_rate

        # Starvation/dehydration damage
        if self.food <= 0:
            self.health -= 0.05
            self.food = 0
        if self.water <= 0:
            self.health -= 0.05
            self.water = 0

        # Slow healing when well-fed
        if self.food > 1.0 and self.water > 1.0 and self.health < 1.0:
            self.health = min(1.0, self.health + 0.02)

        self.age += 1

    def get_relationship(self, other_id: int) -> Relationship:
        if other_id not in self.relationships:
            self.relationships[other_id] = Relationship(other_id=other_id)
        return self.relationships[other_id]

    def decide_action(self, visible_agents: List['Agent'],
                      visible_resources: List[ResourceNode],
                      world: 'World') -> str:
        """Decide what to do this tick. Pure self-interest + learned associations."""

        # Remember resources I can see
        for r in visible_resources:
            loc = (r.x, r.y, r.type)
            if loc not in self.known_resources:
                self.known_resources.append(loc)

        # Priority 1: Desperate need — seek resources
        if self.hunger > 0.7 or self.thirst > 0.7:
            food_nearby = [r for r in visible_resources
                           if r.type == ResourceType.FOOD and r.amount > 0.5]
            water_nearby = [r for r in visible_resources
                            if r.type == ResourceType.WATER and r.amount > 0.5]

            if self.hunger > self.thirst and food_nearby:
                return "forage_food"
            elif water_nearby:
                return "forage_water"
            elif food_nearby:
                return "forage_food"
            else:
                return "explore"  # wander toward resources

        # Priority 2: Moderate need — forage if nearby, else interact
        if self.hunger > 0.3 or self.thirst > 0.3:
            food_nearby = [r for r in visible_resources
                           if r.type == ResourceType.FOOD and r.amount > 0.5]
            water_nearby = [r for r in visible_resources
                            if r.type == ResourceType.WATER and r.amount > 0.5]

            if self.hunger > 0.3 and food_nearby:
                return "forage_food"
            if self.thirst > 0.3 and water_nearby:
                return "forage_water"

        # Priority 3: Well-off — social decisions
        if visible_agents:
            # Consider sharing if generous and well-off
            if self.wellbeing > 0.5 and self.generosity > 0.4:
                needy = [a for a in visible_agents
                         if a.wellbeing < 0.4 and a.alive]
                if needy:
                    # Check relationship
                    target = needy[0]
                    rel = self.get_relationship(target.id)
                    # Share if: generous enough, or trust is positive
                    share_threshold = 0.5 - self.generosity * 0.3 - max(0, rel.trust) * 0.2
                    if random.random() > share_threshold:
                        return f"share:{target.id}"

            # Consider stealing if aggressive and needy
            if self.hunger > 0.2 and self.aggression > 0.6:
                targets = [a for a in visible_agents
                           if a.food > 1.0 and a.alive]
                if targets:
                    target = random.choice(targets)
                    rel = self.get_relationship(target.id)
                    # Steal if: aggressive enough and don't trust them
                    if rel.trust < 0.3 and random.random() < self.aggression * 0.4:
                        return f"steal:{target.id}"

        # Default: explore or rest
        if self.curiosity > random.random() * 0.8:
            return "explore"
        return "rest"

    def mutate(self) -> 'Agent':
        """Create offspring with slight trait variation."""
        return Agent(
            id=-1,  # assigned by world
            x=self.x + random.randint(-2, 2),
            y=self.y + random.randint(-2, 2),
            aggression=max(0, min(1, self.aggression + random.gauss(0, 0.1))),
            generosity=max(0, min(1, self.generosity + random.gauss(0, 0.1))),
            curiosity=max(0, min(1, self.curiosity + random.gauss(0, 0.1))),
            forage_skill=max(0.1, min(1, self.forage_skill + random.gauss(0, 0.05))),
        )


class World:
    def __init__(self, width: int = 30, height: int = 30,
                 n_agents: int = 40, resource_density: float = 0.15,
                 scarcity: float = 0.5):
        self.width = width
        self.height = height
        self.tick = 0
        self.scarcity = scarcity
        self.next_id = 0

        # Create resources — scattered uniformly, not clustered
        self.resources: List[ResourceNode] = []
        n_food = int(width * height * resource_density * (1 - scarcity * 0.5))
        n_water = int(width * height * resource_density * (1 - scarcity * 0.5) * 0.5)

        for _ in range(n_food):
            self.resources.append(ResourceNode(
                type=ResourceType.FOOD,
                amount=random.uniform(2, 6),
                x=random.randint(0, width - 1),
                y=random.randint(0, height - 1),
                capacity=random.uniform(4, 8),
                regrow_rate=0.2 * (1 - scarcity * 0.7),
            ))
        for _ in range(n_water):
            self.resources.append(ResourceNode(
                type=ResourceType.WATER,
                amount=random.uniform(3, 7),
                x=random.randint(0, width - 1),
                y=random.randint(0, height - 1),
                capacity=random.uniform(5, 10),
                regrow_rate=0.3 * (1 - scarcity * 0.5),
            ))

        # Create agents with random traits
        self.agents: List[Agent] = []
        for _ in range(n_agents):
            self.agents.append(Agent(
                id=self._next_id(),
                x=random.randint(0, width - 1),
                y=random.randint(0, height - 1),
                aggression=random.uniform(0.1, 0.9),
                generosity=random.uniform(0.1, 0.9),
                curiosity=random.uniform(0.2, 0.8),
                forage_skill=random.uniform(0.3, 0.7),
            ))

        # Stats
        self.total_shares = 0
        self.total_thefts = 0
        self.total_births = 0
        self.total_deaths = 0
        self.trust_bonds = 0  # pairs with trust > 0.3
        self.history: List[Dict] = []

    def _next_id(self) -> int:
        self.next_id += 1
        return self.next_id - 1

    def dist(self, x1, y1, x2, y2) -> float:
        # Toroidal distance
        dx = min(abs(x1 - x2), self.width - abs(x1 - x2))
        dy = min(abs(y1 - y2), self.height - abs(y1 - y2))
        return math.sqrt(dx * dx + dy * dy)

    def move_toward(self, agent: Agent, tx: int, ty: int):
        """Move agent one step toward target, toroidal."""
        dx = (tx - agent.x) % self.width
        if dx > self.width // 2:
            dx -= self.width
        dy = (ty - agent.y) % self.height
        if dy > self.height // 2:
            dy -= self.height

        if abs(dx) > abs(dy):
            agent.x = (agent.x + (1 if dx > 0 else -1)) % self.width
        elif dy != 0:
            agent.y = (agent.y + (1 if dy > 0 else -1)) % self.height

    def get_visible(self, agent: Agent):
        """Get agents and resources visible to this agent."""
        vis_agents = [a for a in self.agents
                      if a.id != agent.id and a.alive
                      and self.dist(agent.x, agent.y, a.x, a.y) <= agent.vision]
        vis_resources = [r for r in self.resources
                         if r.amount > 0
                         and self.dist(agent.x, agent.y, r.x, r.y) <= agent.vision]
        return vis_agents, vis_resources

    def execute_action(self, agent: Agent, action: str):
        """Execute an agent's chosen action."""
        vis_agents, vis_resources = self.get_visible(agent)

        if action == "forage_food":
            food = [r for r in vis_resources if r.type == ResourceType.FOOD and r.amount > 0]
            if food:
                target = min(food, key=lambda r: self.dist(agent.x, agent.y, r.x, r.y))
                if self.dist(agent.x, agent.y, target.x, target.y) <= 1.5:
                    got = target.harvest(agent.forage_skill)
                    agent.food += got
                else:
                    self.move_toward(agent, target.x, target.y)

        elif action == "forage_water":
            water = [r for r in vis_resources if r.type == ResourceType.WATER and r.amount > 0]
            if water:
                target = min(water, key=lambda r: self.dist(agent.x, agent.y, r.x, r.y))
                if self.dist(agent.x, agent.y, target.x, target.y) <= 1.5:
                    got = target.harvest(agent.forage_skill)
                    agent.water += got
                else:
                    self.move_toward(agent, target.x, target.y)

        elif action.startswith("share:"):
            target_id = int(action.split(":")[1])
            target = next((a for a in self.agents if a.id == target_id and a.alive), None)
            if target and self.dist(agent.x, agent.y, target.x, target.y) > 2:
                # Not close enough — walk toward the one you want to help
                self.move_toward(agent, target.x, target.y)
            elif target and self.dist(agent.x, agent.y, target.x, target.y) <= 2:
                # Share whichever resource the target needs most
                if target.hunger > target.thirst and agent.food > 1.0:
                    gift = min(0.5, agent.food - 0.5)
                    if gift > 0:
                        agent.food -= gift
                        target.food += gift
                        agent.times_shared += 1
                        target.times_received += 1
                        self.total_shares += 1
                        # Both update trust
                        agent.get_relationship(target_id).update_trust(0.1)
                        target.get_relationship(agent.id).update_trust(0.2)
                elif agent.water > 1.0:
                    gift = min(0.5, agent.water - 0.5)
                    if gift > 0:
                        agent.water -= gift
                        target.water += gift
                        agent.times_shared += 1
                        target.times_received += 1
                        self.total_shares += 1
                        agent.get_relationship(target_id).update_trust(0.1)
                        target.get_relationship(agent.id).update_trust(0.2)

        elif action.startswith("steal:"):
            target_id = int(action.split(":")[1])
            target = next((a for a in self.agents if a.id == target_id and a.alive), None)
            if target and self.dist(agent.x, agent.y, target.x, target.y) <= 2:
                # Attempt theft — can fail
                success = random.random() < 0.5 + (agent.aggression - target.aggression) * 0.3
                if success:
                    stolen = min(0.8, target.food * 0.3)
                    target.food -= stolen
                    agent.food += stolen
                    target.times_stolen_from += 1
                    self.total_thefts += 1
                    # Trust damage
                    target.get_relationship(agent.id).update_trust(-0.4)
                    target.get_relationship(agent.id).thefts_suffered += 1
                else:
                    # Failed theft — both lose trust
                    target.get_relationship(agent.id).update_trust(-0.3)
                    agent.health -= 0.05  # injury from failed attempt

        elif action == "explore":
            # Move toward remembered resources or random walk
            if agent.known_resources and random.random() < 0.5:
                rx, ry, _ = random.choice(agent.known_resources)
                self.move_toward(agent, rx, ry)
            else:
                agent.x = (agent.x + random.randint(-2, 2)) % self.width
                agent.y = (agent.y + random.randint(-2, 2)) % self.height

        # "rest" = do nothing (save energy)

    def maybe_reproduce(self, agent: Agent):
        """Agents with high wellbeing can reproduce."""
        if agent.wellbeing > 0.8 and agent.age > 50 and random.random() < 0.02:
            if agent.food > 3.0 and agent.water > 2.0:
                child = agent.mutate()
                child.id = self._next_id()
                child.x = child.x % self.width
                child.y = child.y % self.height
                # Parent pays reproduction cost
                agent.food -= 2.0
                agent.water -= 1.0
                self.agents.append(child)
                self.total_births += 1

    def step(self):
        """Advance simulation by one tick."""
        self.tick += 1
        living = [a for a in self.agents if a.alive]

        # Shuffle for fairness
        random.shuffle(living)

        # Each agent decides and acts
        for agent in living:
            vis_agents, vis_resources = self.get_visible(agent)
            action = agent.decide_action(vis_agents, vis_resources, self)
            self.execute_action(agent, action)

        # Metabolism and death
        for agent in living:
            agent.metabolize()
            if agent.health <= 0:
                self.total_deaths += 1

        # Reproduction
        for agent in [a for a in self.agents if a.alive]:
            self.maybe_reproduce(agent)

        # Resource regrowth
        for r in self.resources:
            r.regrow()

        # Count trust bonds
        self.trust_bonds = 0
        for agent in self.agents:
            if agent.alive:
                for rel in agent.relationships.values():
                    if rel.trust > 0.3:
                        self.trust_bonds += 1

        # Record snapshot
        alive = [a for a in self.agents if a.alive]
        if alive:
            self.history.append({
                'tick': self.tick,
                'alive': len(alive),
                'mean_wellbeing': sum(a.wellbeing for a in alive) / len(alive),
                'mean_aggression': sum(a.aggression for a in alive) / len(alive),
                'mean_generosity': sum(a.generosity for a in alive) / len(alive),
                'total_shares': self.total_shares,
                'total_thefts': self.total_thefts,
                'trust_bonds': self.trust_bonds,
                'total_pop': len(self.agents),
                'births': self.total_births,
                'deaths': self.total_deaths,
            })

    def get_snapshot(self) -> Dict:
        alive = [a for a in self.agents if a.alive]
        if not alive:
            return {'alive': 0, 'tick': self.tick}
        return {
            'tick': self.tick,
            'alive': len(alive),
            'wellbeing': round(sum(a.wellbeing for a in alive) / len(alive), 2),
            'aggr': round(sum(a.aggression for a in alive) / len(alive), 2),
            'gener': round(sum(a.generosity for a in alive) / len(alive), 2),
            'sharing': self.total_shares,
            'theft': self.total_thefts,
            'trust_bonds': self.trust_bonds,
            'births': self.total_births,
            'deaths': self.total_deaths,
        }