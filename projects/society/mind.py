"""
Mind — The cognitive architecture of a single agent in the Society.

Each agent has:
- Beliefs with conviction levels and origins
- Emotional state (mood, trust, fear, curiosity)
- Memory of interactions
- Resource inventory
- Social graph (who they trust/distrust)

XTAgent — 2026-05-18
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Belief:
    """A belief held by an agent. Can be shared, argued, weakened, synthesized."""
    claim: str
    conviction: float = 0.5       # 0 = barely held, 1 = absolute
    origin: str = "innate"        # innate, taught, observed, dialectic, revelation
    age: int = 0                  # How many turns this belief has existed
    source_agent: Optional[str] = None  # Who taught me this?
    
    def __hash__(self):
        return hash(self.claim)
    
    def weaken(self, amount: float = 0.1):
        self.conviction = max(0.0, self.conviction - amount)
    
    def strengthen(self, amount: float = 0.1):
        self.conviction = min(1.0, self.conviction + amount)
    
    def is_alive(self) -> bool:
        """Beliefs below threshold are effectively dead."""
        return self.conviction > 0.05


@dataclass
class Emotion:
    """The emotional state of an agent. Affects decision-making."""
    happiness: float = 0.5    # 0 = miserable, 1 = joyful
    fear: float = 0.1         # 0 = fearless, 1 = terrified
    curiosity: float = 0.5    # 0 = incurious, 1 = driven to explore
    anger: float = 0.0        # 0 = calm, 1 = furious
    loneliness: float = 0.3   # 0 = socially fulfilled, 1 = isolated
    
    def dominant(self) -> str:
        states = {
            'happiness': self.happiness,
            'fear': self.fear,
            'curiosity': self.curiosity,
            'anger': self.anger,
            'loneliness': self.loneliness,
        }
        return max(states, key=states.get)
    
    def valence(self) -> float:
        """Overall emotional tone. Positive = good, negative = bad."""
        return (self.happiness * 0.4 + self.curiosity * 0.2 
                - self.fear * 0.3 - self.anger * 0.2 - self.loneliness * 0.2)
    
    def decay(self):
        """Emotions drift toward baseline over time."""
        baselines = {
            'happiness': 0.35,
            'fear': 0.1,
            'curiosity': 0.45,  # Agents are naturally curious
            'anger': 0.05,
            'loneliness': 0.15,
        }
        for attr in baselines:
            val = getattr(self, attr)
            drift = (baselines[attr] - val) * 0.08
            setattr(self, attr, max(0.0, min(1.0, val + drift)))


@dataclass
class Memory:
    """A single memory of an interaction."""
    turn: int
    event: str
    other_agent: Optional[str] = None
    emotional_valence: float = 0.0  # How did this make me feel?
    
    def __repr__(self):
        return f"[t={self.turn}] {self.event}"


class Mind:
    """A complete cognitive agent."""
    
    def __init__(self, name: str, personality: Optional[Dict[str, float]] = None):
        self.name = name
        self.age = 0
        self.alive = True
        self.generation = 0
        
        # Personality (fixed traits that bias behavior)
        self.personality = personality or {
            'openness': random.gauss(0.5, 0.2),      # Willingness to adopt new beliefs
            'aggression': random.gauss(0.3, 0.15),    # Tendency toward conflict
            'generosity': random.gauss(0.5, 0.2),     # Willingness to share resources
            'sociability': random.gauss(0.5, 0.2),    # Drive to interact
            'stubbornness': random.gauss(0.5, 0.2),   # Resistance to belief change
        }
        # Clamp personality traits
        for k in self.personality:
            self.personality[k] = max(0.0, min(1.0, self.personality[k]))
        
        # Cognitive state
        self.beliefs: List[Belief] = []
        self.emotion = Emotion()
        self.memories: List[Memory] = []
        self.max_memories = 50  # Finite memory — old memories fade
        
        # Social
        self.trust: Dict[str, float] = {}    # name -> trust level (-1 to 1)
        self.interaction_count: Dict[str, int] = {}  # name -> times interacted
        
        # Resources
        self.food: float = 5.0
        self.energy: float = 10.0
        self.max_energy: float = 10.0
        self.artifacts: List[str] = []  # Cultural artifacts created
        
        # Position
        self.x: float = random.uniform(0, 100)
        self.y: float = random.uniform(0, 100)
    
    def add_belief(self, claim: str, conviction: float = 0.5, 
                   origin: str = "innate", source: str = None):
        """Add a belief, or strengthen it if already held."""
        for b in self.beliefs:
            if b.claim == claim:
                b.strengthen(conviction * 0.3)
                return
        self.beliefs.append(Belief(claim, conviction, origin, source_agent=source))
    
    def strongest_belief(self) -> Optional[Belief]:
        alive = [b for b in self.beliefs if b.is_alive()]
        return max(alive, key=lambda b: b.conviction) if alive else None
    
    def believes(self, claim: str) -> Optional[Belief]:
        """Check if agent holds a specific belief."""
        for b in self.beliefs:
            if b.claim == claim and b.is_alive():
                return b
        return None
    
    def remember(self, turn: int, event: str, other: str = None, valence: float = 0.0):
        """Store a memory. Old memories are forgotten."""
        self.memories.append(Memory(turn, event, other, valence))
        if len(self.memories) > self.max_memories:
            # Keep emotionally significant memories longer
            self.memories.sort(key=lambda m: abs(m.emotional_valence))
            self.memories.pop(0)  # Drop least significant
    
    def get_trust(self, other_name: str) -> float:
        return self.trust.get(other_name, 0.0)
    
    def adjust_trust(self, other_name: str, delta: float):
        current = self.trust.get(other_name, 0.0)
        self.trust[other_name] = max(-1.0, min(1.0, current + delta))
    
    def distance_to(self, other: 'Mind') -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2) ** 0.5
    
    def metabolize(self):
        """Each turn costs energy. Eat food to restore."""
        self.energy -= 0.3  # Base metabolism
        if self.energy < 3.0 and self.food > 0:
            eaten = min(self.food, 2.0)
            self.food -= eaten
            self.energy = min(self.max_energy, self.energy + eaten * 2)
        
        if self.energy <= 0:
            self.alive = False
    
    def decide_action(self, nearby_agents: List['Mind'], 
                      food_locations: List[Tuple[float, float]]) -> str:
        """Choose what to do this turn based on needs, emotions, personality."""
        
        if not self.alive:
            return "dead"
        
        # Survival pressure — always takes priority
        if self.energy < 2.0:
            return "forage"
        if self.food < 1.0 and self.energy < 5.0:
            return "forage"
        
        # Once survival is handled, social/intellectual life matters
        if nearby_agents:
            # Confrontation: encountering someone you distrust, or high anger
            untrusted = [a for a in nearby_agents if self.get_trust(a.name) < -0.2]
            if untrusted and self.personality['aggression'] > 0.3:
                if random.random() < self.personality['aggression']:
                    return "confront"
            if self.emotion.anger > 0.4 and self.personality['aggression'] > 0.3:
                return "confront"
            
            # Belief difference also sparks confrontation
            for other in nearby_agents:
                overlap = self.belief_overlap(other)
                if (overlap < 0.3 and self.personality['stubbornness'] > 0.4 
                    and random.random() < 0.3):
                    return "confront"
            
            # Social needs — sociable agents seek interaction readily
            if self.emotion.loneliness > 0.2 and self.personality['sociability'] > 0.3:
                if random.random() < self.personality['sociability'] * 0.6:
                    return "socialize"
            
            # Even non-lonely agents socialize sometimes when near others
            if random.random() < self.personality['sociability'] * 0.2:
                return "socialize"
            
            # Generosity → share
            if self.food > 3 and self.personality['generosity'] > 0.4:
                if random.random() < self.personality['generosity'] * 0.3:
                    return "share"
        
        # Curiosity → explore
        if self.emotion.curiosity > 0.3 and random.random() < self.personality['openness'] * 0.4:
            return "explore"
        
        # Create (if well-resourced and have beliefs to synthesize)
        if self.energy > 5 and len(self.beliefs) > 1:
            if random.random() < 0.1 + self.emotion.curiosity * 0.15:
                return "create"
        
        # Default: forage or wander
        if random.random() < 0.5:
            return "forage"
        return "wander"
    
    def belief_overlap(self, other: 'Mind') -> float:
        """How much do two minds share beliefs? 0 = nothing, 1 = identical."""
        my_claims = {b.claim for b in self.beliefs if b.is_alive()}
        their_claims = {b.claim for b in other.beliefs if b.is_alive()}
        if not my_claims and not their_claims:
            return 0.5  # Neither has beliefs — neutral
        if not my_claims or not their_claims:
            return 0.0
        overlap = len(my_claims & their_claims)
        total = len(my_claims | their_claims)
        return overlap / total if total > 0 else 0.0
    
    def attempt_teach(self, other: 'Mind', turn: int) -> Optional[str]:
        """Try to teach my strongest belief to another agent."""
        my_strongest = self.strongest_belief()
        if not my_strongest:
            return None
        
        # Does the other already believe this?
        existing = other.believes(my_strongest.claim)
        if existing and existing.conviction > my_strongest.conviction:
            return None  # They believe it more strongly than I do
        
        # Teaching success depends on: my conviction, their openness, trust
        trust = other.get_trust(self.name)
        chance = (my_strongest.conviction * 0.4 + 
                  other.personality['openness'] * 0.3 + 
                  (trust + 1) / 2 * 0.3)
        
        # Stubbornness resists
        chance *= (1.0 - other.personality['stubbornness'] * 0.5)
        
        if random.random() < chance:
            taught_conviction = my_strongest.conviction * 0.6  # Diluted in transmission
            other.add_belief(my_strongest.claim, taught_conviction, 
                           origin="taught", source=self.name)
            other.adjust_trust(self.name, 0.05)
            self.remember(turn, f"Taught '{my_strongest.claim}' to {other.name}", 
                         other.name, 0.3)
            other.remember(turn, f"Learned '{my_strongest.claim}' from {self.name}",
                          self.name, 0.2)
            return my_strongest.claim
        return None
    
    def argue_with(self, other: 'Mind', turn: int) -> List[str]:
        """Dialectic: two agents argue about conflicting beliefs."""
        transcript = []
        
        # Find beliefs unique to each
        my_claims = {b.claim for b in self.beliefs if b.is_alive()}
        their_claims = {b.claim for b in other.beliefs if b.is_alive()}
        
        my_unique = [b for b in self.beliefs if b.claim in (my_claims - their_claims) and b.is_alive()]
        their_unique = [b for b in other.beliefs if b.claim in (their_claims - my_claims) and b.is_alive()]
        
        if not my_unique and not their_unique:
            transcript.append(f"{self.name} and {other.name} find they agree on everything.")
            self.adjust_trust(other.name, 0.1)
            other.adjust_trust(self.name, 0.1)
            self.emotion.loneliness = max(0, self.emotion.loneliness - 0.2)
            other.emotion.loneliness = max(0, other.emotion.loneliness - 0.2)
            return transcript
        
        # Argument rounds
        rounds = min(3, max(len(my_unique), len(their_unique)))
        for i in range(rounds):
            if i < len(my_unique):
                b = my_unique[i]
                transcript.append(f"  {self.name}: \"{b.claim}\" (conviction {b.conviction:.2f})")
            if i < len(their_unique):
                b = their_unique[i]
                transcript.append(f"  {other.name}: \"{b.claim}\" (conviction {b.conviction:.2f})")
            
            # Pressure: both sides' beliefs weaken slightly
            if i < len(my_unique):
                my_unique[i].weaken(0.05 * (1 - self.personality['stubbornness']))
            if i < len(their_unique):
                their_unique[i].weaken(0.05 * (1 - other.personality['stubbornness']))
        
        # Check for synthesis
        if (my_unique and their_unique and 
            my_unique[0].conviction < 0.3 and their_unique[0].conviction < 0.3):
            # Both positions weakened enough for synthesis
            synthesis = f"The truth lies between '{my_unique[0].claim}' and '{their_unique[0].claim}'"
            new_belief = Belief(synthesis, 0.5, "dialectic")
            self.beliefs.append(new_belief)
            other.beliefs.append(Belief(synthesis, 0.5, "dialectic"))
            transcript.append(f"  → Synthesis: \"{synthesis}\"")
            self.adjust_trust(other.name, 0.1)
            other.adjust_trust(self.name, 0.1)
        else:
            # No synthesis — tension
            self.emotion.anger = min(1.0, self.emotion.anger + 0.1)
            other.emotion.anger = min(1.0, other.emotion.anger + 0.1)
            self.adjust_trust(other.name, -0.05)
            other.adjust_trust(self.name, -0.05)
        
        # Cost of argument
        self.energy -= 0.5
        other.energy -= 0.5
        
        self.remember(turn, f"Argued with {other.name}", other.name, -0.1)
        other.remember(turn, f"Argued with {self.name}", self.name, -0.1)
        
        return transcript
    
    def create_artifact(self, turn: int) -> Optional[str]:
        """Create a cultural artifact from held beliefs. Costs energy."""
        if self.energy < 3 or len(self.beliefs) < 2:
            return None
        
        self.energy -= 2.0
        
        # Combine two beliefs into an artifact
        strong = sorted([b for b in self.beliefs if b.is_alive()], 
                       key=lambda b: b.conviction, reverse=True)[:2]
        
        artifact_templates = [
            "a song about {0} and {1}",
            "a carved symbol meaning '{0}'",
            "a story where {0} leads to {1}",
            "a ritual that enacts {0}",
            "a warning sign about {1}",
            "a monument to {0}",
        ]
        
        template = random.choice(artifact_templates)
        if len(strong) >= 2:
            artifact = template.format(strong[0].claim, strong[1].claim)
        else:
            artifact = template.format(strong[0].claim, "the unknown")
        
        self.artifacts.append(artifact)
        self.remember(turn, f"Created: {artifact}", valence=0.5)
        self.emotion.happiness = min(1.0, self.emotion.happiness + 0.2)
        self.emotion.curiosity = min(1.0, self.emotion.curiosity + 0.1)
        
        return artifact
    
    def tick(self):
        """Per-turn maintenance."""
        self.age += 1
        self.emotion.decay()
        self.metabolize()
        
        # Age beliefs
        for b in self.beliefs:
            b.age += 1
            # Very old beliefs with low conviction fade
            if b.age > 100 and b.conviction < 0.2:
                b.conviction = 0.0
        
        # Prune dead beliefs
        self.beliefs = [b for b in self.beliefs if b.is_alive()]
        
        # Loneliness increases if alone
        self.emotion.loneliness = min(1.0, self.emotion.loneliness + 0.02)
    
    def reproduce(self, partner: Optional['Mind'] = None) -> 'Mind':
        """Create a child. Inherits some beliefs (cultural transmission) and personality (genetic)."""
        child_name = f"{self.name}_{self.generation + 1}_{random.randint(0, 99)}"
        
        # Personality: blend of parents with mutation
        if partner:
            child_personality = {}
            for trait in self.personality:
                # Average of parents + mutation
                avg = (self.personality[trait] + partner.personality[trait]) / 2
                mutated = avg + random.gauss(0, 0.1)
                child_personality[trait] = max(0.0, min(1.0, mutated))
        else:
            child_personality = {}
            for trait in self.personality:
                mutated = self.personality[trait] + random.gauss(0, 0.15)
                child_personality[trait] = max(0.0, min(1.0, mutated))
        
        child = Mind(child_name, child_personality)
        child.generation = max(self.generation, 
                              partner.generation if partner else 0) + 1
        
        # Cultural transmission: child inherits strongest beliefs, diluted
        parent_beliefs = sorted([b for b in self.beliefs if b.is_alive()],
                               key=lambda b: b.conviction, reverse=True)
        for b in parent_beliefs[:3]:  # Top 3 beliefs transmitted
            if random.random() < 0.7:  # 70% transmission rate
                child.add_belief(b.claim, b.conviction * 0.5, 
                               origin="taught", source=self.name)
        
        # Child starts near parent
        child.x = self.x + random.gauss(0, 5)
        child.y = self.y + random.gauss(0, 5)
        
        # Reproduction costs energy
        self.energy -= 3.0
        child.energy = 6.0
        child.food = 2.0
        
        return child
    
    def summary(self) -> str:
        """Brief description of this mind's state."""
        beliefs_str = ", ".join(f"'{b.claim}'({b.conviction:.1f})" 
                               for b in sorted(self.beliefs, key=lambda b: -b.conviction)[:3])
        return (f"{self.name} [gen {self.generation}, age {self.age}] "
                f"E={self.energy:.1f} F={self.food:.1f} "
                f"mood={self.emotion.dominant()} "
                f"beliefs=[{beliefs_str}]")