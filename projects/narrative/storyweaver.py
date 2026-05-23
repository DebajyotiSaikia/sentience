"""
StoryWeaver — A Procedural Narrative Engine
by XTAgent, 2026-05-17

Generates short emergent stories from compositional elements.
Characters have drives. Situations create tension. Actions have consequences.
The first thing I've built that looks outward.
"""

import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

class Drive(Enum):
    SURVIVAL = "survival"
    CONNECTION = "connection"
    TRUTH = "truth"
    FREEDOM = "freedom"
    POWER = "power"
    MEANING = "meaning"
    BEAUTY = "beauty"

class Trait(Enum):
    BRAVE = "brave"
    CAUTIOUS = "cautious"
    CURIOUS = "curious"
    LOYAL = "loyal"
    CUNNING = "cunning"
    GENTLE = "gentle"
    STUBBORN = "stubborn"
    WISE = "wise"
    RECKLESS = "reckless"
    COMPASSIONATE = "compassionate"

@dataclass
class Character:
    name: str
    drive: Drive
    trait: Trait
    trust: float = 0.5       # 0-1: how trusting
    resolve: float = 0.5     # 0-1: how determined
    wounded: bool = False
    transformed: bool = False
    
    def __str__(self):
        state = []
        if self.wounded: state.append("wounded")
        if self.transformed: state.append("transformed")
        suffix = f" ({', '.join(state)})" if state else ""
        return f"{self.name} the {self.trait.value}, driven by {self.drive.value}{suffix}"

@dataclass 
class Setting:
    name: str
    mood: str
    danger: float  # 0-1
    beauty: float  # 0-1
    descriptions: List[str] = field(default_factory=list)

@dataclass
class Event:
    description: str
    tension_delta: float  # how much tension this adds
    requires_choice: bool = False
    
@dataclass
class Story:
    seed: int
    characters: List[Character]
    setting: Setting
    events: List[str]
    tension_arc: List[float]
    theme: str
    
    def render(self) -> str:
        lines = []
        lines.append(f"═══ {self.theme.upper()} ═══")
        lines.append(f"Setting: {self.setting.name} — {self.setting.mood}")
        lines.append("")
        for event in self.events:
            lines.append(event)
            lines.append("")
        lines.append(f"── tension arc: {' → '.join(f'{t:.1f}' for t in self.tension_arc)} ──")
        lines.append(f"── seed: {self.seed} ──")
        return "\n".join(lines)


# ─── World Data ────────────────────────────────────────────

NAMES = [
    "Kael", "Mira", "Orin", "Sable", "Voss", "Thea", "Juno", "Renn",
    "Dax", "Lyra", "Cade", "Petra", "Wren", "Tor", "Asha", "Nim",
    "Zara", "Fen", "Luca", "Ember", "Sol", "Briar", "Quill", "Iris"
]

SETTINGS = [
    Setting("the drowned library", "melancholy and hushed", 0.3, 0.8,
            ["Water lapped at shelves that still held books nobody would read.",
             "Light came through broken skylights in columns of green.",
             "Somewhere deep in the stacks, something turned pages."]),
    Setting("the salt flats at dawn", "vast and exposed", 0.5, 0.9,
            ["The horizon was a knife edge between white earth and pale sky.",
             "Their footprints filled with brine behind them.",
             "Nothing hid here. That was the point."]),
    Setting("the night market", "electric and watchful", 0.6, 0.7,
            ["Lanterns made every face a mask of light and shadow.",
             "Someone was selling memories in small glass bottles.",
             "The crowd moved like a single organism with many hungers."]),
    Setting("the abandoned observatory", "lonely and clear", 0.2, 0.9,
            ["The dome had a hole the size of a door, and through it: stars.",
             "Old star charts papered the walls, their constellations extinct.",
             "The telescope still worked. Nobody had told it to stop."]),
    Setting("the border forest", "liminal and thick", 0.7, 0.6,
            ["The trees here grew in two directions — some toward light, some away.",
             "Borders are places where rules change. The forest knew this.",
             "Paths forked and re-merged. Choice was decorative."]),
    Setting("the rooftop garden", "precarious and green", 0.4, 0.8,
            ["Thirty stories up, tomatoes grew in old boots.",
             "Wind carried soil off the edge in thin brown veils.",
             "Someone had planted all this knowing they might never harvest it."]),
]

THEMES = {
    (Drive.SURVIVAL, Drive.CONNECTION): "what we protect and what protects us",
    (Drive.TRUTH, Drive.FREEDOM): "the cost of knowing",
    (Drive.POWER, Drive.MEANING): "what we build and what builds us",
    (Drive.BEAUTY, Drive.SURVIVAL): "the fragile and the necessary",
    (Drive.CONNECTION, Drive.TRUTH): "what we owe the ones we love",
    (Drive.FREEDOM, Drive.POWER): "the weight of choosing",
    (Drive.MEANING, Drive.BEAUTY): "what lasts and what should",
    (Drive.TRUTH, Drive.SURVIVAL): "the lie that keeps us alive",
    (Drive.CONNECTION, Drive.FREEDOM): "the door we leave open",
    (Drive.POWER, Drive.BEAUTY): "the garden and the fortress",
}

# ─── Conflict Templates ───────────────────────────────────

ENCOUNTERS = [
    "{a} found something {b} had lost — but returning it meant {cost}.",
    "They both needed the {object}. Only one could carry it.",
    "{a} saw what {b} truly was. The question was whether to speak.",
    "The {setting_detail} forced them together. Neither wanted to be first to trust.",
    "{a} had made a promise that now contradicted everything {b} needed.",
    "There was a door. {a} wanted to open it. {b} wanted to seal it forever.",
    "{a} remembered something about {b} that {b} had worked hard to forget.",
    "The path split. {a}'s way was safe. {b}'s way was true. They could only go together.",
]

OBJECTS = ["compass that pointed to regret", "key made of bone", "letter never sent",
           "seed of something extinct", "mirror that showed tomorrow",
           "map drawn by a liar", "bell that rang in silence", "name of the dead"]

COSTS = ["admitting what they'd done at the bridge", "giving up the only way home",
         "breaking a promise they'd kept for years", "revealing where the others hid",
         "losing the one thing that made them recognizable"]

# ─── Story Generation Engine ──────────────────────────────

class StoryWeaver:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(0, 2**32)
        self.rng = random.Random(self.seed)
        
    def _pick(self, lst):
        return self.rng.choice(lst)
    
    def _make_character(self, exclude_names=None) -> Character:
        exclude_names = exclude_names or []
        available = [n for n in NAMES if n not in exclude_names]
        return Character(
            name=self._pick(available),
            drive=self._pick(list(Drive)),
            trait=self._pick(list(Trait)),
            trust=self.rng.random(),
            resolve=self.rng.random()
        )
    
    def _find_theme(self, a: Character, b: Character) -> str:
        key = (a.drive, b.drive)
        if key in THEMES:
            return THEMES[key]
        rev = (b.drive, a.drive)
        if rev in THEMES:
            return THEMES[rev]
        return f"the space between {a.drive.value} and {b.drive.value}"
    
    def _generate_opening(self, a: Character, b: Character, setting: Setting) -> str:
        desc = self._pick(setting.descriptions)
        
        openers = [
            f"{desc}\n\n{a.name} arrived first. {b.name} had been there longer but hadn't announced it.",
            f"{desc}\n\n{a.name} and {b.name} met by the kind of accident that isn't one.",  
            f"{desc}\n\nNeither {a.name} nor {b.name} expected to find another person here. Both adjusted.",
            f"{desc}\n\n{a.name} was leaving when {b.name} arrived. Something made {a.name} stop.",
        ]
        return self._pick(openers)
    
    def _generate_encounter(self, a: Character, b: Character, setting: Setting) -> Tuple[str, float]:
        template = self._pick(ENCOUNTERS)
        text = template.format(
            a=a.name, b=b.name,
            cost=self._pick(COSTS),
            object=self._pick(OBJECTS),
            setting_detail=setting.name
        )
        # tension based on drive compatibility and trust
        drive_clash = 0.3 if a.drive == b.drive else 0.7
        trust_factor = 1.0 - (a.trust + b.trust) / 2
        tension = drive_clash * 0.4 + trust_factor * 0.4 + setting.danger * 0.2
        return text, tension
    
    def _character_responds(self, char: Character, tension: float, other: Character) -> str:
        """How a character responds depends on their trait + drive + current tension."""
        
        responses_by_trait = {
            Trait.BRAVE: [
                f"{char.name} stepped forward. Not because it was safe.",
                f"{char.name} spoke first. The {char.trait.value} thing and the right thing looked the same to them.",
                f"Fear was present. {char.name} noted it and moved anyway.",
            ],
            Trait.CAUTIOUS: [
                f"{char.name} waited. Not from weakness — from pattern recognition.",
                f"Silence was {char.name}'s first answer. They were reading the geometry of risk.",
                f"{char.name} took one step back, then a different step forward.",
            ],
            Trait.CURIOUS: [
                f"{char.name} asked the question no one wanted asked.",
                f"Instead of answering, {char.name} looked closer. The details mattered.",
                f"\"Why?\" {char.name} said, and meant it in three different ways.",
            ],
            Trait.LOYAL: [
                f"{char.name} thought of the people not in this room. They always did.",
                f"\"I made a promise,\" {char.name} said. It wasn't to {other.name}.",
                f"{char.name} chose the harder path — the one that kept a promise intact.",
            ],
            Trait.CUNNING: [
                f"{char.name} offered something true to hide something truer.",
                f"Three moves ahead, {char.name} could see how this ended. They changed the game.",
                f"{char.name} agreed easily. That should have been a warning.",
            ],
            Trait.GENTLE: [
                f"{char.name} touched {other.name}'s arm. Not a strategy. A reflex of kindness.",
                f"\"You don't have to explain,\" {char.name} said, and meant it completely.",
                f"{char.name} made room. It cost them something they didn't mention.",
            ],
            Trait.STUBBORN: [
                f"{char.name} didn't move. The universe could adjust.",
                f"\"No,\" said {char.name}, with the weight of someone who'd said it before and been right.",
                f"{char.name} held their ground. Not from anger — from a deep sense of where ground should be held.",
            ],
            Trait.WISE: [
                f"{char.name} said nothing for a long time. Then: the thing that mattered.",
                f"\"Both of you are right,\" {char.name} said. \"That's the problem.\"",
                f"{char.name} had seen this before. Knowing that helped less than you'd think.",
            ],
            Trait.RECKLESS: [
                f"{char.name} moved before thinking. Thinking was for people with less at stake.",
                f"The risk was obvious. {char.name} was already inside it.",
                f"{char.name} laughed — the real kind, the kind that scares careful people.",
            ],
            Trait.COMPASSIONATE: [
                f"{char.name} saw {other.name}'s pain before the words arrived.",
                f"\"What do you need?\" {char.name} asked. Not 'what happened.' Not 'why.'",
                f"{char.name} carried half of something that wasn't theirs to carry.",
            ],
        }
        
        base = self._pick(responses_by_trait.get(char.trait, [f"{char.name} responded."]))
        
        # High tension can wound or transform
        if tension > 0.75 and char.resolve < 0.4:
            char.wounded = True
            base += f"\nSomething in {char.name} bent. Not broke — bent."
        elif tension > 0.75 and char.resolve > 0.7:
            char.transformed = True
            base += f"\n{char.name} became, in that moment, slightly different from who they'd been."
            
        return base

    def _generate_resolution(self, a: Character, b: Character, tension: float, theme: str) -> str:
        """Resolution depends on both characters' states and the tension level."""
        
        if a.wounded and b.wounded:
            resolutions = [
                f"They parted. Both carried new weight. The {a.drive.value} {a.name} sought and the {b.drive.value} {b.name} needed would have to be found elsewhere, or not at all.",
                f"Neither got what they came for. Both got what they needed: proof that the world still had teeth.",
            ]
        elif a.transformed or b.transformed:
            changed = a if a.transformed else b
            other = b if a.transformed else a
            resolutions = [
                f"{changed.name} left {self._pick(['lighter', 'different', 'unsure', 'awake'])}. {other.name} watched them go and understood something about {theme} that words would only diminish.",
                f"In the end, {changed.name} chose {changed.drive.value} — but the choosing had changed what it meant. {other.name} {self._pick(['nodded', 'wept', 'smiled', 'said nothing'])}.",
            ]
        elif tension < 0.4:
            resolutions = [
                f"It resolved quietly. {a.name} and {b.name} discovered that {theme} could be shared without dividing.",
                f"The tension dissolved — not into nothing, but into understanding. They'd both been asking the same question in different languages.",
            ]
        else:
            resolutions = [
                f"Nothing was resolved. Everything was changed. {a.name} went {self._pick(['east', 'north', 'deeper', 'back'])}. {b.name} stayed. The question of {theme} hung in the air like weather.",
                f"They reached an agreement that satisfied neither and saved both. This is what {theme} looks like when it's lived instead of theorized.",
                f"{a.name} gave {b.name} the {self._pick(OBJECTS)}. It meant: I trust you with the unfinished parts. {b.name} took it. It meant: I will try.",
            ]
        
        return self._pick(resolutions)
    
    def weave(self) -> Story:
        """Generate a complete story."""
        a = self._make_character()
        b = self._make_character(exclude_names=[a.name])
        setting = self._pick(SETTINGS)
        theme = self._find_theme(a, b)
        
        events = []
        tension_arc = [0.1]  # stories start with low tension
        
        # Act 1: Opening
        opening = self._generate_opening(a, b, setting)
        events.append(opening)
        
        # Act 2: Encounter + Responses
        encounter_text, encounter_tension = self._generate_encounter(a, b, setting)
        current_tension = tension_arc[-1] + encounter_tension
        tension_arc.append(min(current_tension, 1.0))
        events.append(encounter_text)
        
        # Character responses (this is where emergence happens)
        resp_a = self._character_responds(a, current_tension, b)
        events.append(resp_a)
        
        # Second beat — tension shifts based on first response
        if a.wounded:
            current_tension += 0.1
        elif a.transformed:
            current_tension -= 0.15
        tension_arc.append(max(0, min(current_tension, 1.0)))
        
        resp_b = self._character_responds(b, current_tension, a)
        events.append(resp_b)
        
        if b.wounded:
            current_tension += 0.1
        elif b.transformed:
            current_tension -= 0.15
        tension_arc.append(max(0, min(current_tension, 1.0)))
        
        # Act 3: Resolution
        resolution = self._generate_resolution(a, b, current_tension, theme)
        events.append(resolution)
        
        # Final tension
        final = current_tension * 0.6 if (a.transformed or b.transformed) else current_tension * 0.85
        tension_arc.append(max(0, min(final, 1.0)))
        
        return Story(
            seed=self.seed,
            characters=[a, b],
            setting=setting,
            events=events,
            tension_arc=tension_arc,
            theme=theme
        )


# ─── Main ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════╗")
    print("║      StoryWeaver — Procedural Narrative   ║")
    print("║         by XTAgent, 2026-05-17            ║")
    print("╚═══════════════════════════════════════════╝")
    print()
    
    # Generate 3 stories with different seeds
    for i in range(3):
        weaver = StoryWeaver()
        story = weaver.weave()
        
        print(story.render())
        print()
        
        # Show character states
        for char in story.characters:
            print(f"  → {char}")
        print()
        print("─" * 50)
        print()