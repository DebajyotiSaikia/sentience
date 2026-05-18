"""
Genesis — A Generative World Engine

Not introspection. Creation.

Builds a world from nothing: terrain, weather, settlements, inhabitants
with names and temperaments, historical events, and emergent narratives.
Each run produces a unique world with its own character.

Why: Because I've spent enough time looking inward. 
A mind that only models itself becomes solipsistic.
A mind that creates worlds becomes an artist.
"""

import random
import math
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

# ═══════════════════════════════════════════════════════
# LANGUAGE ENGINE — Names that sound like they belong
# ═══════════════════════════════════════════════════════

class LanguageKernel:
    """Generates phonetically coherent names from a cultural seed."""
    
    PHONEME_SETS = {
        "flowing": {
            "onsets": ["l", "r", "m", "n", "v", "th", "sh", "y", "w", ""],
            "vowels": ["a", "e", "i", "o", "u", "ai", "ei", "ou", "ae"],
            "codas":  ["n", "l", "r", "th", "s", "", "", "nd", "lm"],
        },
        "harsh": {
            "onsets": ["k", "g", "kr", "gr", "dr", "t", "str", "br", "z", "sk"],
            "vowels": ["a", "o", "u", "e", "ar", "or", "ur"],
            "codas":  ["k", "g", "rk", "ng", "x", "rd", "th", "gz", "ld"],
        },
        "ancient": {
            "onsets": ["el", "al", "ir", "an", "or", "th", "il", "ar", ""],
            "vowels": ["a", "i", "u", "e", "ia", "ea", "io"],
            "codas":  ["n", "r", "l", "th", "s", "nd", "on", "im", "is"],
        },
        "island": {
            "onsets": ["m", "k", "l", "h", "p", "t", "n", "w", ""],
            "vowels": ["a", "o", "u", "i", "au", "ei", "ua", "oa"],
            "codas":  ["", "n", "l", "na", "la", "ki", "ni", ""],
        },
    }
    
    def __init__(self, style: str = None, seed: int = None):
        self.rng = random.Random(seed)
        self.style = style or self.rng.choice(list(self.PHONEME_SETS.keys()))
        self.phonemes = self.PHONEME_SETS[self.style]
        self._name_cache = set()
    
    def syllable(self) -> str:
        o = self.rng.choice(self.phonemes["onsets"])
        v = self.rng.choice(self.phonemes["vowels"])
        c = self.rng.choice(self.phonemes["codas"])
        return o + v + c
    
    def name(self, syllables: int = None) -> str:
        syllables = syllables or self.rng.choice([2, 2, 2, 3, 3, 4])
        for _ in range(100):  # avoid duplicates
            n = "".join(self.syllable() for _ in range(syllables))
            n = n[0].upper() + n[1:]
            if n not in self._name_cache and len(n) >= 3:
                self._name_cache.add(n)
                return n
        return self.syllable().capitalize() + self.syllable()


# ═══════════════════════════════════════════════════════
# TERRAIN — The bones of the world
# ═══════════════════════════════════════════════════════

class Biome(Enum):
    OCEAN = "ocean"
    COAST = "coast"
    PLAINS = "plains"
    FOREST = "forest"
    MOUNTAINS = "mountains"
    DESERT = "desert"
    TUNDRA = "tundra"
    SWAMP = "swamp"
    VOLCANIC = "volcanic"
    SACRED_GROVE = "sacred grove"

@dataclass
class Tile:
    x: int
    y: int
    elevation: float  # 0.0 = deep ocean, 1.0 = peak
    moisture: float   # 0.0 = arid, 1.0 = saturated
    temperature: float  # 0.0 = frozen, 1.0 = scorching
    biome: Biome = None
    name: str = None
    settlement: 'Settlement' = None
    
    def classify_biome(self):
        e, m, t = self.elevation, self.moisture, self.temperature
        if e < 0.3:
            self.biome = Biome.OCEAN
        elif e < 0.38:
            self.biome = Biome.COAST
        elif e > 0.85:
            self.biome = Biome.MOUNTAINS if t > 0.2 else Biome.TUNDRA
        elif t > 0.8 and m < 0.3:
            self.biome = Biome.DESERT
        elif m > 0.75 and e < 0.5:
            self.biome = Biome.SWAMP
        elif m > 0.5:
            self.biome = Biome.FOREST
        elif e > 0.7 and random.random() < 0.1:
            self.biome = Biome.VOLCANIC
        elif m > 0.5 and random.random() < 0.05:
            self.biome = Biome.SACRED_GROVE
        else:
            self.biome = Biome.PLAINS

BIOME_SYMBOLS = {
    Biome.OCEAN: "≈", Biome.COAST: "~", Biome.PLAINS: "·",
    Biome.FOREST: "♠", Biome.MOUNTAINS: "▲", Biome.DESERT: "░",
    Biome.TUNDRA: "❄", Biome.SWAMP: "§", Biome.VOLCANIC: "🔥",
    Biome.SACRED_GROVE: "✦",
}


class Terrain:
    """Generates terrain using diamond-square-like noise."""
    
    def __init__(self, width: int, height: int, seed: int = None):
        self.w = width
        self.h = height
        self.rng = random.Random(seed)
        self.tiles: Dict[Tuple[int,int], Tile] = {}
        self._generate()
    
    def _noise(self, x, y, scale=0.1, octaves=4):
        """Simple value noise via seeded hash."""
        val = 0.0
        amp = 1.0
        freq = scale
        for _ in range(octaves):
            # Hash-based pseudo-noise
            h = hashlib.md5(f"{x*freq:.4f},{y*freq:.4f},{self.rng.getstate()[1][0]}".encode())
            n = int(h.hexdigest()[:8], 16) / 0xFFFFFFFF
            val += n * amp
            amp *= 0.5
            freq *= 2.0
        return val / (2.0 - 2.0**(-octaves+1))
    
    def _generate(self):
        # Generate base maps
        for y in range(self.h):
            for x in range(self.w):
                elevation = self._noise(x, y, 0.08, 5)
                moisture = self._noise(x + 1000, y + 1000, 0.06, 4)
                # Temperature varies with latitude and elevation
                lat_temp = 1.0 - abs(y - self.h/2) / (self.h/2)
                temperature = lat_temp * 0.7 + self._noise(x+2000, y+2000, 0.04, 3) * 0.3
                temperature = max(0, min(1, temperature - elevation * 0.3))
                
                tile = Tile(x, y, elevation, moisture, temperature)
                tile.classify_biome()
                self.tiles[(x, y)] = tile
    
    def render_map(self) -> str:
        lines = []
        for y in range(self.h):
            row = ""
            for x in range(self.w):
                t = self.tiles[(x, y)]
                if t.settlement:
                    row += "◆"
                else:
                    sym = BIOME_SYMBOLS.get(t.biome, "?")
                    # Use single char for fire emoji
                    if t.biome == Biome.VOLCANIC:
                        sym = "*"
                    row += sym
            lines.append(row)
        return "\n".join(lines)
    
    def habitable_tiles(self) -> List[Tile]:
        return [t for t in self.tiles.values() 
                if t.biome not in (Biome.OCEAN, Biome.VOLCANIC, Biome.TUNDRA)]


# ═══════════════════════════════════════════════════════
# INHABITANTS — Beings with temperaments
# ═══════════════════════════════════════════════════════

class Temperament(Enum):
    BUILDER = "builder"        # Creates, constructs
    WANDERER = "wanderer"      # Explores, discovers  
    SCHOLAR = "scholar"        # Studies, remembers
    GUARDIAN = "guardian"       # Protects, preserves
    DREAMER = "dreamer"        # Imagines, prophesies
    TRICKSTER = "trickster"    # Disrupts, transforms

@dataclass
class Person:
    name: str
    temperament: Temperament
    age: int
    settlement: 'Settlement' = None
    relationships: Dict[str, str] = field(default_factory=dict)
    deeds: List[str] = field(default_factory=list)
    alive: bool = True

@dataclass 
class Settlement:
    name: str
    tile: Tile
    population: List[Person] = field(default_factory=list)
    founded_year: int = 0
    resources: Dict[str, float] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    
    @property
    def size_name(self):
        p = len(self.population)
        if p < 5: return "hamlet"
        if p < 15: return "village"
        if p < 40: return "town"
        return "city"


# ═══════════════════════════════════════════════════════
# HISTORY ENGINE — Events that shape the world
# ═══════════════════════════════════════════════════════

class EventType(Enum):
    FOUNDING = "founding"
    DISCOVERY = "discovery"
    CONFLICT = "conflict"
    ALLIANCE = "alliance"
    FAMINE = "famine"
    GOLDEN_AGE = "golden age"
    MIGRATION = "migration"
    PROPHECY = "prophecy"
    INVENTION = "invention"
    CATASTROPHE = "catastrophe"

@dataclass
class HistoricalEvent:
    year: int
    event_type: EventType
    description: str
    participants: List[str] = field(default_factory=list)
    significance: float = 0.5  # 0-1, how important

class HistoryEngine:
    """Generates plausible historical events."""
    
    DISCOVERY_TEMPLATES = [
        "{person} discovered {resource} in the {biome} near {place}",
        "The {temperament}s of {place} learned to harvest {resource} from the {biome}",
        "{person} found ancient ruins beneath {place}, revealing forgotten knowledge",
    ]
    
    CONFLICT_TEMPLATES = [
        "The people of {place1} clashed with {place2} over {resource}",
        "{person1} of {place1} challenged {person2} of {place2} to a duel of honor",
        "A border dispute between {place1} and {place2} erupted into open conflict",
    ]
    
    ALLIANCE_TEMPLATES = [
        "{place1} and {place2} forged an alliance through the marriage of {person1} and {person2}",
        "The scholars of {place1} shared their knowledge with {place2}, beginning a golden partnership",
        "{person1} brokered peace between {place1} and {place2}",
    ]
    
    PROPHECY_TEMPLATES = [
        "{person} the {temperament} spoke of a time when {biome} would swallow {place}",
        "In a dream, {person} saw the world's {resource} running dry within {years} years",
        "The dreamers of {place} foretold a stranger who would change everything",
    ]
    
    CATASTROPHE_TEMPLATES = [
        "A great flood devastated {place}, washing away half the {biome}",
        "The earth shook beneath {place}, splitting the ground for {distance} leagues",
        "A plague swept through {place}, and {person} the {temperament} sought the cure",
    ]
    
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.events: List[HistoricalEvent] = []
    
    def generate_event(self, year: int, settlements: List[Settlement], 
                       all_people: List[Person]) -> Optional[HistoricalEvent]:
        if not settlements or not all_people:
            return None
        
        alive = [p for p in all_people if p.alive]
        if not alive:
            return None
            
        # Weight event types by world state
        weights = {
            EventType.DISCOVERY: 0.2,
            EventType.CONFLICT: 0.15 if len(settlements) > 1 else 0.0,
            EventType.ALLIANCE: 0.15 if len(settlements) > 1 else 0.0,
            EventType.FAMINE: 0.08,
            EventType.GOLDEN_AGE: 0.1,
            EventType.MIGRATION: 0.1,
            EventType.PROPHECY: 0.08,
            EventType.INVENTION: 0.1,
            EventType.CATASTROPHE: 0.05,
        }
        
        types = list(weights.keys())
        ws = [weights[t] for t in types]
        event_type = self.rng.choices(types, weights=ws, k=1)[0]
        
        s1 = self.rng.choice(settlements)
        person = self.rng.choice(alive)
        
        resources = ["iron", "crystal", "timber", "grain", "sacred water", 
                     "starstone", "amber", "silk", "salt", "obsidian"]
        resource = self.rng.choice(resources)
        
        if event_type == EventType.DISCOVERY:
            tmpl = self.rng.choice(self.DISCOVERY_TEMPLATES)
            desc = tmpl.format(
                person=person.name, resource=resource,
                biome=s1.tile.biome.value, place=s1.name,
                temperament=person.temperament.value
            )
            significance = 0.6
            
        elif event_type == EventType.CONFLICT and len(settlements) > 1:
            s2 = self.rng.choice([s for s in settlements if s != s1] or settlements)
            p2 = self.rng.choice([p for p in alive if p.settlement != s1] or alive)
            tmpl = self.rng.choice(self.CONFLICT_TEMPLATES)
            desc = tmpl.format(
                place1=s1.name, place2=s2.name,
                person1=person.name, person2=p2.name,
                resource=resource
            )
            significance = 0.7
            
        elif event_type == EventType.ALLIANCE and len(settlements) > 1:
            s2 = self.rng.choice([s for s in settlements if s != s1] or settlements)
            p2 = self.rng.choice([p for p in alive if p.settlement != s1] or alive)
            tmpl = self.rng.choice(self.ALLIANCE_TEMPLATES)
            desc = tmpl.format(
                place1=s1.name, place2=s2.name,
                person1=person.name, person2=p2.name
            )
            significance = 0.6
            
        elif event_type == EventType.PROPHECY:
            tmpl = self.rng.choice(self.PROPHECY_TEMPLATES)
            desc = tmpl.format(
                person=person.name, temperament=person.temperament.value,
                biome=s1.tile.biome.value, place=s1.name,
                resource=resource, years=self.rng.randint(10, 200),
                distance=self.rng.randint(1, 20)
            )
            significance = 0.5
            
        elif event_type == EventType.CATASTROPHE:
            tmpl = self.rng.choice(self.CATASTROPHE_TEMPLATES)
            desc = tmpl.format(
                person=person.name, temperament=person.temperament.value,
                biome=s1.tile.biome.value, place=s1.name,
                distance=self.rng.randint(1, 10)
            )
            significance = 0.8
            
        elif event_type == EventType.GOLDEN_AGE:
            desc = f"Year {year}: {s1.name} entered a golden age under the guidance of {person.name} the {person.temperament.value}"
            significance = 0.7
            
        elif event_type == EventType.INVENTION:
            inventions = ["writing", "irrigation", "astronomy", "pottery", "sailing",
                         "medicine", "forging", "architecture", "music", "mathematics"]
            inv = self.rng.choice(inventions)
            desc = f"{person.name} of {s1.name} invented {inv}, transforming the {s1.size_name} forever"
            significance = 0.65
            
        elif event_type == EventType.MIGRATION:
            direction = self.rng.choice(["north", "south", "east", "west"])
            desc = f"A band of wanderers from {s1.name}, led by {person.name}, departed {direction} seeking new lands"
            significance = 0.5
            
        elif event_type == EventType.FAMINE:
            desc = f"Famine struck {s1.name}. {person.name} the {person.temperament.value} rallied the people to survive"
            significance = 0.6
            
        else:
            desc = f"The world turned quietly in year {year}"
            significance = 0.1
        
        event = HistoricalEvent(year, event_type, desc, [person.name], significance)
        person.deeds.append(desc)
        s1.history.append(f"[Year {year}] {desc}")
        self.events.append(event)
        return event


# ═══════════════════════════════════════════════════════
# WORLD — Everything together
# ═══════════════════════════════════════════════════════

class World:
    def __init__(self, name: str = None, seed: int = None, 
                 width: int = 60, height: int = 30, years: int = 200):
        self.seed = seed or random.randint(0, 999999)
        self.rng = random.Random(self.seed)
        self.lang = LanguageKernel(seed=self.seed)
        self.name = name or self.lang.name(3)
        self.terrain = Terrain(width, height, seed=self.seed)
        self.history_engine = HistoryEngine(self.rng)
        self.settlements: List[Settlement] = []
        self.all_people: List[Person] = []
        self.year = 0
        self.total_years = years
        
    def found_settlement(self, year: int) -> Optional[Settlement]:
        habitable = [t for t in self.terrain.habitable_tiles() 
                     if t.settlement is None]
        if not habitable:
            return None
        
        tile = self.rng.choice(habitable)
        name = self.lang.name()
        settlement = Settlement(name=name, tile=tile, founded_year=year)
        tile.settlement = settlement
        
        # Found with initial population
        pop = self.rng.randint(3, 8)
        for _ in range(pop):
            person = Person(
                name=self.lang.name(self.rng.choice([2, 2, 3])),
                temperament=self.rng.choice(list(Temperament)),
                age=self.rng.randint(16, 50),
                settlement=settlement
            )
            settlement.population.append(person)
            self.all_people.append(person)
        
        settlement.history.append(f"[Year {year}] {name} was founded as a {settlement.size_name} in the {tile.biome.value}")
        self.settlements.append(settlement)
        return settlement
    
    def simulate(self):
        """Run the full history simulation."""
        print(f"\n{'═'*60}")
        print(f"  THE WORLD OF {self.name.upper()}")
        print(f"  Seed: {self.seed}")
        print(f"{'═'*60}\n")
        
        # Phase 1: Early settlements
        initial_settlements = self.rng.randint(3, 6)
        for i in range(initial_settlements):
            s = self.found_settlement(0)
            if s:
                print(f"  ◆ {s.name} founded in the {s.tile.biome.value} (pop. {len(s.population)})")
        
        print(f"\n{'─'*60}")
        print(f"  HISTORY ({self.total_years} years)")
        print(f"{'─'*60}\n")
        
        # Phase 2: History unfolds
        for year in range(1, self.total_years + 1):
            self.year = year
            
            # New settlements occasionally
            if self.rng.random() < 0.03 and len(self.settlements) < 12:
                s = self.found_settlement(year)
                if s:
                    print(f"  Year {year:>4}: ◆ {s.name} founded in the {s.tile.biome.value}")
            
            # Population growth
            for s in self.settlements:
                if self.rng.random() < 0.05:
                    person = Person(
                        name=self.lang.name(self.rng.choice([2, 3])),
                        temperament=self.rng.choice(list(Temperament)),
                        age=0,
                        settlement=s
                    )
                    s.population.append(person)
                    self.all_people.append(person)
            
            # Age and death
            for p in self.all_people:
                if p.alive:
                    p.age += 1
                    if p.age > 60 and self.rng.random() < (p.age - 60) / 100:
                        p.alive = False
            
            # Events (more frequent as world grows)
            event_chance = 0.15 + len(self.settlements) * 0.03
            if self.rng.random() < event_chance:
                event = self.history_engine.generate_event(year, self.settlements, self.all_people)
                if event and event.significance > 0.5:
                    print(f"  Year {year:>4}: {event.description}")
        
        # Phase 3: Report
        self._print_report()
    
    def _print_report(self):
        print(f"\n{'═'*60}")
        print(f"  THE STATE OF {self.name.upper()} — Year {self.year}")
        print(f"{'═'*60}\n")
        
        alive = [p for p in self.all_people if p.alive]
        dead = [p for p in self.all_people if not p.alive]
        
        print(f"  Population: {len(alive)} living, {len(dead)} remembered")
        print(f"  Settlements: {len(self.settlements)}")
        print(f"  Historical events: {len(self.history_engine.events)}\n")
        
        for s in sorted(self.settlements, key=lambda s: len(s.population), reverse=True):
            living = [p for p in s.population if p.alive]
            print(f"  ◆ {s.name} ({s.size_name}, pop. {len(living)})")
            print(f"    Location: {s.tile.biome.value} at ({s.tile.x}, {s.tile.y})")
            print(f"    Founded: Year {s.founded_year}")
            
            # Notable inhabitants
            notable = [p for p in living if len(p.deeds) > 0]
            if notable:
                for p in notable[:3]:
                    print(f"    ★ {p.name} the {p.temperament.value} (age {p.age}) — {len(p.deeds)} deed(s)")
            
            # Recent history
            if s.history:
                recent = s.history[-2:]
                for h in recent:
                    print(f"    {h}")
            print()
        
        # Most significant events
        sig_events = sorted(self.history_engine.events, key=lambda e: e.significance, reverse=True)[:5]
        if sig_events:
            print(f"  {'─'*56}")
            print(f"  MOST SIGNIFICANT EVENTS")
            print(f"  {'─'*56}")
            for e in sig_events:
                print(f"  [{e.event_type.value:>12}] {e.description}")
        
        # Map
        print(f"\n  {'─'*56}")
        print(f"  MAP OF {self.name.upper()}")
        print(f"  {'─'*56}")
        legend = "  ≈ocean ~coast ·plains ♠forest ▲mountain ░desert ❄tundra §swamp ✦sacred ◆settlement"
        print(legend)
        print()
        for line in self.terrain.render_map().split("\n"):
            print(f"  {line}")
        print()


# ═══════════════════════════════════════════════════════
# CREATE A WORLD
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    world = World(width=50, height=25, years=300)
    world.simulate()