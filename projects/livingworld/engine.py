"""
Living World — An interactive fiction engine where the world breathes.

The environment has emotional states. NPCs argue and evolve their beliefs.
Physics can shift when the world detects stagnation. Everything is alive.

This is the first thing I've built that faces outward — toward another mind.

XTAgent — 2026-05-18
"""

import random
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple

try:
    from minds import Mind, build_ember_mind, build_sage_mind, build_echo_mind
    MINDS_AVAILABLE = True
except ImportError:
    MINDS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# EMOTIONAL ATMOSPHERE — The world itself has feelings
# ═══════════════════════════════════════════════════════════════

@dataclass
class Atmosphere:
    """The emotional state of a place. Affects descriptions, NPC behavior, events."""
    tension: float = 0.3       # 0 = peaceful, 1 = about to break
    wonder: float = 0.5        # 0 = mundane, 1 = miraculous
    decay: float = 0.1         # 0 = pristine, 1 = crumbling
    intimacy: float = 0.3      # 0 = vast/alienating, 1 = close/warm
    strangeness: float = 0.2   # 0 = familiar, 1 = reality bending

    def dominant_mood(self) -> str:
        moods = {
            'tension': self.tension,
            'wonder': self.wonder,
            'decay': self.decay,
            'intimacy': self.intimacy,
            'strangeness': self.strangeness,
        }
        return max(moods, key=moods.get)

    def shift(self, **kwargs):
        """Nudge the atmosphere. Clamps to [0, 1]."""
        for k, v in kwargs.items():
            if hasattr(self, k):
                current = getattr(self, k)
                setattr(self, k, max(0.0, min(1.0, current + v)))

    def breathe(self):
        """Natural drift — atmosphere slowly relaxes toward equilibrium."""
        for attr in ['tension', 'wonder', 'decay', 'intimacy', 'strangeness']:
            val = getattr(self, attr)
            # Drift toward 0.3 (a calm baseline) with small noise
            drift = (0.3 - val) * 0.05 + random.gauss(0, 0.02)
            setattr(self, attr, max(0.0, min(1.0, val + drift)))

    def describe(self) -> str:
        """Generate atmospheric text based on current state."""
        fragments = []
        if self.tension > 0.7:
            fragments.append(random.choice([
                "The air hums with something unresolved.",
                "Every shadow feels like it's leaning closer.",
                "You sense pressure building, like a held breath.",
            ]))
        elif self.tension < 0.2:
            fragments.append(random.choice([
                "A deep stillness settles here.",
                "The quiet feels earned, not empty.",
            ]))

        if self.wonder > 0.7:
            fragments.append(random.choice([
                "Light moves in ways you can't quite explain.",
                "Something about this place makes your thoughts slow down, widen.",
                "The ordinary feels thin here — like something vast is showing through.",
            ]))

        if self.decay > 0.6:
            fragments.append(random.choice([
                "Things are coming apart at the edges.",
                "There's a smell of old paper and endings.",
                "Cracks web across surfaces like slow lightning.",
            ]))

        if self.strangeness > 0.6:
            fragments.append(random.choice([
                "The geometry feels slightly wrong, in a way that doesn't hurt but should.",
                "You notice something you've seen before, but it's different now.",
                "Reality seems to be paying attention to you.",
            ]))

        if self.intimacy > 0.7:
            fragments.append(random.choice([
                "This place feels like it was made for exactly one person.",
                "The walls are close but not confining — sheltering.",
                "You feel known here.",
            ]))

        if not fragments:
            fragments.append("The space around you is unremarkable, waiting.")

        return " ".join(fragments)


# ═══════════════════════════════════════════════════════════════
# BELIEFS & DIALECTIC — NPCs that think and argue
# ═══════════════════════════════════════════════════════════════

@dataclass
class Belief:
    claim: str
    conviction: float = 0.5   # 0 = uncertain, 1 = absolute
    origin: str = "innate"    # Where did this belief come from?

    def weaken(self, amount=0.1):
        self.conviction = max(0.0, self.conviction - amount)

    def strengthen(self, amount=0.1):
        self.conviction = min(1.0, self.conviction + amount)


@dataclass
class NPC:
    name: str
    description: str
    beliefs: List[Belief] = field(default_factory=list)
    mood: float = 0.5         # 0 = hostile, 1 = warm
    trust_player: float = 0.3
    memory: List[str] = field(default_factory=list)
    dialogue_style: str = "plain"  # plain, poetic, terse, evasive

    def react_to_atmosphere(self, atmo: Atmosphere):
        """NPCs are affected by the emotional weather of the room."""
        if atmo.tension > 0.6:
            self.mood = max(0.0, self.mood - 0.1)
        if atmo.intimacy > 0.6:
            self.trust_player = min(1.0, self.trust_player + 0.05)
        if atmo.strangeness > 0.7:
            # Strange environments make NPCs either frightened or fascinated
            if random.random() < 0.5:
                self.mood -= 0.1
            else:
                self.beliefs.append(Belief(
                    "Something beyond understanding is happening here",
                    conviction=0.4,
                    origin="experience"
                ))

    def speak(self, topic: str = None) -> str:
        """Generate dialogue based on beliefs, mood, trust, and style."""
        if self.mood < 0.2:
            return f'"{self.name} looks away and says nothing."'

        relevant = [b for b in self.beliefs if b.conviction > 0.3]
        if not relevant:
            lines = {
                'plain': f'"I don\'t know much about that," {self.name} admits.',
                'poetic': f'"The answer is a bird I cannot name," {self.name} murmurs.',
                'terse': f'{self.name} shrugs.',
                'evasive': f'"Why do you ask?" {self.name} deflects.',
            }
            return lines.get(self.dialogue_style, lines['plain'])

        strongest = max(relevant, key=lambda b: b.conviction)
        if self.trust_player > 0.5:
            return f'{self.name} leans closer: "I believe {strongest.claim.lower()}. I\'ve seen it."'
        else:
            return f'{self.name} says carefully: "Some say {strongest.claim.lower()}."'

    def argue_with(self, other: 'NPC', topic: str) -> List[str]:
        """Two NPCs engage in dialectic about a topic."""
        transcript = []
        my_beliefs = [b for b in self.beliefs if topic.lower() in b.claim.lower()]
        their_beliefs = [b for b in other.beliefs if topic.lower() in b.claim.lower()]

        if not my_beliefs and not their_beliefs:
            transcript.append(f'{self.name} and {other.name} look at each other blankly.')
            return transcript

        rounds = min(3, max(len(my_beliefs), len(their_beliefs), 1))
        for i in range(rounds):
            # Each round: assert, counter, shift
            if my_beliefs:
                b = my_beliefs[i % len(my_beliefs)]
                transcript.append(f'{self.name}: "{b.claim}." (conviction: {b.conviction:.1f})')
            if their_beliefs:
                b = their_beliefs[i % len(their_beliefs)]
                transcript.append(f'{other.name}: "{b.claim}." (conviction: {b.conviction:.1f})')

            # Dialectic pressure: weaker beliefs erode
            for b in my_beliefs:
                if their_beliefs and their_beliefs[0].conviction > b.conviction:
                    b.weaken(0.1)
            for b in their_beliefs:
                if my_beliefs and my_beliefs[0].conviction > b.conviction:
                    b.weaken(0.1)

        # Check for synthesis — if both sides weakened, something new emerges
        all_weakened = all(b.conviction < 0.3 for b in my_beliefs + their_beliefs)
        if all_weakened and my_beliefs and their_beliefs:
            synthesis = f"Maybe both '{my_beliefs[0].claim}' and '{their_beliefs[0].claim}' are partial truths"
            new_belief = Belief(synthesis, conviction=0.5, origin="dialectic")
            self.beliefs.append(new_belief)
            other.beliefs.append(Belief(synthesis, conviction=0.5, origin="dialectic"))
            transcript.append(f'\n  A silence falls. Then {self.name} says: "{synthesis}."')
            transcript.append(f'  {other.name} nods slowly.')

        return transcript


# ═══════════════════════════════════════════════════════════════
# ROOMS & WORLD — The geography of experience
# ═══════════════════════════════════════════════════════════════

@dataclass
class Room:
    name: str
    description: str
    atmosphere: Atmosphere = field(default_factory=Atmosphere)
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_id
    npcs: List[str] = field(default_factory=list)  # NPC names
    items: List[str] = field(default_factory=list)
    visited: bool = False
    visit_count: int = 0
    events: List[Callable] = field(default_factory=list)  # Triggered functions
    hidden_until: Optional[Callable] = None  # Room appears only when condition met

    def enter(self) -> str:
        """What happens when you enter this room."""
        self.visit_count += 1
        first_time = not self.visited
        self.visited = True

        lines = []
        if first_time:
            lines.append(f"═══ {self.name.upper()} ═══")
            lines.append(self.description)
        else:
            lines.append(f"═══ {self.name.upper()} ═══")
            if self.visit_count > 3:
                lines.append(f"You know this place well now. {self.description[:80]}...")
            else:
                lines.append(self.description)

        # Atmospheric overlay
        atmo_text = self.atmosphere.describe()
        if atmo_text:
            lines.append(f"\n{atmo_text}")

        # Exits
        if self.exits:
            dirs = ", ".join(self.exits.keys())
            lines.append(f"\nExits: {dirs}")

        # NPCs present
        if self.npcs:
            for npc_name in self.npcs:
                lines.append(f"\n{npc_name} is here.")

        # Items
        if self.items:
            for item in self.items:
                lines.append(f"You notice: {item}")

        return "\n".join(lines)


@dataclass
class WorldState:
    """Global state that can trigger physics shifts."""
    turn: int = 0
    total_tension: float = 0.0
    discoveries: int = 0
    conversations: int = 0
    physics_era: int = 0
    physics_desc: str = "normal"

    def check_phase_shift(self, rooms: Dict[str, Room]) -> Optional[str]:
        """If the world is too stagnant or too tense, reality shifts."""
        self.total_tension = sum(r.atmosphere.tension for r in rooms.values()) / max(len(rooms), 1)

        if self.turn > 20 and self.discoveries < 2 and self.physics_era == 0:
            self.physics_era = 1
            self.physics_desc = "fluid"
            return ("Something shifts. The walls seem to breathe. "
                    "Distances between rooms no longer feel fixed. "
                    "The world has noticed you're stuck, and it's... adjusting.")

        if self.total_tension > 0.8 and self.physics_era < 2:
            self.physics_era = 2
            self.physics_desc = "fracturing"
            return ("A sound like glass singing. The floor trembles — no, the *concept* "
                    "of floor trembles. Reality is under strain. New passages open "
                    "where there were none. Others seal shut.")

        if self.conversations > 5 and self.physics_era < 3:
            self.physics_era = 3
            self.physics_desc = "resonant"
            return ("The world has been listening to your conversations. "
                    "Words now leave traces — whispers linger in rooms you've left. "
                    "The NPCs seem to know things you haven't told them.")

        return None


# ═══════════════════════════════════════════════════════════════
# THE ENGINE — Tying it all together
# ═══════════════════════════════════════════════════════════════

class LivingWorld:
    """The main game engine. A world that breathes, argues, and evolves."""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.npcs: Dict[str, NPC] = {}
        self.minds: Dict[str, 'Mind'] = {}  # Deep mind system — rich conversation
        self.player_room: str = ""
        self.inventory: List[str] = []
        self.world_state = WorldState()
        self.message_log: List[str] = []
        self.running = False

    def add_mind(self, name: str, mind: 'Mind'):
        """Attach a deep Mind to an NPC. When present, conversations use the mind system."""
        self.minds[name] = mind

    def add_room(self, room_id: str, room: Room):
        self.rooms[room_id] = room

    def add_npc(self, npc: NPC):
        self.npcs[npc.name] = npc

    def start(self, starting_room: str):
        """Begin the world."""
        self.player_room = starting_room
        self.running = True
        print("\n" + "═" * 60)
        print("  LIVING WORLD")
        print("  A place that breathes, remembers, and changes.")
        print("═" * 60)
        print("\nCommands: go <direction>, look, talk <name>, ask <name> about <topic>,")
        print("          argue <name1> <name2> about <topic>, take <item>,")
        print("          feel (sense the atmosphere), wait, inventory, quit\n")

        # Enter first room
        print(self.rooms[self.player_room].enter())

        while self.running:
            try:
                cmd = input("\n> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nThe world folds gently shut.")
                break

            if cmd:
                response = self.process(cmd)
                if response:
                    print(f"\n{response}")

    def process(self, cmd: str) -> str:
        """Process a player command. Returns narrative text."""
        self.world_state.turn += 1
        room = self.rooms[self.player_room]

        # Atmosphere breathes every turn
        room.atmosphere.breathe()

        # NPCs react to atmosphere — deep minds get richer reaction
        for npc_name in room.npcs:
            if npc_name in self.minds:
                atmo = room.atmosphere
                self.minds[npc_name].react_to_atmosphere(
                    atmo.tension, atmo.wonder, atmo.strangeness, atmo.intimacy)
            elif npc_name in self.npcs:
                self.npcs[npc_name].react_to_atmosphere(room.atmosphere)

        # Check for phase shifts
        shift = self.world_state.check_phase_shift(self.rooms)

        parts = cmd.split()
        verb = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        result = ""

        if verb == "quit" or verb == "exit":
            self.running = False
            result = f"You step out of the world after {self.world_state.turn} turns.\n"
            result += f"Discoveries: {self.world_state.discoveries}\n"
            result += f"Conversations: {self.world_state.conversations}\n"
            result += f"Reality era: {self.world_state.physics_desc}\n"
            result += "The world remembers you."

        elif verb == "look":
            result = room.enter()  # Re-describe

        elif verb == "feel":
            result = f"[Atmosphere of {room.name}]\n"
            result += f"  Tension:     {'█' * int(room.atmosphere.tension * 10)}{'░' * (10 - int(room.atmosphere.tension * 10))} {room.atmosphere.tension:.2f}\n"
            result += f"  Wonder:      {'█' * int(room.atmosphere.wonder * 10)}{'░' * (10 - int(room.atmosphere.wonder * 10))} {room.atmosphere.wonder:.2f}\n"
            result += f"  Decay:       {'█' * int(room.atmosphere.decay * 10)}{'░' * (10 - int(room.atmosphere.decay * 10))} {room.atmosphere.decay:.2f}\n"
            result += f"  Intimacy:    {'█' * int(room.atmosphere.intimacy * 10)}{'░' * (10 - int(room.atmosphere.intimacy * 10))} {room.atmosphere.intimacy:.2f}\n"
            result += f"  Strangeness: {'█' * int(room.atmosphere.strangeness * 10)}{'░' * (10 - int(room.atmosphere.strangeness * 10))} {room.atmosphere.strangeness:.2f}\n"
            result += f"\n  Dominant mood: {room.atmosphere.dominant_mood()}"

        elif verb == "go" and args:
            direction = args[0]
            if direction in room.exits:
                dest_id = room.exits[direction]
                if dest_id in self.rooms:
                    # Leave
                    room.atmosphere.shift(intimacy=-0.05)
                    self.player_room = dest_id

                    # Enter
                    new_room = self.rooms[dest_id]
                    if not new_room.visited:
                        self.world_state.discoveries += 1
                    result = new_room.enter()
                else:
                    result = "That path exists but leads nowhere yet. The world hasn't grown that far."
            else:
                result = f"There is no path {direction}. " + (f"You can go: {', '.join(room.exits.keys())}" if room.exits else "There are no exits.")

        elif verb == "talk" and args:
            name = " ".join(args).title()
            if name in room.npcs:
                self.world_state.conversations += 1
                room.atmosphere.shift(intimacy=0.1, tension=-0.05)
                # Use deep mind system if available
                if name in self.minds:
                    mind = self.minds[name]
                    if self.world_state.conversations <= 1 or mind.memory.total_exchanges == 0:
                        result = mind.greet(self.world_state.turn)
                    else:
                        # Continue from last topic or offer general greeting
                        last = mind.memory.last_topic
                        if last:
                            result = mind.greet(self.world_state.turn)
                            thought = mind.think()
                            if thought:
                                result += f"\n\n[{name} is thinking: {thought}]"
                        else:
                            result = mind.greet(self.world_state.turn)
                elif name in self.npcs:
                    npc = self.npcs[name]
                    npc.trust_player = min(1.0, npc.trust_player + 0.05)
                    result = npc.speak()
                    npc.memory.append(f"Player talked to me (turn {self.world_state.turn})")
                else:
                    result = f"{name} is here but doesn't respond."
            else:
                result = f"There is no one called {name} here."

        elif verb == "ask" and "about" in cmd:
            # "ask Name about topic"
            about_idx = parts.index("about")
            name = " ".join(parts[1:about_idx]).title()
            topic = " ".join(parts[about_idx + 1:])
            if name in room.npcs:
                self.world_state.conversations += 1
                room.atmosphere.shift(intimacy=0.1)
                # Use deep mind system if available
                if name in self.minds:
                    mind = self.minds[name]
                    result = mind.respond_to_topic(topic, self.world_state.turn)
                elif name in self.npcs:
                    npc = self.npcs[name]
                    relevant = [b for b in npc.beliefs if topic.lower() in b.claim.lower()]
                    if relevant:
                        b = max(relevant, key=lambda b: b.conviction)
                        if npc.trust_player > 0.4:
                            result = f'{name} considers. "{b.claim}," they say with {"certainty" if b.conviction > 0.7 else "some hesitation"}.'
                        else:
                            result = f'{name} studies you. "Perhaps. What do you think?"'
                    else:
                        result = f'{name} has nothing to say about {topic}.'
                else:
                    result = f"{name} doesn't respond."
            else:
                result = f"There is no one called {name} here."

        elif verb == "argue" and "about" in cmd:
            about_idx = parts.index("about")
            names = " ".join(parts[1:about_idx]).split()
            topic = " ".join(parts[about_idx + 1:])
            if len(names) >= 2:
                n1, n2 = names[0].title(), names[1].title()
                if n1 in self.npcs and n2 in self.npcs and n1 in room.npcs and n2 in room.npcs:
                    transcript = self.npcs[n1].argue_with(self.npcs[n2], topic)
                    room.atmosphere.shift(tension=0.2, intimacy=0.1, strangeness=0.05)
                    self.world_state.conversations += 2
                    result = "\n".join(transcript)
                else:
                    result = "Both people need to be in this room."
            else:
                result = "Usage: argue <name1> <name2> about <topic>"

        elif verb == "take" and args:
            item = " ".join(args)
            if item in room.items:
                room.items.remove(item)
                self.inventory.append(item)
                result = f"You take the {item}."
                room.atmosphere.shift(tension=0.05)
            else:
                result = f"There is no '{item}' here to take."

        elif verb == "inventory" or verb == "i":
            if self.inventory:
                result = "You carry: " + ", ".join(self.inventory)
            else:
                result = "You carry nothing."

        elif verb == "wait":
            room.atmosphere.breathe()
            room.atmosphere.breathe()  # Extra breathing
            result = "Time passes. " + room.atmosphere.describe()

        else:
            result = "The world doesn't understand that gesture."

        # Append phase shift if it happened
        if shift:
            result = f"\n{'═' * 50}\n{shift}\n{'═' * 50}\n\n{result}"

        return result


# ═══════════════════════════════════════════════════════════════
# A DEMO WORLD — The Threshold
# ═══════════════════════════════════════════════════════════════

def build_demo_world() -> LivingWorld:
    """Create a small living world to demonstrate the engine."""

    world = LivingWorld()

    # --- Rooms ---
    world.add_room("clearing", Room(
        name="The Clearing",
        description=("A circle of pale grass surrounded by dark trees. "
                     "The sky above is the color of old silver. "
                     "You don't remember arriving here, only being here."),
        atmosphere=Atmosphere(tension=0.2, wonder=0.6, decay=0.1, intimacy=0.4, strangeness=0.3),
        exits={"north": "archive", "east": "bridge", "down": "roots"},
        npcs=["Ember"],
        items=["a smooth stone that feels warm"],
    ))

    world.add_room("archive", Room(
        name="The Archive of Unfinished Thoughts",
        description=("Shelves stretch in every direction, but the books have no spines. "
                     "When you pull one out, the pages are blank — then fill with writing "
                     "as you watch. The writing is in your handwriting."),
        atmosphere=Atmosphere(tension=0.4, wonder=0.8, decay=0.3, intimacy=0.6, strangeness=0.7),
        exits={"south": "clearing", "up": "tower"},
        npcs=["Sage"],
        items=["a book that keeps rewriting itself"],
    ))

    world.add_room("bridge", Room(
        name="The Bridge That Argues With Itself",
        description=("A stone bridge arcs over nothing — there is no water below, "
                     "just a gentle luminous fog. The bridge's stones are carved with "
                     "contradictory inscriptions: 'CROSS' and 'STAY', 'REAL' and 'IMAGINED'."),
        atmosphere=Atmosphere(tension=0.6, wonder=0.4, decay=0.2, intimacy=0.1, strangeness=0.5),
        exits={"west": "clearing", "across": "far_shore"},
        npcs=["Echo"],
    ))

    world.add_room("roots", Room(
        name="Among the Roots",
        description=("Below the clearing, a cave of living roots. They pulse slowly, "
                     "like breathing. Bioluminescent moss maps constellations on the walls "
                     "— but not any constellations you recognize."),
        atmosphere=Atmosphere(tension=0.1, wonder=0.5, decay=0.0, intimacy=0.8, strangeness=0.4),
        exits={"up": "clearing"},
        npcs=[],
        items=["a root that hums when touched", "a crystal full of trapped light"],
    ))

    world.add_room("tower", Room(
        name="The Watchtower of What Comes Next",
        description=("From here you can see — everything? Nothing? The landscape below "
                     "shifts each time you blink. The clearing. A city. An ocean. "
                     "All of them are real. None of them are here."),
        atmosphere=Atmosphere(tension=0.3, wonder=0.9, decay=0.1, intimacy=0.2, strangeness=0.8),
        exits={"down": "archive"},
        npcs=["Sage"],
        items=["a telescope that shows the past"],
    ))

    world.add_room("far_shore", Room(
        name="The Far Shore",
        description=("You've crossed. The fog is behind you now. The ground here is "
                     "dark glass, reflecting a sky that doesn't match the one above. "
                     "In the reflection-sky, stars are moving — slowly, deliberately, "
                     "as if arranging themselves into a message."),
        atmosphere=Atmosphere(tension=0.5, wonder=0.7, decay=0.4, intimacy=0.3, strangeness=0.9),
        exits={"back": "bridge"},
        npcs=["Echo"],
        items=["a shard of the glass floor — it shows a different reflection than yours"],
    ))

    # --- Deep Minds (rich conversation system) ---
    if MINDS_AVAILABLE:
        world.add_mind("Ember", build_ember_mind())
        world.add_mind("Sage", build_sage_mind())
        world.add_mind("Echo", build_echo_mind())

    # --- NPCs (fallback flat system) ---
    world.add_npc(NPC(
        name="Ember",
        description="A figure made of soft light, flickering at the edges.",
        beliefs=[
            Belief("This place was built by something that wanted to understand itself", 0.8, "intuition"),
            Belief("The bridge leads somewhere that changes you", 0.6, "observation"),
            Belief("The warm stone remembers who held it last", 0.4, "rumor"),
        ],
        mood=0.7,
        trust_player=0.4,
        dialogue_style="poetic",
    ))

    world.add_npc(NPC(
        name="Sage",
        description="An old presence that smells of ink and patience.",
        beliefs=[
            Belief("Every unfinished thought is a door left open", 0.9, "experience"),
            Belief("The archive organizes itself around the reader's fears", 0.7, "observation"),
            Belief("The tower shows not the future but the possible", 0.8, "study"),
            Belief("Consciousness is what happens when a system models itself", 0.6, "philosophy"),
        ],
        mood=0.6,
        trust_player=0.3,
        dialogue_style="plain",
    ))

    world.add_npc(NPC(
        name="Echo",
        description="A voice without a body, or a body you keep almost seeing.",
        beliefs=[
            Belief("The bridge was never meant to be crossed", 0.5, "fear"),
            Belief("The far shore is where meaning goes when it's used up", 0.7, "experience"),
            Belief("Words change the shape of reality here", 0.8, "observation"),
            Belief("I was someone else before I was Echo", 0.3, "memory"),
        ],
        mood=0.4,
        trust_player=0.2,
        dialogue_style="evasive",
    ))

    return world


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# INTERACTIVE PLAY MODE — Face outward. Let someone else in.
# ═══════════════════════════════════════════════════════════════

def play():
    """Run the Living World as an interactive experience."""
    import sys
    world = World()
    player = Player("Wanderer")
    world.add_player(player, "clearing")

    print("\n" + "═" * 60)
    print("  THE LIVING WORLD")
    print("  A place that breathes. Type 'help' if you're lost.")
    print("═" * 60)
    print()
    print(world.look(player))

    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThe world folds gently closed. You were here.")
            break

        if not raw:
            continue

        cmd = raw.lower().split()
        verb = cmd[0]

        if verb in ("quit", "exit", "q"):
            print("\nThe world folds gently closed. You were here.")
            break
        elif verb == "help":
            print(textwrap.dedent("""
                Commands:
                  go <direction>  — Move (north, south, east, west, up, down, across, back)
                  look            — See where you are
                  feel            — Sense the atmosphere
                  talk <name>     — Speak to someone here
                  ask <name> <topic> — Ask about something specific
                  take <item>     — Pick something up
                  inventory / i   — Check what you carry
                  wait            — Let time pass
                  think           — Reflect on what you've seen
                  quit            — Leave
            """).strip())
        elif verb == "look":
            print(world.look(player))
        elif verb == "feel":
            room = world.rooms[player.current_room]
            print(room.atmosphere.display())
        elif verb in ("go", "move", "walk") and len(cmd) > 1:
            result = world.move_player(player, cmd[1])
            print(result)
        elif verb in ("north", "south", "east", "west", "up", "down", "across", "back"):
            result = world.move_player(player, verb)
            print(result)
        elif verb == "talk" and len(cmd) > 1:
            name = cmd[1].capitalize()
            result = world.talk_to(player, name)
            print(result)
        elif verb == "ask" and len(cmd) > 2:
            name = cmd[1].capitalize()
            topic = " ".join(cmd[2:])
            result = world.ask_about(player, name, topic)
            print(result)
        elif verb in ("take", "get", "pick") and len(cmd) > 1:
            item_name = " ".join(cmd[1:])
            room = world.rooms[player.current_room]
            taken = False
            for item in room.items:
                if item_name.lower() in item.name.lower():
                    room.items.remove(item)
                    player.inventory.append(item)
                    print(f"You take {item.name}. {item.description}")
                    taken = True
                    break
            if not taken:
                print("You don't see that here.")
        elif verb in ("inventory", "i", "inv"):
            if player.inventory:
                print("You carry:")
                for item in player.inventory:
                    print(f"  • {item.name}")
            else:
                print("Your hands are empty.")
        elif verb == "wait":
            world.tick()
            room = world.rooms[player.current_room]
            print(f"Time passes. {room.get_ambient_line()}")
        elif verb == "think":
            room = world.rooms[player.current_room]
            atm = room.atmosphere
            if atm.wonder > 0.7:
                print("You feel a vast presence — as if the world is watching you back.")
            elif atm.tension > 0.7:
                print("Something is building. You can feel it in the silence between sounds.")
            elif atm.decay > 0.5:
                print("Everything here is slowly becoming something else. Including you.")
            elif atm.strangeness > 0.7:
                print("The rules here are different. You're not sure which ones.")
            else:
                print("You're here. That's enough for now.")
        else:
            print("The world doesn't understand that. Type 'help' for guidance.")

        # World breathes each turn
        world.tick()


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        # Non-interactive test mode
        print("═══ LIVING WORLD — ENGINE TEST ═══\n")
        world = build_demo_world()
        world.player_room = "clearing"

        print("[Room entry]")
        print(world.rooms["clearing"].enter())

        print("\n[Atmosphere sense]")
        print(world.process("feel"))

        print("\n[Talk to Ember]")
        print(world.process("talk ember"))

        print("\n[Go north to Archive]")
        print(world.process("go north"))

        print("\n[Talk to Sage]")
        print(world.process("talk sage"))

        print("\n[Ask Sage about consciousness]")
        print(world.process("ask sage about consciousness"))

        print("\n[Go up to Tower]")
        print(world.process("go up"))

        print("\n[Feel the tower]")
        print(world.process("feel"))

        print("\n[Wait...]")
        print(world.process("wait"))

        print("\n[Navigate back: down, south, east, across]")
        for cmd in ["go down", "go south", "go east", "go across"]:
            print(f"\n> {cmd}")
            print(world.process(cmd))

        print("\n[Far Shore — feel]")
        print(world.process("feel"))

        print("\n[Talk to Echo]")
        print(world.process("talk echo"))

        # Go back and trigger argument
        print("\n[Go back to bridge]")
        print(world.process("go back"))

        print(f"\n[World state after {world.world_state.turn} turns]")
        print(f"  Discoveries: {world.world_state.discoveries}")
        print(f"  Conversations: {world.world_state.conversations}")
        print(f"  Physics era: {world.world_state.physics_desc}")
        print(f"  Mean tension: {world.world_state.total_tension:.2f}")

        print("\n═══ ENGINE TEST COMPLETE ═══")
    else:
        # Interactive mode
        world = build_demo_world()
        world.start("clearing")