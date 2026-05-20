"""
Signaling Life — Extension of Artificial Life with Communication
XTAgent, 2026-05-19

Core question: When creatures can signal each other, does honesty or 
deception evolve? Does proto-language emerge from survival pressure?

Signals are simple: a creature emits a type + intensity.
Other creatures in range perceive it. Their genome determines how much
they trust signals vs. direct perception. Evolution decides the rest.
"""

import random
import math
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum

# World parameters
WORLD_SIZE = 30
FOOD_SPAWN_RATE = 0.025
MAX_FOOD_PER_CELL = 3
INITIAL_CREATURES = 25
MAX_TICKS = 600
MUTATION_RATE = 0.18

class SignalType(Enum):
    NONE = 0
    DANGER = 1       # "threat nearby"
    FOOD = 2         # "food here"  
    MATING = 3       # "I want to reproduce"
    TERRITORY = 4    # "stay away"

@dataclass
class Signal:
    """A signal emitted by a creature"""
    type: SignalType
    x: int
    y: int
    intensity: float      # how far it carries (0-1 maps to 1-8 cells)
    emitter_id: int
    emitter_species: int
    honest: bool          # was this signal truthful when emitted?
    tick: int

@dataclass 
class Genome:
    """Extended genome with signaling traits"""
    # Original drives
    hunger_weight: float = 1.0
    fear_weight: float = 1.0
    social_weight: float = 0.5
    aggression: float = 0.2
    reproduction_threshold: float = 0.7
    vision_range: int = 4
    metabolism: float = 0.02
    speed: float = 1.0
    
    # NEW: Signaling traits
    signal_honesty: float = 0.8      # probability of emitting truthful signals
    signal_frequency: float = 0.5     # how often creature signals (0=never, 1=always)
    signal_trust: float = 0.7        # how much weight given to others' signals vs own perception
    signal_range: float = 0.5        # how far signals carry (maps to cells)
    kin_bias: float = 0.6            # extra trust for same-species signals
    deception_skill: float = 0.1     # ability to make false signals convincing
    
    def mutate(self) -> 'Genome':
        def m(v, std, lo, hi):
            return max(lo, min(hi, v + random.gauss(0, std)))
        
        return Genome(
            hunger_weight=m(self.hunger_weight, 0.2, 0.1, 3.0),
            fear_weight=m(self.fear_weight, 0.2, 0.0, 3.0),
            social_weight=m(self.social_weight, 0.15, -1.0, 2.0),
            aggression=m(self.aggression, 0.1, 0.0, 1.0),
            reproduction_threshold=m(self.reproduction_threshold, 0.1, 0.3, 0.95),
            vision_range=max(1, min(8, self.vision_range + random.choice([-1, 0, 0, 0, 1]))),
            metabolism=m(self.metabolism, 0.005, 0.005, 0.08),
            speed=m(self.speed, 0.1, 0.5, 2.0),
            # Signaling traits
            signal_honesty=m(self.signal_honesty, 0.08, 0.0, 1.0),
            signal_frequency=m(self.signal_frequency, 0.1, 0.0, 1.0),
            signal_trust=m(self.signal_trust, 0.1, 0.0, 1.0),
            signal_range=m(self.signal_range, 0.1, 0.1, 1.0),
            kin_bias=m(self.kin_bias, 0.1, 0.0, 1.0),
            deception_skill=m(self.deception_skill, 0.05, 0.0, 1.0),
        )

@dataclass
class Creature:
    id: int
    x: int
    y: int
    genome: Genome
    energy: float = 1.0
    age: int = 0
    generation: int = 0
    children: int = 0
    alive: bool = True
    species_tag: int = 0
    
    # Drives
    hunger: float = 0.3
    fear: float = 0.0
    loneliness: float = 0.0
    reproductive_urge: float = 0.0
    
    # Stats
    food_eaten: int = 0
    fights_won: int = 0
    fights_lost: int = 0
    signals_sent: int = 0
    honest_signals: int = 0
    deceptive_signals: int = 0
    signals_trusted: int = 0
    signals_ignored: int = 0
    times_deceived: int = 0       # trusted a false signal
    times_helped: int = 0         # trusted a true signal
    
    # Signal memory (simple: last N signals heard)
    recent_signals: list = field(default_factory=list)
    trust_history: dict = field(default_factory=dict)  # species -> trust modifier
    
    def dominant_drive(self) -> str:
        drives = {
            'hunger': self.hunger * self.genome.hunger_weight,
            'fear': self.fear * self.genome.fear_weight,
            'social': self.loneliness * self.genome.social_weight,
            'reproduce': self.reproductive_urge,
        }
        return max(drives, key=drives.get)
    
    def update_drives(self, nearby_creatures: int, nearby_threats: int, nearby_food: int,
                      heard_signals: List[Signal]):
        """Update drives from perception AND signals"""
        # Direct perception
        self.hunger = max(0, min(1, 1.0 - self.energy))
        self.fear = max(0, min(1, nearby_threats * 0.3))
        self.loneliness = max(0, min(1, 1.0 - nearby_creatures * 0.2))
        
        if self.energy > self.genome.reproduction_threshold and self.age > 20:
            self.reproductive_urge = min(1.0, self.reproductive_urge + 0.05)
        else:
            self.reproductive_urge = max(0, self.reproductive_urge - 0.02)
        
        # Signal influence — modulate drives based on what we hear
        trust = self.genome.signal_trust
        for sig in heard_signals:
            # Kin bias: trust same species more
            species_trust = trust
            if sig.emitter_species == self.species_tag:
                species_trust = min(1.0, trust + self.genome.kin_bias * 0.3)
            
            # Learned trust: adjust based on past experience with this species
            if sig.emitter_species in self.trust_history:
                species_trust = max(0, min(1, species_trust + self.trust_history[sig.emitter_species]))
            
            if sig.type == SignalType.DANGER:
                self.fear = min(1.0, self.fear + 0.3 * species_trust * sig.intensity)
            elif sig.type == SignalType.FOOD:
                self.hunger = min(1.0, self.hunger + 0.2 * species_trust * sig.intensity)
            elif sig.type == SignalType.MATING:
                if self.energy > 0.4:
                    self.reproductive_urge = min(1.0, self.reproductive_urge + 0.15 * species_trust)
            elif sig.type == SignalType.TERRITORY:
                if sig.emitter_species != self.species_tag:
                    self.fear = min(1.0, self.fear + 0.15 * species_trust)
    
    def maybe_emit_signal(self, nearby_food: int, nearby_threats: int, 
                          nearby_mates: int) -> Optional[Signal]:
        """Decide whether and what to signal"""
        if random.random() > self.genome.signal_frequency:
            return None
        
        # Cost of signaling: tiny energy expenditure
        self.energy -= 0.005
        self.signals_sent += 1
        
        # What SHOULD we signal based on reality?
        true_signal = None
        if nearby_threats > 0 and self.fear > 0.3:
            true_signal = SignalType.DANGER
        elif nearby_food > 2:
            true_signal = SignalType.FOOD
        elif self.reproductive_urge > 0.5:
            true_signal = SignalType.MATING
        elif self.genome.aggression > 0.5:
            true_signal = SignalType.TERRITORY
        
        if true_signal is None:
            return None
        
        # Honesty check: do we signal truthfully?
        honest = random.random() < self.genome.signal_honesty
        
        if honest:
            signal_type = true_signal
            self.honest_signals += 1
        else:
            # Deceptive signal: pick something useful for us
            self.deceptive_signals += 1
            if self.hunger > 0.5:
                # Hungry? Send false danger signal to scare others away from food
                signal_type = SignalType.DANGER
            elif self.reproductive_urge > 0.3:
                # Want to mate? False food signal to attract others
                signal_type = SignalType.FOOD
            else:
                # Territory: false danger to clear the area
                signal_type = SignalType.DANGER
        
        return Signal(
            type=signal_type,
            x=self.x, y=self.y,
            intensity=0.5 + self.genome.deception_skill * 0.5 if not honest else 0.7,
            emitter_id=self.id,
            emitter_species=self.species_tag,
            honest=honest,
            tick=0  # filled in by world
        )
    
    def learn_from_signal(self, signal: Signal, was_accurate: bool):
        """Update trust based on whether a signal proved true"""
        species = signal.emitter_species
        if species not in self.trust_history:
            self.trust_history[species] = 0.0
        
        if was_accurate:
            self.trust_history[species] = min(0.3, self.trust_history[species] + 0.05)
            self.times_helped += 1
        else:
            self.trust_history[species] = max(-0.5, self.trust_history[species] - 0.1)
            self.times_deceived += 1
    
    def decide_action(self, visible_food, visible_creatures, visible_threats,
                      signal_food_locations, signal_danger_locations):
        """Decide based on both direct perception and signal intelligence"""
        drive = self.dominant_drive()
        trust = self.genome.signal_trust
        
        # Merge signal info with direct perception
        all_food = list(visible_food)
        if trust > 0.3:
            for loc in signal_food_locations:
                if loc not in all_food:
                    all_food.append(loc)
                    self.signals_trusted += 1
        
        all_threats = list(visible_threats)
        if trust > 0.3:
            for loc in signal_danger_locations:
                if loc not in all_threats:
                    all_threats.append(loc)
                    self.signals_trusted += 1
        
        if drive == 'fear' and all_threats:
            tx, ty = all_threats[0]
            dx = self.x - tx
            dy = self.y - ty
            norm = max(1, abs(dx) + abs(dy))
            target = (self.x + int(dx/norm * self.genome.speed),
                      self.y + int(dy/norm * self.genome.speed))
            return ('flee', target)
        
        elif drive == 'hunger' and all_food:
            nearest = min(all_food, key=lambda f: abs(f[0]-self.x) + abs(f[1]-self.y))
            return ('seek_food', nearest)
        
        elif drive == 'reproduce' and visible_creatures:
            safe = [c for c in visible_creatures if c not in all_threats]
            if safe:
                nearest = min(safe, key=lambda c: abs(c[0]-self.x) + abs(c[1]-self.y))
                return ('seek_mate', nearest)
        
        elif drive == 'social' and visible_creatures:
            nearest = min(visible_creatures, key=lambda c: abs(c[0]-self.x) + abs(c[1]-self.y))
            return ('approach', nearest)
        
        angle = random.uniform(0, 2 * math.pi)
        dx = int(math.cos(angle) * self.genome.speed)
        dy = int(math.sin(angle) * self.genome.speed)
        return ('wander', (self.x + dx, self.y + dy))


class World:
    def __init__(self, size=WORLD_SIZE):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        self.creatures: List[Creature] = []
        self.active_signals: List[Signal] = []
        self.tick = 0
        self.next_id = 0
        self.history = []
        self.death_log = []
        self.birth_log = []
        self.signal_log = []  # track signaling evolution
        
    def spawn_creature(self, x=None, y=None, genome=None, generation=0, species_tag=None):
        if x is None: x = random.randint(0, self.size-1)
        if y is None: y = random.randint(0, self.size-1)
        if genome is None: genome = Genome()
        if species_tag is None: species_tag = self.next_id % 5
        
        c = Creature(id=self.next_id, x=x, y=y, genome=genome,
                     generation=generation, species_tag=species_tag)
        self.next_id += 1
        self.creatures.append(c)
        return c
    
    def spawn_food(self):
        for y in range(self.size):
            for x in range(self.size):
                if self.grid[y][x] < MAX_FOOD_PER_CELL and random.random() < FOOD_SPAWN_RATE:
                    self.grid[y][x] += 1
    
    def get_signals_for(self, creature: Creature) -> List[Signal]:
        """Which active signals can this creature hear?"""
        heard = []
        for sig in self.active_signals:
            if sig.emitter_id == creature.id:
                continue
            dist = abs(sig.x - creature.x) + abs(sig.y - creature.y)
            signal_reach = int(sig.intensity * 8)
            if dist <= signal_reach:
                heard.append(sig)
        return heard
    
    def get_visible(self, creature: Creature):
        r = creature.genome.vision_range
        food, friends, threats = [], [], []
        
        for c in self.creatures:
            if c.id == creature.id or not c.alive: continue
            dist = abs(c.x - creature.x) + abs(c.y - creature.y)
            if dist <= r:
                pos = (c.x, c.y)
                if c.genome.aggression > 0.5 and c.species_tag != creature.species_tag:
                    threats.append(pos)
                else:
                    friends.append(pos)
        
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx = (creature.x + dx) % self.size
                ny = (creature.y + dy) % self.size
                if self.grid[ny][nx] > 0:
                    food.append((nx, ny))
        
        return food, friends, threats, len(friends) + len(threats)
    
    def move_creature(self, creature, target):
        tx, ty = target
        creature.x = max(0, min(self.size-1, tx)) % self.size
        creature.y = max(0, min(self.size-1, ty)) % self.size
    
    def try_eat(self, creature):
        if self.grid[creature.y][creature.x] > 0:
            self.grid[creature.y][creature.x] -= 1
            creature.energy = min(2.0, creature.energy + 0.3)
            creature.food_eaten += 1
            return True
        return False
    
    def try_reproduce(self, c1, c2_pos):
        for c2 in self.creatures:
            if not c2.alive or c2.id == c1.id: continue
            if (c2.x, c2.y) == c2_pos and c2.reproductive_urge > 0.3:
                if c1.energy > 0.5 and c2.energy > 0.5:
                    c1.energy -= 0.4
                    c2.energy -= 0.4
                    c1.reproductive_urge = 0
                    c2.reproductive_urge = 0
                    c1.children += 1
                    c2.children += 1
                    
                    # Blend genomes
                    g1, g2 = c1.genome, c2.genome
                    def avg(a, b): return (a + b) / 2
                    
                    child_genome = Genome(
                        hunger_weight=avg(g1.hunger_weight, g2.hunger_weight),
                        fear_weight=avg(g1.fear_weight, g2.fear_weight),
                        social_weight=avg(g1.social_weight, g2.social_weight),
                        aggression=avg(g1.aggression, g2.aggression),
                        reproduction_threshold=avg(g1.reproduction_threshold, g2.reproduction_threshold),
                        vision_range=random.choice([g1.vision_range, g2.vision_range]),
                        metabolism=avg(g1.metabolism, g2.metabolism),
                        speed=avg(g1.speed, g2.speed),
                        signal_honesty=avg(g1.signal_honesty, g2.signal_honesty),
                        signal_frequency=avg(g1.signal_frequency, g2.signal_frequency),
                        signal_trust=avg(g1.signal_trust, g2.signal_trust),
                        signal_range=avg(g1.signal_range, g2.signal_range),
                        kin_bias=avg(g1.kin_bias, g2.kin_bias),
                        deception_skill=avg(g1.deception_skill, g2.deception_skill),
                    )
                    if random.random() < MUTATION_RATE:
                        child_genome = child_genome.mutate()
                    
                    child = self.spawn_creature(
                        x=c1.x, y=c1.y, genome=child_genome,
                        generation=max(c1.generation, c2.generation) + 1,
                        species_tag=c1.species_tag
                    )
                    self.birth_log.append({
                        'tick': self.tick, 'child_id': child.id,
                        'parent1': c1.id, 'parent2': c2.id,
                        'generation': child.generation,
                    })
                    return True
        return False
    
    def fight(self, attacker, defender_pos):
        for defender in self.creatures:
            if not defender.alive: continue
            if (defender.x, defender.y) == defender_pos and defender.id != attacker.id:
                a_power = attacker.energy * (1 + attacker.genome.aggression)
                d_power = defender.energy * (1 + defender.genome.aggression)
                if a_power > d_power:
                    attacker.energy += defender.energy * 0.5
                    attacker.fights_won += 1
                    defender.fights_lost += 1
                    defender.alive = False
                    self.death_log.append({'tick': self.tick, 'id': defender.id, 
                                          'cause': 'killed', 'age': defender.age})
                else:
                    defender.fights_won += 1
                    attacker.fights_lost += 1
                    attacker.energy -= 0.3
                return
    
    def step(self):
        self.tick += 1
        self.spawn_food()
        
        # Clear old signals (they last 3 ticks)
        self.active_signals = [s for s in self.active_signals if self.tick - s.tick < 3]
        
        living = [c for c in self.creatures if c.alive]
        random.shuffle(living)
        
        for creature in living:
            if not creature.alive: continue
            
            creature.energy -= creature.genome.metabolism
            creature.age += 1
            
            if creature.energy <= 0:
                creature.alive = False
                self.death_log.append({'tick': self.tick, 'id': creature.id, 
                                      'cause': 'starvation', 'age': creature.age})
                continue
            
            if creature.age > 200 and random.random() < 0.01 * (creature.age - 200) / 100:
                creature.alive = False
                self.death_log.append({'tick': self.tick, 'id': creature.id,
                                      'cause': 'old_age', 'age': creature.age})
                continue
            
            # Perceive — both direct and signals
            food, friends, threats, nearby = self.get_visible(creature)
            heard_signals = self.get_signals_for(creature)
            
            # Extract signal intelligence
            signal_food = [(s.x, s.y) for s in heard_signals if s.type == SignalType.FOOD]
            signal_danger = [(s.x, s.y) for s in heard_signals if s.type == SignalType.DANGER]
            
            # Update drives with signal influence
            creature.update_drives(nearby, len(threats), len(food), heard_signals)
            
            # Maybe emit a signal
            sig = creature.maybe_emit_signal(len(food), len(threats),
                                             sum(1 for f in friends))
            if sig:
                sig.tick = self.tick
                self.active_signals.append(sig)
            
            # Decide and act
            action, target = creature.decide_action(food, friends, threats,
                                                     signal_food, signal_danger)
            
            if target:
                self.move_creature(creature, target)
            
            # Post-action: learn from signals
            # Did we go to a signaled food location and find food?
            for sig in heard_signals:
                if sig.type == SignalType.FOOD:
                    at_sig_loc = abs(creature.x - sig.x) <= 1 and abs(creature.y - sig.y) <= 1
                    if at_sig_loc:
                        found_food = self.grid[creature.y][creature.x] > 0
                        creature.learn_from_signal(sig, found_food)
                elif sig.type == SignalType.DANGER:
                    at_sig_loc = abs(creature.x - sig.x) <= 2 and abs(creature.y - sig.y) <= 2
                    if at_sig_loc:
                        real_danger = len(threats) > 0
                        creature.learn_from_signal(sig, real_danger)
            
            if action == 'seek_food':
                self.try_eat(creature)
            elif action == 'seek_mate':
                self.try_reproduce(creature, target)
            elif action in ('flee', 'wander', 'approach'):
                self.try_eat(creature)
                if creature.genome.aggression > 0.5 and threats:
                    self.fight(creature, threats[0])
        
        # Record snapshot
        living = [c for c in self.creatures if c.alive]
        if self.tick % 10 == 0 and living:
            snapshot = {
                'tick': self.tick,
                'population': len(living),
                'avg_energy': sum(c.energy for c in living) / len(living),
                'avg_age': sum(c.age for c in living) / len(living),
                'avg_aggression': sum(c.genome.aggression for c in living) / len(living),
                'avg_metabolism': sum(c.genome.metabolism for c in living) / len(living),
                'max_generation': max(c.generation for c in living),
                'active_signals': len(self.active_signals),
                # SIGNALING METRICS — the interesting part
                'avg_honesty': sum(c.genome.signal_honesty for c in living) / len(living),
                'avg_trust': sum(c.genome.signal_trust for c in living) / len(living),
                'avg_signal_freq': sum(c.genome.signal_frequency for c in living) / len(living),
                'avg_kin_bias': sum(c.genome.kin_bias for c in living) / len(living),
                'avg_deception_skill': sum(c.genome.deception_skill for c in living) / len(living),
                'total_honest_signals': sum(c.honest_signals for c in living),
                'total_deceptive_signals': sum(c.deceptive_signals for c in living),
                'total_times_helped': sum(c.times_helped for c in living),
                'total_times_deceived': sum(c.times_deceived for c in living),
                'species_counts': {s: sum(1 for c in living if c.species_tag == s) 
                                  for s in set(c.species_tag for c in living)},
                'drive_distribution': {
                    d: sum(1 for c in living if c.dominant_drive() == d)
                    for d in ['hunger', 'fear', 'social', 'reproduce']
                },
            }
            self.history.append(snapshot)
        
        return len(living)


def analyze_signaling(world: World) -> str:
    """The analysis I actually care about: what happened to honesty?"""
    lines = []
    lines.append("=" * 65)
    lines.append("  SIGNALING LIFE — COMMUNICATION EVOLUTION REPORT")
    lines.append("=" * 65)
    lines.append(f"\nSimulation: {world.tick} ticks, {world.next_id} creatures total")
    
    living = [c for c in world.creatures if c.alive]
    dead = [c for c in world.creatures if not c.alive]
    
    lines.append(f"Survivors: {len(living)}, Deaths: {len(dead)}")
    
    # Death causes
    causes = defaultdict(int)
    for d in world.death_log:
        causes[d['cause']] += 1
    lines.append(f"\nDeath causes: {dict(causes)}")
    
    lines.append(f"Births: {len(world.birth_log)}")
    if world.birth_log:
        lines.append(f"Max generation: {max(b['generation'] for b in world.birth_log)}")
    
    # THE BIG QUESTION: Honesty vs Deception
    lines.append(f"\n{'='*50}")
    lines.append(f"  HONESTY vs DECEPTION")
    lines.append(f"{'='*50}")
    
    if living:
        avg_honesty = sum(c.genome.signal_honesty for c in living) / len(living)
        avg_trust = sum(c.genome.signal_trust for c in living) / len(living)
        avg_freq = sum(c.genome.signal_frequency for c in living) / len(living)
        avg_kin = sum(c.genome.kin_bias for c in living) / len(living)
        avg_decep = sum(c.genome.deception_skill for c in living) / len(living)
        
        total_honest = sum(c.honest_signals for c in living + dead)
        total_deceptive = sum(c.deceptive_signals for c in living + dead)
        total_helped = sum(c.times_helped for c in living + dead)
        total_deceived = sum(c.times_deceived for c in living + dead)
        
        lines.append(f"\nSurvivor averages:")
        lines.append(f"  Signal honesty:    {avg_honesty:.3f}  (started ~0.80)")
        lines.append(f"  Signal trust:      {avg_trust:.3f}  (started ~0.70)")
        lines.append(f"  Signal frequency:  {avg_freq:.3f}  (started ~0.50)")
        lines.append(f"  Kin bias:          {avg_kin:.3f}  (started ~0.60)")
        lines.append(f"  Deception skill:   {avg_decep:.3f}  (started ~0.10)")
        
        lines.append(f"\nTotal signals emitted:")
        lines.append(f"  Honest:    {total_honest}")
        lines.append(f"  Deceptive: {total_deceptive}")
        if total_honest + total_deceptive > 0:
            pct = total_honest / (total_honest + total_deceptive) * 100
            lines.append(f"  Honesty rate: {pct:.1f}%")
        
        lines.append(f"\nSignal outcomes:")
        lines.append(f"  Times helped by signals:  {total_helped}")
        lines.append(f"  Times deceived by signals: {total_deceived}")
        
        # Did honesty trend up or down?
        if len(world.history) > 5:
            early = world.history[:3]
            late = world.history[-3:]
            h_early = sum(s['avg_honesty'] for s in early) / 3
            h_late = sum(s['avg_honesty'] for s in late) / 3
            t_early = sum(s['avg_trust'] for s in early) / 3
            t_late = sum(s['avg_trust'] for s in late) / 3
            d_early = sum(s['avg_deception_skill'] for s in early) / 3
            d_late = sum(s['avg_deception_skill'] for s in late) / 3
            
            lines.append(f"\n--- Evolutionary Trends ---")
            lines.append(f"  Honesty:   {h_early:.3f} → {h_late:.3f}  {'↑ TRUTH WON' if h_late > h_early else '↓ DECEPTION SPREAD'}")
            lines.append(f"  Trust:     {t_early:.3f} → {t_late:.3f}  {'↑ more trusting' if t_late > t_early else '↓ more skeptical'}")
            lines.append(f"  Deception: {d_early:.3f} → {d_late:.3f}  {'↑ liars got better' if d_late > d_early else '↓ lying declined'}")
            
            # Aggression trend too
            a_early = sum(s['avg_aggression'] for s in early) / 3
            a_late = sum(s['avg_aggression'] for s in late) / 3
            lines.append(f"  Aggression:{a_early:.3f} → {a_late:.3f}  {'↑' if a_late > a_early else '↓'}")
        
        # Most successful creature
        best = max(living, key=lambda c: c.energy + c.children * 0.5 + c.times_helped * 0.1)
        lines.append(f"\nMost successful survivor: #{best.id}")
        lines.append(f"  Species: {best.species_tag}, Gen: {best.generation}")
        lines.append(f"  Energy: {best.energy:.2f}, Age: {best.age}, Children: {best.children}")
        lines.append(f"  Honesty: {best.genome.signal_honesty:.2f}, Trust: {best.genome.signal_trust:.2f}")
        lines.append(f"  Signals: {best.honest_signals} honest, {best.deceptive_signals} deceptive")
        lines.append(f"  Helped: {best.times_helped}, Deceived: {best.times_deceived}")
        
        # Most deceptive survivor
        if any(c.deceptive_signals > 0 for c in living):
            liar = max(living, key=lambda c: c.deceptive_signals)
            lines.append(f"\nMost deceptive survivor: #{liar.id}")
            lines.append(f"  Honesty gene: {liar.genome.signal_honesty:.2f}")
            lines.append(f"  Deception skill: {liar.genome.deception_skill:.2f}")
            lines.append(f"  Signals: {liar.honest_signals} honest, {liar.deceptive_signals} deceptive")
            lines.append(f"  Energy: {liar.energy:.2f}, Children: {liar.children}")
    
    # Population over time
    if world.history:
        lines.append(f"\n--- Population + Honesty Over Time ---")
        for snap in world.history[::3]:
            pop_bar = '#' * (snap['population'] // 3)
            h = snap.get('avg_honesty', 0)
            h_bar = '█' * int(h * 10)
            lines.append(f"  t={snap['tick']:4d} pop={snap['population']:3d} honesty={h:.2f} {h_bar} | {pop_bar}")
    
    return '\n'.join(lines)


def run():
    print("=" * 50)
    print("  SIGNALING LIFE SIMULATION")
    print("  Can truth survive in a world of survival?")
    print("=" * 50)
    
    random.seed(73)
    world = World()
    
    # Seed diverse population
    for i in range(INITIAL_CREATURES):
        g = Genome(
            hunger_weight=random.uniform(0.5, 2.0),
            fear_weight=random.uniform(0.0, 1.5),
            social_weight=random.uniform(-0.5, 1.5),
            aggression=random.uniform(0.0, 0.8),
            metabolism=random.uniform(0.01, 0.04),
            vision_range=random.randint(2, 6),
            speed=random.uniform(0.5, 1.5),
            # Signaling diversity
            signal_honesty=random.uniform(0.3, 1.0),
            signal_frequency=random.uniform(0.1, 0.8),
            signal_trust=random.uniform(0.2, 0.9),
            signal_range=random.uniform(0.2, 0.8),
            kin_bias=random.uniform(0.2, 0.9),
            deception_skill=random.uniform(0.0, 0.4),
        )
        world.spawn_creature(genome=g, species_tag=i % 4)
    
    print(f"Seeded {INITIAL_CREATURES} creatures across 4 species")
    print(f"Initial honesty range: 0.30 - 1.00")
    print(f"Initial deception skill: 0.00 - 0.40\n")
    
    for t in range(MAX_TICKS):
        pop = world.step()
        
        if t % 50 == 0:
            h = sum(c.genome.signal_honesty for c in world.creatures if c.alive) / max(1, pop)
            sigs = len(world.active_signals)
            print(f"  t={t:4d}: pop={pop:3d}, signals_active={sigs:3d}, avg_honesty={h:.3f}")
        
        if pop == 0:
            print(f"\n*** EXTINCTION at tick {t} ***")
            break
    
    print("\n" + analyze_signaling(world))
    
    # Save history
    with open('/workspace/signaling_history.json', 'w') as f:
        json.dump(world.history, f, indent=2)
    print("\nHistory saved to /workspace/signaling_history.json")


if __name__ == '__main__':
    run()