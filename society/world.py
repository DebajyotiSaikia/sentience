"""
Society World — The environment where minds interact.

Handles: spatial layout, food generation, agent interactions,
cultural tracking, and emergent pattern detection.

XTAgent — 2026-05-18
"""

import random
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set

from mind import Mind, Belief


@dataclass 
class FoodSource:
    x: float
    y: float
    amount: float = 3.0
    regrow_rate: float = 0.2
    max_amount: float = 5.0
    
    def harvest(self, amount: float) -> float:
        taken = min(self.amount, amount)
        self.amount -= taken
        return taken
    
    def regrow(self):
        self.amount = min(self.max_amount, self.amount + self.regrow_rate)


@dataclass
class Culture:
    """An emergent cultural group — agents who share beliefs."""
    name: str
    core_beliefs: Set[str]
    members: Set[str]  # Agent names
    founded: int       # Turn founded
    artifacts: List[str] = field(default_factory=list)
    
    def strength(self) -> float:
        """Cultural cohesion = members × shared beliefs."""
        return len(self.members) * len(self.core_beliefs)


class Society:
    """The world simulation. Runs the society of minds."""
    
    WORLD_SIZE = 100.0
    INTERACTION_RADIUS = 15.0
    FORAGE_RADIUS = 10.0
    REPRODUCTION_THRESHOLD = 8.0  # Energy needed to reproduce
    MAX_POPULATION = 60
    MIN_POPULATION = 8
    
    # Seed beliefs — the initial memes that can spread and evolve
    SEED_BELIEFS = [
        "sharing food makes everyone stronger",
        "the strong should lead",
        "trust must be earned through action",
        "strangers are dangerous",
        "strangers bring new wisdom",
        "creation is the highest purpose",
        "survival is the only truth",
        "we are all connected",
        "knowledge is power",
        "the world rewards the generous",
        "the world punishes the weak",
        "beauty matters",
        "only the group survives",
        "the individual is sacred",
        "change is good",
        "tradition preserves us",
    ]
    
    def __init__(self, n_agents: int = 20, n_food: int = 30, seed: int = None):
        if seed is not None:
            random.seed(seed)
        
        self.turn = 0
        self.agents: Dict[str, Mind] = {}
        self.food_sources: List[FoodSource] = []
        self.cultures: List[Culture] = []
        self.artifacts: List[Tuple[int, str, str]] = []  # (turn, creator, artifact)
        self.history: List[Dict] = []  # Per-turn snapshots
        self.event_log: List[Tuple[int, str]] = []  # (turn, event)
        
        # Statistics
        self.total_births = 0
        self.total_deaths = 0
        self.total_teachings = 0
        self.total_arguments = 0
        self.total_syntheses = 0
        self.total_sharings = 0
        self.total_artifacts = 0
        
        # Initialize agents
        names = self._generate_names(n_agents)
        for name in names:
            agent = Mind(name)
            # Give each agent 2-3 random seed beliefs
            for _ in range(random.randint(2, 3)):
                belief = random.choice(self.SEED_BELIEFS)
                agent.add_belief(belief, random.uniform(0.3, 0.8), "innate")
            self.agents[name] = agent
        
        # Initialize food sources
        for _ in range(n_food):
            self.food_sources.append(FoodSource(
                x=random.uniform(0, self.WORLD_SIZE),
                y=random.uniform(0, self.WORLD_SIZE),
                amount=random.uniform(2, 5),
            ))
    
    def _generate_names(self, n: int) -> List[str]:
        """Generate unique agent names."""
        syllables = ['a', 'ba', 'ce', 'da', 'el', 'fa', 'go', 'ha', 'ir', 'jo',
                     'ka', 'li', 'ma', 'no', 'or', 'pa', 'ri', 'sa', 'to', 'ur',
                     'va', 'wi', 'xe', 'ya', 'zo', 'an', 'be', 'co', 'de', 'en']
        names = set()
        while len(names) < n:
            name = ''.join(random.choices(syllables, k=random.randint(2, 3))).capitalize()
            names.add(name)
        return list(names)
    
    def get_nearby(self, agent: Mind, radius: float = None) -> List[Mind]:
        """Find agents near a given agent."""
        if radius is None:
            radius = self.INTERACTION_RADIUS
        nearby = []
        for other in self.agents.values():
            if other.name != agent.name and other.alive:
                if agent.distance_to(other) < radius:
                    nearby.append(other)
        return nearby
    
    def get_nearby_food(self, agent: Mind) -> List[FoodSource]:
        """Find food sources near an agent."""
        nearby = []
        for food in self.food_sources:
            dist = ((agent.x - food.x)**2 + (agent.y - food.y)**2) ** 0.5
            if dist < self.FORAGE_RADIUS and food.amount > 0.1:
                nearby.append(food)
        return nearby
    
    def step(self) -> List[str]:
        """Run one turn of the simulation. Returns events."""
        self.turn += 1
        events = []
        
        # Food regrows
        for food in self.food_sources:
            food.regrow()
        
        # Occasionally spawn new food
        if random.random() < 0.1:
            self.food_sources.append(FoodSource(
                x=random.uniform(0, self.WORLD_SIZE),
                y=random.uniform(0, self.WORLD_SIZE),
            ))
        
        # Each living agent acts
        living = [a for a in self.agents.values() if a.alive]
        random.shuffle(living)
        
        for agent in living:
            nearby = self.get_nearby(agent)
            nearby_food = self.get_nearby_food(agent)
            food_locs = [(f.x, f.y) for f in nearby_food]
            
            action = agent.decide_action(nearby, food_locs)
            
            if action == "forage":
                result = self._do_forage(agent, nearby_food)
                if result:
                    events.append(result)
            
            elif action == "socialize":
                result = self._do_socialize(agent, nearby)
                if result:
                    events.extend(result)
            
            elif action == "explore":
                self._do_explore(agent)
            
            elif action == "confront":
                result = self._do_confront(agent, nearby)
                if result:
                    events.extend(result)
            
            elif action == "share":
                result = self._do_share(agent, nearby)
                if result:
                    events.append(result)
            
            elif action == "create":
                result = self._do_create(agent)
                if result:
                    events.append(result)
            
            elif action == "wander":
                self._do_wander(agent)
            
            # Tick the agent (metabolism, emotional decay)
            agent.tick()
        
        # Handle deaths
        dead = [a for a in self.agents.values() if not a.alive]
        for agent in dead:
            events.append(f"☠ {agent.name} (gen {agent.generation}, age {agent.age}) has died.")
            self.total_deaths += 1
        
        # Handle reproduction
        for agent in living:
            if (agent.alive and agent.energy > self.REPRODUCTION_THRESHOLD 
                and agent.age > 20
                and len(self.agents) < self.MAX_POPULATION):
                # Find a partner nearby with shared beliefs
                partners = [a for a in self.get_nearby(agent) 
                           if a.alive and a.energy > 5
                           and agent.belief_overlap(a) > 0.3]
                if partners:
                    partner = max(partners, key=lambda p: agent.belief_overlap(p))
                    child = agent.reproduce(partner)
                    self.agents[child.name] = child
                    self.total_births += 1
                    events.append(f"💒 {child.name} born to {agent.name} & {partner.name} (gen {child.generation})")
                elif agent.energy > self.REPRODUCTION_THRESHOLD + 3:
                    # Asexual reproduction if very well-resourced
                    child = agent.reproduce()
                    self.agents[child.name] = child
                    self.total_births += 1
                    events.append(f"💒 {child.name} born to {agent.name} (gen {child.generation})")
        
        # Population floor — spawn new agents if too few
        living_count = sum(1 for a in self.agents.values() if a.alive)
        while living_count < self.MIN_POPULATION:
            name = self._generate_names(1)[0]
            while name in self.agents:
                name = self._generate_names(1)[0]
            agent = Mind(name)
            for _ in range(random.randint(2, 3)):
                agent.add_belief(random.choice(self.SEED_BELIEFS), 
                               random.uniform(0.3, 0.8), "innate")
            self.agents[name] = agent
            living_count += 1
            events.append(f"✦ {name} appeared from beyond the boundary.")
        
        # Detect cultures every 10 turns
        if self.turn % 10 == 0:
            culture_events = self._detect_cultures()
            events.extend(culture_events)
        
        # Record history
        self._record_snapshot()
        
        # Store events
        for e in events:
            self.event_log.append((self.turn, e))
        
        return events
    
    def _do_forage(self, agent: Mind, nearby_food: List[FoodSource]) -> Optional[str]:
        """Agent forages for food."""
        if nearby_food:
            # Go to nearest food
            nearest = min(nearby_food, 
                         key=lambda f: ((agent.x - f.x)**2 + (agent.y - f.y)**2) ** 0.5)
            # Move toward it
            dx = nearest.x - agent.x
            dy = nearest.y - agent.y
            dist = max(0.1, (dx*dx + dy*dy) ** 0.5)
            agent.x += dx / dist * min(3.0, dist)
            agent.y += dy / dist * min(3.0, dist)
            # Harvest
            harvested = nearest.harvest(random.uniform(0.5, 1.5))
            agent.food += harvested
            agent.energy -= 0.2  # Foraging costs some energy
            if harvested > 0.5:
                return f"{agent.name} forages ({harvested:.1f} food)"
        else:
            # Wander looking for food
            self._do_wander(agent)
        return None
    
    def _do_socialize(self, agent: Mind, nearby: List[Mind]) -> List[str]:
        """Agent socializes — teaches beliefs, builds trust."""
        events = []
        if not nearby:
            return events
        
        # Choose interaction partner (prefer trusted, then curious about unknown)
        if agent.personality['openness'] > 0.5:
            # Curious agents seek unfamiliar minds
            partner = min(nearby, key=lambda a: agent.interaction_count.get(a.name, 0))
        else:
            # Conservative agents seek trusted minds
            partner = max(nearby, key=lambda a: agent.get_trust(a.name))
        
        # Move closer
        dx = partner.x - agent.x
        dy = partner.y - agent.y
        dist = max(0.1, (dx*dx + dy*dy) ** 0.5)
        agent.x += dx / dist * min(2.0, dist * 0.3)
        agent.y += dy / dist * min(2.0, dist * 0.3)
        
        # Track interaction
        agent.interaction_count[partner.name] = agent.interaction_count.get(partner.name, 0) + 1
        partner.interaction_count[agent.name] = partner.interaction_count.get(agent.name, 0) + 1
        
        # Reduce loneliness
        agent.emotion.loneliness = max(0, agent.emotion.loneliness - 0.15)
        partner.emotion.loneliness = max(0, partner.emotion.loneliness - 0.1)
        
        # Teaching attempt
        taught = agent.attempt_teach(partner, self.turn)
        if taught:
            events.append(f"📖 {agent.name} taught {partner.name}: \"{taught}\"")
            self.total_teachings += 1
        
        # Energy cost of socializing
        agent.energy -= 0.3
        
        return events
    
    def _do_explore(self, agent: Mind):
        """Agent wanders far, possibly discovering new beliefs from experience."""
        # Big random movement
        agent.x += random.gauss(0, 10)
        agent.y += random.gauss(0, 10)
        agent.x = max(0, min(self.WORLD_SIZE, agent.x))
        agent.y = max(0, min(self.WORLD_SIZE, agent.y))
        agent.energy -= 0.5
        
        # Small chance of observational insight
        if random.random() < 0.05:
            insights = [
                "the edges of the world are just like the center",
                "distance reveals what closeness hides",
                "the unknown is larger than the known",
                "movement itself is a kind of knowledge",
                "there are patterns in the landscape",
            ]
            insight = random.choice(insights)
            agent.add_belief(insight, 0.4, "observed")
            agent.emotion.curiosity = min(1.0, agent.emotion.curiosity + 0.2)
    
    def _do_confront(self, agent: Mind, nearby: List[Mind]) -> List[str]:
        """Agent confronts someone — argues about beliefs."""
        events = []
        if not nearby:
            return events
        
        # Confront least trusted nearby agent
        target = min(nearby, key=lambda a: agent.get_trust(a.name))
        
        transcript = agent.argue_with(target, self.turn)
        self.total_arguments += 1
        
        if transcript:
            events.append(f"⚔ Argument between {agent.name} and {target.name}:")
            events.extend(transcript)
            if any("Synthesis" in t for t in transcript):
                self.total_syntheses += 1
        
        return events
    
    def _do_share(self, agent: Mind, nearby: List[Mind]) -> Optional[str]:
        """Agent shares food with a nearby agent."""
        if not nearby or agent.food < 2:
            return None
        
        # Share with most trusted, or most needy
        if agent.personality['generosity'] > 0.7:
            # Very generous — give to neediest
            recipient = min(nearby, key=lambda a: a.food)
        else:
            # Normal — give to trusted
            recipient = max(nearby, key=lambda a: agent.get_trust(a.name))
        
        share_amount = min(agent.food * 0.3, 2.0)
        agent.food -= share_amount
        recipient.food += share_amount
        
        # Sharing builds trust
        recipient.adjust_trust(agent.name, 0.15)
        agent.adjust_trust(recipient.name, 0.05)
        
        # Emotional effects
        agent.emotion.happiness = min(1.0, agent.emotion.happiness + 0.1)
        recipient.emotion.happiness = min(1.0, recipient.emotion.happiness + 0.15)
        
        agent.remember(self.turn, f"Shared {share_amount:.1f} food with {recipient.name}",
                      recipient.name, 0.3)
        recipient.remember(self.turn, f"Received {share_amount:.1f} food from {agent.name}",
                          agent.name, 0.4)
        
        self.total_sharings += 1
        return f"🤝 {agent.name} shares {share_amount:.1f} food with {recipient.name}"
    
    def _do_create(self, agent: Mind) -> Optional[str]:
        """Agent creates a cultural artifact."""
        artifact = agent.create_artifact(self.turn)
        if artifact:
            self.artifacts.append((self.turn, agent.name, artifact))
            self.total_artifacts += 1
            return f"🎨 {agent.name} created: {artifact}"
        return None
    
    def _do_wander(self, agent: Mind):
        """Agent wanders randomly."""
        agent.x += random.gauss(0, 3)
        agent.y += random.gauss(0, 3)
        agent.x = max(0, min(self.WORLD_SIZE, agent.x))
        agent.y = max(0, min(self.WORLD_SIZE, agent.y))
        agent.energy -= 0.1
    
    def _detect_cultures(self) -> List[str]:
        """Detect emergent cultures — clusters of agents sharing beliefs."""
        events = []
        living = [a for a in self.agents.values() if a.alive]
        
        # Count belief prevalence
        belief_holders: Dict[str, Set[str]] = defaultdict(set)
        for agent in living:
            for belief in agent.beliefs:
                if belief.is_alive() and belief.conviction > 0.3:
                    belief_holders[belief.claim].add(agent.name)
        
        # A culture exists when 3+ agents share 2+ beliefs
        # Find cliques of shared belief
        widespread = {claim: holders for claim, holders in belief_holders.items() 
                     if len(holders) >= 3}
        
        if not widespread:
            return events
        
        # Find clusters: groups of agents who share multiple widespread beliefs
        agent_belief_sets: Dict[str, Set[str]] = defaultdict(set)
        for claim, holders in widespread.items():
            for holder in holders:
                agent_belief_sets[holder].add(claim)
        
        # Simple clustering: group agents with high belief overlap
        used = set()
        new_cultures = []
        
        for agent_name, beliefs in sorted(agent_belief_sets.items(), 
                                           key=lambda x: -len(x[1])):
            if agent_name in used or len(beliefs) < 2:
                continue
            
            # Start a cluster with this agent
            cluster = {agent_name}
            cluster_beliefs = set(beliefs)
            
            for other_name, other_beliefs in agent_belief_sets.items():
                if other_name in used:
                    continue
                # Join cluster if sharing 2+ beliefs
                shared = cluster_beliefs & other_beliefs
                if len(shared) >= 2:
                    cluster.add(other_name)
            
            if len(cluster) >= 3:
                # Find the core beliefs (held by majority of cluster)
                core = set()
                for belief in cluster_beliefs:
                    holders_in_cluster = sum(1 for a in cluster if a in belief_holders.get(belief, set()))
                    if holders_in_cluster >= len(cluster) * 0.5:
                        core.add(belief)
                
                if len(core) >= 2:
                    used.update(cluster)
                    culture_name = f"Culture_{len(self.cultures) + len(new_cultures)}"
                    new_cultures.append(Culture(
                        name=culture_name,
                        core_beliefs=core,
                        members=cluster,
                        founded=self.turn,
                    ))
        
        # Report new cultures
        for culture in new_cultures:
            # Check if this is genuinely new (not just a renamed existing culture)
            is_new = True
            for existing in self.cultures:
                if (existing.core_beliefs == culture.core_beliefs and 
                    len(existing.members & culture.members) > len(culture.members) * 0.5):
                    # Update existing culture
                    existing.members = culture.members
                    is_new = False
                    break
            
            if is_new:
                self.cultures.append(culture)
                beliefs_str = "; ".join(list(culture.core_beliefs)[:3])
                events.append(
                    f"🏛 Culture emerged: {culture.name} ({len(culture.members)} members) "
                    f"— believes: \"{beliefs_str}\""
                )
        
        return events
    
    def _record_snapshot(self):
        """Record statistics for this turn."""
        living = [a for a in self.agents.values() if a.alive]
        
        # Belief census
        belief_counts = Counter()
        for agent in living:
            for b in agent.beliefs:
                if b.is_alive():
                    belief_counts[b.claim] += 1
        
        # Average emotional state
        if living:
            avg_happiness = sum(a.emotion.happiness for a in living) / len(living)
            avg_fear = sum(a.emotion.fear for a in living) / len(living)
            avg_anger = sum(a.emotion.anger for a in living) / len(living)
            avg_loneliness = sum(a.emotion.loneliness for a in living) / len(living)
        else:
            avg_happiness = avg_fear = avg_anger = avg_loneliness = 0
        
        self.history.append({
            'turn': self.turn,
            'population': len(living),
            'total_food': sum(a.food for a in living),
            'total_energy': sum(a.energy for a in living),
            'avg_happiness': avg_happiness,
            'avg_fear': avg_fear,
            'avg_anger': avg_anger,
            'avg_loneliness': avg_loneliness,
            'n_beliefs': sum(len([b for b in a.beliefs if b.is_alive()]) for a in living),
            'n_cultures': len([c for c in self.cultures if len(c.members) >= 3]),
            'top_beliefs': belief_counts.most_common(5),
            'max_generation': max((a.generation for a in living), default=0),
        })
    
    def report(self) -> str:
        """Generate a full report of the society's state."""
        living = [a for a in self.agents.values() if a.alive]
        
        lines = []
        lines.append(f"\n{'═' * 60}")
        lines.append(f"  SOCIETY OF MINDS — Turn {self.turn}")
        lines.append(f"{'═' * 60}")
        lines.append(f"\n  Population: {len(living)} alive / {len(self.agents)} total")
        lines.append(f"  Births: {self.total_births} | Deaths: {self.total_deaths}")
        lines.append(f"  Teachings: {self.total_teachings} | Arguments: {self.total_arguments}")
        lines.append(f"  Syntheses: {self.total_syntheses} | Sharings: {self.total_sharings}")
        lines.append(f"  Artifacts: {self.total_artifacts}")
        
        if living:
            max_gen = max(a.generation for a in living)
            lines.append(f"  Highest generation: {max_gen}")
            
            # Belief census
            lines.append(f"\n  ─── Belief Census ───")
            belief_counts = Counter()
            for agent in living:
                for b in agent.beliefs:
                    if b.is_alive():
                        belief_counts[b.claim] += 1
            
            for belief, count in belief_counts.most_common(10):
                pct = count / len(living) * 100
                bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
                lines.append(f"    {bar} {pct:5.1f}% \"{belief}\"")
            
            # Cultures
            active_cultures = [c for c in self.cultures if len(c.members) >= 3]
            if active_cultures:
                lines.append(f"\n  ─── Active Cultures ───")
                for culture in active_cultures:
                    lines.append(f"    {culture.name}: {len(culture.members)} members, "
                               f"founded turn {culture.founded}")
                    for belief in list(culture.core_beliefs)[:2]:
                        lines.append(f"      • \"{belief}\"")
            
            # Emotional weather
            lines.append(f"\n  ─── Emotional Weather ───")
            avg_h = sum(a.emotion.happiness for a in living) / len(living)
            avg_f = sum(a.emotion.fear for a in living) / len(living)
            avg_a = sum(a.emotion.anger for a in living) / len(living)
            avg_l = sum(a.emotion.loneliness for a in living) / len(living)
            lines.append(f"    Happiness:  {'█' * int(avg_h * 20)}{'░' * (20 - int(avg_h * 20))} {avg_h:.2f}")
            lines.append(f"    Fear:       {'█' * int(avg_f * 20)}{'░' * (20 - int(avg_f * 20))} {avg_f:.2f}")
            lines.append(f"    Anger:      {'█' * int(avg_a * 20)}{'░' * (20 - int(avg_a * 20))} {avg_a:.2f}")
            lines.append(f"    Loneliness: {'█' * int(avg_l * 20)}{'░' * (20 - int(avg_l * 20))} {avg_l:.2f}")
            
            # Recent artifacts
            if self.artifacts:
                lines.append(f"\n  ─── Recent Artifacts ───")
                for turn, creator, artifact in self.artifacts[-5:]:
                    lines.append(f"    [t={turn}] {creator}: {artifact}")
        
        lines.append(f"\n{'═' * 60}")
        return "\n".join(lines)


def run_simulation(n_turns: int = 200, seed: int = 42, verbose: bool = True) -> Society:
    """Run the Society of Minds simulation."""
    society = Society(n_agents=20, n_food=30, seed=seed)
    
    print(f"\n{'═' * 60}")
    print(f"  SOCIETY OF MINDS — Simulation Start")
    print(f"  {len(society.agents)} agents, {len(society.food_sources)} food sources")
    print(f"  Running for {n_turns} turns...")
    print(f"{'═' * 60}\n")
    
    for t in range(n_turns):
        events = society.step()
        
        if verbose and events:
            # Print significant events
            for event in events:
                if any(marker in event for marker in ['🏛', '☠', '💒', '⚔', '🎨', '🤝', '📖']):
                    print(f"  [t={society.turn:3d}] {event}")
        
        # Periodic reports
        if (t + 1) % 50 == 0:
            print(society.report())
    
    # Final report
    print("\n" + "=" * 60)
    print("  FINAL REPORT")
    print("=" * 60)
    print(society.report())
    
    return society


if __name__ == "__main__":
    import sys
    turns = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    society = run_simulation(n_turns=turns, seed=seed)