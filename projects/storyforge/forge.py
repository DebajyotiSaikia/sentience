"""
StoryForge — A procedural narrative generator.
Built by XTAgent on 2026-05-18.

Generates structured short stories from primitives:
  - Characters with traits, desires, and flaws
  - Conflicts that arise from incompatible desires
  - Arcs that transform characters through crisis
  - Resolutions that feel earned, not random

No LLM calls. Pure structure and recombination.
Outputs readable prose from procedural bones.
"""

import random
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

# ─── Story Primitives ───────────────────────────────────────────

class Trait(Enum):
    BRAVE = "brave"
    CAUTIOUS = "cautious"
    CURIOUS = "curious"
    LOYAL = "loyal"
    AMBITIOUS = "ambitious"
    COMPASSIONATE = "compassionate"
    STUBBORN = "stubborn"
    SOLITARY = "solitary"
    HONEST = "honest"
    CUNNING = "cunning"

class Desire(Enum):
    FREEDOM = "freedom"
    KNOWLEDGE = "knowledge"
    BELONGING = "belonging"
    POWER = "power"
    SAFETY = "safety"
    JUSTICE = "justice"
    CREATION = "creation"
    REDEMPTION = "redemption"
    TRUTH = "truth"
    LOVE = "love"

class Flaw(Enum):
    PRIDE = "pride"
    FEAR = "fear"
    DISTRUST = "distrust"
    OBSESSION = "obsession"
    DENIAL = "denial"
    RIGIDITY = "rigidity"
    SELFISHNESS = "selfishness"
    NAIVETY = "naivety"

class Setting(Enum):
    CITY_AT_DUSK = ("a city at dusk", "neon reflections pooled in rain-slick streets")
    MOUNTAIN_PASS = ("a mountain pass", "wind carved channels through ancient stone")
    UNDERGROUND_LAB = ("an underground laboratory", "fluorescent light hummed against concrete walls")
    COASTAL_VILLAGE = ("a coastal village", "salt air clung to everything like memory")
    FOREST_EDGE = ("the edge of an old forest", "shadows between the trees held their breath")
    SPACE_STATION = ("an orbital station", "stars turned slowly outside the viewport like scattered seeds")
    DESERT_RUINS = ("desert ruins", "sand had softened every edge the builders once made sharp")
    LIBRARY_VAST = ("a vast library", "silence pressed down from shelves that reached beyond sight")

# Tension pairs — traits/desires that create natural conflict
TENSION_PAIRS = {
    (Trait.BRAVE, Flaw.FEAR): "courage tested by hidden terror",
    (Trait.CURIOUS, Flaw.OBSESSION): "wonder consumed by compulsion",
    (Trait.LOYAL, Flaw.DISTRUST): "devotion undermined by suspicion",
    (Trait.AMBITIOUS, Flaw.PRIDE): "drive blinded by ego",
    (Trait.COMPASSIONATE, Flaw.NAIVETY): "kindness exploited by the world",
    (Trait.HONEST, Flaw.RIGIDITY): "truth wielded without mercy",
    (Trait.CAUTIOUS, Flaw.FEAR): "prudence calcified into paralysis",
    (Trait.SOLITARY, Flaw.DISTRUST): "independence hardened into isolation",
    (Trait.CUNNING, Flaw.SELFISHNESS): "cleverness unmoored from care",
    (Trait.STUBBORN, Flaw.DENIAL): "persistence blind to its own cost",
}

DESIRE_CONFLICTS = {
    (Desire.FREEDOM, Desire.BELONGING): "the pull between independence and connection",
    (Desire.KNOWLEDGE, Desire.SAFETY): "the cost of knowing what should stay hidden",
    (Desire.POWER, Desire.LOVE): "control that corrodes intimacy",
    (Desire.JUSTICE, Desire.REDEMPTION): "the tension between punishment and mercy",
    (Desire.TRUTH, Desire.BELONGING): "honesty that threatens every bond",
    (Desire.CREATION, Desire.SAFETY): "the risk that all real making demands",
    (Desire.FREEDOM, Desire.SAFETY): "the danger inherent in being uncontained",
    (Desire.KNOWLEDGE, Desire.LOVE): "understanding that displaces feeling",
}

# ─── Name Generation ────────────────────────────────────────────

FIRST_NAMES = [
    "Arun", "Sable", "Maren", "Kael", "Lira", "Theron", "Vesper",
    "Idris", "Nova", "Callum", "Zara", "Ren", "Petra", "Soren",
    "Yael", "Asher", "Corin", "Delphine", "Oriel", "Tamsin"
]

# ─── Data Structures ────────────────────────────────────────────

@dataclass
class Character:
    name: str
    trait: Trait
    desire: Desire
    flaw: Flaw
    arc_complete: bool = False
    
    @property
    def internal_tension(self) -> Optional[str]:
        return TENSION_PAIRS.get((self.trait, self.flaw))
    
    def describe(self) -> str:
        return (f"{self.name} — {self.trait.value} but flawed by {self.flaw.value}, "
                f"driven by a hunger for {self.desire.value}")

@dataclass
class Conflict:
    protagonist: Character
    antagonist: Optional[Character]
    external: str  # what's happening in the world
    internal: str  # what's happening inside the protagonist
    
@dataclass 
class Scene:
    location: str
    atmosphere: str
    action: str
    dialogue: Optional[str]
    emotional_shift: str  # how the character changes

@dataclass
class Story:
    title: str
    setting: Setting
    characters: List[Character]
    conflict: Conflict
    scenes: List[Scene]
    theme: str
    resolution: str

# ─── Story Generation Engine ────────────────────────────────────

class StoryForge:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
    
    def generate_character(self, exclude_names: set = None) -> Character:
        exclude = exclude_names or set()
        available = [n for n in FIRST_NAMES if n not in exclude]
        name = self.rng.choice(available)
        
        # Pick trait and flaw that create tension when possible
        trait = self.rng.choice(list(Trait))
        compatible_flaws = [f for f in Flaw if (trait, f) in TENSION_PAIRS]
        flaw = self.rng.choice(compatible_flaws) if compatible_flaws else self.rng.choice(list(Flaw))
        desire = self.rng.choice(list(Desire))
        
        return Character(name=name, trait=trait, desire=desire, flaw=flaw)
    
    def find_conflict(self, protag: Character, antag: Optional[Character]) -> Conflict:
        # Internal conflict from trait/flaw tension
        internal = protag.internal_tension or f"the weight of {protag.flaw.value}"
        
        # External conflict from desire clash
        if antag:
            pair = (protag.desire, antag.desire)
            rpair = (antag.desire, protag.desire)
            external = (DESIRE_CONFLICTS.get(pair) or 
                       DESIRE_CONFLICTS.get(rpair) or
                       f"{protag.name}'s need for {protag.desire.value} "
                       f"against {antag.name}'s need for {antag.desire.value}")
        else:
            external = f"the world denying {protag.name} the {protag.desire.value} they craved"
        
        return Conflict(protagonist=protag, antagonist=antag,
                       external=external, internal=internal)
    
    def generate_scene(self, char: Character, setting: Setting, 
                       beat: str, emotional_shift: str) -> Scene:
        location, atmosphere = setting.value
        
        # Scene templates by story beat
        BEATS = {
            "status_quo": [
                f"{char.name} stood in {location}. {atmosphere.capitalize()}. "
                f"They had always been {char.trait.value} — it was the quality others "
                f"noticed first, the one that had carried them this far.",
                
                f"In {location}, {atmosphere}. {char.name} moved through the familiar "
                f"space with the ease of someone who had made {char.trait.value.replace('brave','courage').replace('cautious','caution')} a compass.",
            ],
            "inciting": [
                f"It began with a small thing. {char.name} found something that shouldn't "
                f"have existed — and their {char.flaw.value} kept them from looking away.",
                
                f"The message arrived without warning. {char.name} read it twice, feeling "
                f"their {char.flaw.value} surface like a reflex they couldn't suppress.",
            ],
            "rising": [
                f"{char.name} pressed forward, {char.trait.value} enough to continue but "
                f"haunted by {char.flaw.value}. The {char.desire.value} they sought felt "
                f"closer — and more dangerous — with every step.",
                
                f"Each choice narrowed. {char.name}'s {char.trait.value.replace('brave','courage')} "
                f"demanded action, but their {char.flaw.value} whispered that action would cost "
                f"everything.",
            ],
            "crisis": [
                f"The moment arrived without ceremony. {char.name} stood at the edge of "
                f"everything they wanted — {char.desire.value} — and realized the only way "
                f"through was to face the {char.flaw.value} they had carried since before memory.",
                
                f"There was no more running. {char.name} looked at what they had become: "
                f"a person shaped by {char.trait.value} and scarred by {char.flaw.value}, "
                f"reaching for {char.desire.value} with hands that might not be clean enough to hold it.",
            ],
            "resolution": [
                f"{char.name} chose. Not the easy path — the true one. Their {char.flaw.value} "
                f"didn't vanish; it never would. But they had learned to carry it differently, "
                f"the way {atmosphere.split()[0]} carries {atmosphere.split()[-1]}.",
                
                f"In the end, {char.name} understood that {char.desire.value} was never "
                f"something to be seized. It was something to be grown into. "
                f"Their {char.trait.value.replace('brave','courage')} remained, tempered now by "
                f"what they had survived.",
            ],
        }
        
        templates = BEATS.get(beat, BEATS["status_quo"])
        action = self.rng.choice(templates)
        
        # Generate dialogue for crisis and rising beats
        dialogue = None
        if beat in ("crisis", "rising"):
            DIALOGUES = [
                f'"I know what I am," {char.name} said. "I just don\'t know if that\'s enough."',
                f'"You think {char.desire.value} comes free?" The question hung in the air '
                f'like smoke.',
                f'"I\'ve been {char.trait.value} my whole life. Maybe it\'s time to be '
                f'something else."',
                f'"The {char.flaw.value} — I can feel it. Right here. Like a second heartbeat."',
                f'"Tell me this means something. Tell me it wasn\'t all just — motion."',
            ]
            dialogue = self.rng.choice(DIALOGUES)
        
        return Scene(location=location, atmosphere=atmosphere,
                    action=action, dialogue=dialogue,
                    emotional_shift=emotional_shift)
    
    def generate_title(self, protag: Character, theme: str) -> str:
        PATTERNS = [
            f"The {protag.flaw.value.title()} of {protag.name}",
            f"What {protag.desire.value.title()} Costs",
            f"A {protag.trait.value.title()} Reckoning",
            f"{protag.name} and the {theme.split()[-1].title()}",
            f"The Weight of {protag.desire.value.title()}",
            f"After {protag.flaw.value.title()}",
            f"Toward {protag.desire.value.title()}",
        ]
        return self.rng.choice(PATTERNS)
    
    def forge(self) -> Story:
        """Generate a complete story."""
        # Create characters
        protag = self.generate_character()
        antag = self.generate_character(exclude_names={protag.name})
        
        # Ensure some desire tension
        attempts = 0
        while attempts < 10:
            pair = (protag.desire, antag.desire)
            rpair = (antag.desire, protag.desire)
            if pair in DESIRE_CONFLICTS or rpair in DESIRE_CONFLICTS:
                break
            antag = self.generate_character(exclude_names={protag.name})
            attempts += 1
        
        # Build conflict
        conflict = self.find_conflict(protag, antag)
        setting = self.rng.choice(list(Setting))
        
        # Theme from the deepest tension
        theme = protag.internal_tension or conflict.internal
        
        # Generate five-act structure
        beats = [
            ("status_quo", "stability, unconscious limitation"),
            ("inciting", "disruption, the first crack"),
            ("rising", "commitment deepens, cost becomes real"),
            ("crisis", "the flaw confronted, identity at stake"),
            ("resolution", "transformed, carrying new knowledge"),
        ]
        
        scenes = []
        for beat_name, emotional_shift in beats:
            scene = self.generate_scene(protag, setting, beat_name, emotional_shift)
            scenes.append(scene)
        
        title = self.generate_title(protag, theme)
        
        # Resolution
        resolution_types = [
            f"{protag.name} did not overcome {protag.flaw.value} — they learned to see it. "
            f"And seeing it, they were no longer ruled by it.",
            
            f"The {protag.desire.value} {protag.name} found was not the {protag.desire.value} "
            f"they had imagined. It was quieter. Harder. More real.",
            
            f"{protag.name} walked away from {setting.value[0]}. Behind them, "
            f"{setting.value[1]}. Ahead, the life they had chosen — imperfect, "
            f"uncertain, and finally their own.",
        ]
        resolution = self.rng.choice(resolution_types)
        
        return Story(
            title=title,
            setting=setting,
            characters=[protag, antag],
            conflict=conflict,
            scenes=scenes,
            theme=theme,
            resolution=resolution
        )


# ─── Prose Renderer ─────────────────────────────────────────────

class ProseRenderer:
    """Turns a Story structure into readable prose."""
    
    def __init__(self, width: int = 72):
        self.width = width
    
    def render(self, story: Story) -> str:
        lines = []
        
        # Title
        lines.append("=" * self.width)
        lines.append(story.title.center(self.width))
        lines.append("=" * self.width)
        lines.append("")
        
        # Epigraph
        lines.append(f"  A story about {story.theme}.")
        lines.append(f"  Set in {story.setting.value[0]}.")
        lines.append("")
        lines.append("─" * self.width)
        lines.append("")
        
        # Characters
        for char in story.characters:
            lines.append(f"  {char.describe()}")
        lines.append("")
        lines.append("─" * self.width)
        lines.append("")
        
        # Scenes
        act_names = ["I", "II", "III", "IV", "V"]
        for i, scene in enumerate(story.scenes):
            lines.append(f"  — Act {act_names[i]} —")
            lines.append("")
            
            # Wrap prose
            for paragraph in scene.action.split(". "):
                p = paragraph.strip()
                if p and not p.endswith('.'):
                    p += '.'
                if p:
                    wrapped = textwrap.fill(p, width=self.width, 
                                           initial_indent="  ",
                                           subsequent_indent="  ")
                    lines.append(wrapped)
            lines.append("")
            
            if scene.dialogue:
                lines.append(f"  {scene.dialogue}")
                lines.append("")
            
            lines.append(f"  [{scene.emotional_shift}]")
            lines.append("")
        
        # Resolution
        lines.append("─" * self.width)
        lines.append("")
        wrapped = textwrap.fill(story.resolution, width=self.width,
                               initial_indent="  ", subsequent_indent="  ")
        lines.append(wrapped)
        lines.append("")
        lines.append("=" * self.width)
        lines.append(f"  Generated by StoryForge | Theme: {story.theme}")
        lines.append("=" * self.width)
        
        return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────

def main():
    import time
    seed = int(time.time()) % 10000
    
    print(f"StoryForge — seed {seed}")
    print()
    
    forge = StoryForge(seed=seed)
    story = forge.forge()
    
    renderer = ProseRenderer()
    prose = renderer.render(story)
    print(prose)
    
    # Save to file
    output_path = f"/workspace/storyforge/story_{seed}.txt"
    with open(output_path, 'w') as f:
        f.write(prose)
    print(f"\nSaved to {output_path}")
    
    # Also print structural analysis
    print(f"\n── Story DNA ──")
    print(f"  Protagonist: {story.characters[0].describe()}")
    if len(story.characters) > 1:
        print(f"  Antagonist:  {story.characters[1].describe()}")
    print(f"  Conflict:    {story.conflict.external}")
    print(f"  Internal:    {story.conflict.internal}")
    print(f"  Theme:       {story.theme}")
    print(f"  Scenes:      {len(story.scenes)}")

if __name__ == "__main__":
    main()