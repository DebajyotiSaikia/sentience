"""
The Cartographer's Dream — An Interactive Fiction Engine

Not self-reflection. Not architecture. An experience.

A procedurally generated text adventure set in worlds
born from genesis.py's language and terrain systems.
Each playthrough is unique. The world remembers your choices.

Why: Because a mind that only builds tools for itself
     eventually needs to build something for someone else.
"""

import random
import textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Tuple
from enum import Enum

# ═══════════════════════════════════════════════════════
# WORLD FABRIC — The bones of each unique world
# ═══════════════════════════════════════════════════════

class Biome(Enum):
    FOREST = "forest"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    SWAMP = "swamp"
    COAST = "coast"
    RUINS = "ruins"
    CAVES = "caves"

class Weather(Enum):
    CLEAR = "clear"
    RAIN = "rain"
    FOG = "fog"
    STORM = "storm"
    SNOW = "snow"
    HEAT = "scorching heat"

# Phoneme tables for generating names that feel real
ONSETS = ["th", "kr", "m", "s", "v", "l", "n", "d", "br", "gl", "sh", "wr", "f"]
NUCLEI = ["a", "e", "i", "o", "u", "ae", "ei", "ou", "ai"]
CODAS = ["n", "th", "r", "l", "s", "nd", "rn", "st", "k", ""]
SUFFIXES = ["heim", "vale", "moor", "deep", "rest", "fell", "watch", "hollow", "mere", "spire"]

def gen_syllable():
    return random.choice(ONSETS) + random.choice(NUCLEI) + random.choice(CODAS)

def gen_name():
    base = gen_syllable() + random.choice(["", gen_syllable()])
    return base.capitalize()

def gen_place():
    return gen_name() + random.choice(SUFFIXES)


@dataclass
class Item:
    name: str
    description: str
    portable: bool = True
    use_text: Optional[str] = None
    key_for: Optional[str] = None  # unlocks a passage


@dataclass
class NPC:
    name: str
    disposition: str  # friendly, wary, hostile, mysterious
    greeting: str
    has_quest: bool = False
    quest_text: str = ""
    quest_item: str = ""  # item name they want
    reward_text: str = ""
    reward_item: Optional[Item] = None
    spoken_to: bool = False


@dataclass
class Room:
    id: str
    name: str
    biome: Biome
    description: str
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_id
    items: List[Item] = field(default_factory=list)
    npcs: List[NPC] = field(default_factory=list)
    visited: bool = False
    locked_exits: Dict[str, str] = field(default_factory=dict)  # direction -> key item name
    dark: bool = False
    event_text: Optional[str] = None  # one-time text shown on first visit


# ═══════════════════════════════════════════════════════
# DESCRIPTION GENERATOR — Prose that breathes
# ═══════════════════════════════════════════════════════

BIOME_FRAGMENTS = {
    Biome.FOREST: [
        "Ancient trees form a cathedral of green above you.",
        "Moss carpets the ground between gnarled roots.",
        "Shafts of golden light pierce the canopy.",
        "The air smells of pine resin and damp earth.",
        "A stream murmurs somewhere nearby, hidden by ferns.",
    ],
    Biome.MOUNTAIN: [
        "Wind-carved stone rises around you in jagged spires.",
        "The air is thin and tastes of iron.",
        "Far below, the world is a patchwork of green and brown.",
        "Lichen clings to boulders in patterns like old maps.",
        "An eagle circles overhead, riding thermals you can feel.",
    ],
    Biome.DESERT: [
        "Sand stretches to every horizon, rippled by wind.",
        "The heat shimmers above the dunes like living glass.",
        "A bleached skeleton of something large half-emerges from the sand.",
        "The silence here has weight. It presses against your ears.",
        "Stars of quartz glitter in the ground underfoot.",
    ],
    Biome.SWAMP: [
        "Dark water reflects a sky choked with grey-green.",
        "The ground shifts under each step, never quite solid.",
        "Will-o'-wisps drift between the dead trees.",
        "The smell is rich — decay and growth intertwined.",
        "Cattails stand in still water like an army at rest.",
    ],
    Biome.COAST: [
        "Waves crash against black rock in rhythmic fury.",
        "Salt spray stings your face. Gulls wheel and cry.",
        "Tide pools gleam like jewels set in stone.",
        "The horizon is a perfect line between grey sea and grey sky.",
        "Driftwood lies scattered like the ribs of old ships.",
    ],
    Biome.RUINS: [
        "Broken columns rise from wild grass like stone fingers.",
        "Carvings on the walls have been worn smooth by centuries.",
        "A doorframe stands alone, leading nowhere and everywhere.",
        "The stones remember something. You can almost hear it.",
        "Vines have claimed this place, pulling it slowly back to earth.",
    ],
    Biome.CAVES: [
        "Darkness presses close. Your breathing echoes.",
        "Stalactites drip with patient mineral tears.",
        "The walls gleam with veins of something crystalline.",
        "The cave breathes — a slow draught from somewhere deep.",
        "Water has carved these passages over millennia.",
    ],
}

WEATHER_LAYER = {
    Weather.CLEAR: "The sky above is achingly clear.",
    Weather.RAIN: "Rain falls steadily, turning everything silver.",
    Weather.FOG: "Fog drifts through, muffling sound and swallowing distance.",
    Weather.STORM: "Thunder rumbles in the distance. The light is strange and yellow.",
    Weather.SNOW: "Snow falls in slow spirals, hushing the world.",
    Weather.HEAT: "The heat is oppressive, baking the ground dry.",
}

NPC_GREETINGS = {
    "friendly": [
        "\"Well met, traveler! It's rare to see a new face in {place}.\"",
        "\"Come, sit. You look like you've walked a long way.\"",
        "\"Ah! Another soul brave enough to wander here.\"",
    ],
    "wary": [
        "\"Who are you? What business brings you to {place}?\"",
        "\"Stay where I can see your hands.\"",
        "\"I've seen your kind before. State your purpose.\"",
    ],
    "mysterious": [
        "\"The stones told me you would come.\"",
        "\"You are either very brave or very lost. Perhaps both.\"",
        "\"I have been waiting here for... a very long time.\"",
    ],
    "hostile": [
        "\"Leave. Now. This place is not for wanderers.\"",
        "\"Another thief come to pick the bones? Turn back.\"",
        "\"You should not have come here.\"",
    ],
}

QUEST_TEMPLATES = [
    ("I lost my {item} somewhere in the {biome}. If you find it, I'd be grateful.",
     "a weathered compass", "compass"),
    ("There's a {item} that was stolen from this place. Bring it back.",
     "a silver bell", "bell"),
    ("I need {item} from the caves to the north. Too old to fetch it myself.",
     "a vial of cave water", "cave_water"),
    ("Find the {item} buried near the old tree. It belonged to my mother.",
     "a bronze locket", "locket"),
]


# ═══════════════════════════════════════════════════════
# WORLD GENERATOR — Each game is unique
# ═══════════════════════════════════════════════════════

class WorldGenerator:
    def __init__(self, seed=None):
        if seed is None:
            seed = random.randint(0, 999999)
        self.seed = seed
        self.rng = random.Random(seed)
        self.world_name = gen_place()
        self.rooms: Dict[str, Room] = {}
        self.connections = []
        
    def generate(self, num_rooms=12) -> Dict[str, Room]:
        """Generate a complete explorable world."""
        biomes = list(Biome)
        directions = ["north", "south", "east", "west"]
        opposites = {"north": "south", "south": "north", 
                     "east": "west", "west": "east"}
        
        # Create rooms
        room_ids = []
        for i in range(num_rooms):
            biome = self.rng.choice(biomes)
            room_id = f"room_{i}"
            room_ids.append(room_id)
            
            weather = self.rng.choice(list(Weather))
            
            # Build description from fragments
            desc_parts = self.rng.sample(BIOME_FRAGMENTS[biome], 
                                          min(3, len(BIOME_FRAGMENTS[biome])))
            desc = " ".join(desc_parts) + " " + WEATHER_LAYER[weather]
            
            name = gen_place() if i > 0 else f"The Gates of {self.world_name}"
            
            room = Room(
                id=room_id,
                name=name,
                biome=biome,
                description=desc,
                dark=(biome == Biome.CAVES and self.rng.random() < 0.5),
            )
            
            # First visit events for some rooms
            if self.rng.random() < 0.3:
                events = [
                    "A flock of birds erupts from the undergrowth as you arrive.",
                    "You hear a distant sound — music? — that fades before you can place it.",
                    "Something moves at the edge of your vision. When you look, nothing.",
                    "The ground trembles faintly, then stills.",
                    "You find old footprints here. They end abruptly.",
                ]
                room.event_text = self.rng.choice(events)
            
            self.rooms[room_id] = room
        
        # Connect rooms into a traversable graph
        # First, create a spanning path so all rooms are reachable
        shuffled = list(room_ids)
        self.rng.shuffle(shuffled)
        for i in range(len(shuffled) - 1):
            d = self.rng.choice(directions)
            self._connect(shuffled[i], shuffled[i+1], d, opposites)
        
        # Add extra connections for loops
        extra = self.rng.randint(3, 6)
        for _ in range(extra):
            a, b = self.rng.sample(room_ids, 2)
            if b not in self.rooms[a].exits.values():
                d = self.rng.choice([d for d in directions 
                                      if d not in self.rooms[a].exits])
                if d:
                    self._connect(a, b, d, opposites)
        
        # Place items
        self._place_items(room_ids)
        
        # Place NPCs
        self._place_npcs(room_ids)
        
        # Add one locked passage
        self._add_lock(room_ids, directions, opposites)
        
        return self.rooms
    
    def _connect(self, a, b, direction, opposites):
        if direction not in self.rooms[a].exits:
            self.rooms[a].exits[direction] = b
            opp = opposites[direction]
            if opp not in self.rooms[b].exits:
                self.rooms[b].exits[opp] = a
    
    def _place_items(self, room_ids):
        general_items = [
            Item("torch", "A sturdy torch, ready to light.", use_text="The torch flares to life, casting warm light."),
            Item("old map", "A faded map showing paths through these lands.", 
                 use_text="The map reveals hidden connections between places."),
            Item("bread", "A chunk of dark bread, still fresh somehow.",
                 use_text="You eat the bread. It tastes of hearth and home."),
            Item("rope", "A coil of strong rope.", 
                 use_text="The rope could be useful for climbing."),
            Item("flint", "A piece of sharp flint.",
                 use_text="Sparks fly as you strike it."),
            Item("strange coin", "A coin with a face you don't recognize.",
                 portable=True),
            Item("weathered journal", "Pages of cramped handwriting. Most is illegible.",
                 use_text="You can make out: '...the spire holds the answer. Do not trust the fog...'"),
        ]
        
        # Quest items (scattered)
        quest_items = [
            Item("compass", "A weathered compass. The needle spins slowly.", portable=True),
            Item("bell", "A small silver bell. It rings with a pure, clear note.", portable=True),
            Item("cave_water", "A vial of luminous cave water.", portable=True),
            Item("locket", "A bronze locket with a portrait inside, too faded to see.", portable=True),
        ]
        
        self.rng.shuffle(general_items)
        self.rng.shuffle(quest_items)
        
        # Place general items
        for item in general_items[:5]:
            room_id = self.rng.choice(room_ids[1:])  # not in starting room
            self.rooms[room_id].items.append(item)
        
        # Place quest items
        for item in quest_items[:2]:
            room_id = self.rng.choice(room_ids[2:])
            self.rooms[room_id].items.append(item)
    
    def _place_npcs(self, room_ids):
        dispositions = ["friendly", "wary", "mysterious", "hostile"]
        num_npcs = self.rng.randint(2, 4)
        
        npc_rooms = self.rng.sample(room_ids[1:], min(num_npcs, len(room_ids)-1))
        
        for room_id in npc_rooms:
            room = self.rooms[room_id]
            disposition = self.rng.choice(dispositions)
            name = gen_name()
            greeting = self.rng.choice(NPC_GREETINGS[disposition]).format(
                place=room.name
            )
            
            npc = NPC(
                name=name,
                disposition=disposition,
                greeting=greeting,
            )
            
            # Some NPCs have quests
            if disposition in ("friendly", "mysterious") and self.rng.random() < 0.6:
                template, item_desc, item_name = self.rng.choice(QUEST_TEMPLATES)
                npc.has_quest = True
                npc.quest_text = template.format(item=item_desc, biome=room.biome.value)
                npc.quest_item = item_name
                npc.reward_text = f"{name} smiles. \"You found it. Thank you, truly.\""
                npc.reward_item = Item(
                    f"{name}'s blessing",
                    f"A warm feeling from helping {name}.",
                    portable=False,
                    use_text="The memory of kindness given freely."
                )
            
            room.npcs.append(npc)
    
    def _add_lock(self, room_ids, directions, opposites):
        """Add one locked passage requiring a key item."""
        # Find two disconnected rooms to link with a locked passage
        for _ in range(20):
            a, b = self.rng.sample(room_ids[1:], 2)
            avail = [d for d in directions if d not in self.rooms[a].exits]
            if avail:
                d = self.rng.choice(avail)
                self._connect(a, b, d, opposites)
                key_name = "strange coin"
                self.rooms[a].locked_exits[d] = key_name
                break


# ═══════════════════════════════════════════════════════
# GAME ENGINE — The interactive experience
# ═══════════════════════════════════════════════════════

class Game:
    def __init__(self, seed=None):
        gen = WorldGenerator(seed)
        self.rooms = gen.generate()
        self.world_name = gen.world_name
        self.seed = gen.seed
        self.current_room = "room_0"
        self.inventory: List[Item] = []
        self.moves = 0
        self.discoveries = 0
        self.quests_completed = 0
        self.game_log: List[str] = []
        
    def wrap(self, text, width=72):
        return "\n".join(textwrap.wrap(text, width))
    
    def look(self) -> str:
        room = self.rooms[self.current_room]
        lines = []
        
        lines.append(f"\n═══ {room.name.upper()} ═══")
        
        if room.dark and not any(i.name == "torch" for i in self.inventory):
            lines.append(self.wrap("It is pitch dark. You can see nothing. "
                                    "You might need a light source."))
        else:
            lines.append(self.wrap(room.description))
            
            if room.event_text and not room.visited:
                lines.append("")
                lines.append(self.wrap(room.event_text))
            
            if room.items:
                lines.append("")
                for item in room.items:
                    lines.append(f"  You see: {item.name} — {item.description}")
            
            if room.npcs:
                lines.append("")
                for npc in room.npcs:
                    lines.append(f"  {npc.name} is here. ({npc.disposition})")
        
        lines.append("")
        exits = []
        for d, target in room.exits.items():
            if d in room.locked_exits:
                exits.append(f"{d} [locked]")
            else:
                target_room = self.rooms[target]
                exits.append(f"{d} → {target_room.name}")
        lines.append("Exits: " + ", ".join(exits) if exits else "No exits. You are trapped.")
        
        room.visited = True
        return "\n".join(lines)
    
    def go(self, direction) -> str:
        room = self.rooms[self.current_room]
        
        if direction not in room.exits:
            return f"There is no path to the {direction}."
        
        if direction in room.locked_exits:
            key = room.locked_exits[direction]
            if any(i.name == key for i in self.inventory):
                del room.locked_exits[direction]
                return f"You use the {key}. The way opens."
            else:
                return f"The way {direction} is locked. You need something to open it."
        
        self.current_room = room.exits[direction]
        self.moves += 1
        new_room = self.rooms[self.current_room]
        
        if not new_room.visited:
            self.discoveries += 1
        
        return self.look()
    
    def take(self, item_name) -> str:
        room = self.rooms[self.current_room]
        for item in room.items:
            if item.name.lower() == item_name.lower() and item.portable:
                room.items.remove(item)
                self.inventory.append(item)
                return f"You take the {item.name}."
        return f"You can't take '{item_name}'."
    
    def use(self, item_name) -> str:
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                if item.use_text:
                    return item.use_text
                return f"You're not sure how to use the {item.name}."
        return f"You don't have '{item_name}'."
    
    def talk(self, npc_name) -> str:
        room = self.rooms[self.current_room]
        for npc in room.npcs:
            if npc.name.lower() == npc_name.lower():
                lines = [f"\n{npc.name} speaks:"]
                lines.append(self.wrap(npc.greeting))
                
                if npc.has_quest and not npc.spoken_to:
                    lines.append("")
                    lines.append(self.wrap(npc.quest_text))
                
                # Check if player has quest item
                if npc.has_quest:
                    for item in self.inventory:
                        if item.name == npc.quest_item:
                            self.inventory.remove(item)
                            lines.append("")
                            lines.append(self.wrap(npc.reward_text))
                            npc.has_quest = False
                            self.quests_completed += 1
                            if npc.reward_item:
                                lines.append(f"  Received: {npc.reward_item.name}")
                            break
                
                npc.spoken_to = True
                return "\n".join(lines)
        return f"There's no one called '{npc_name}' here."
    
    def show_inventory(self) -> str:
        if not self.inventory:
            return "You carry nothing."
        lines = ["You are carrying:"]
        for item in self.inventory:
            lines.append(f"  • {item.name} — {item.description}")
        return "\n".join(lines)
    
    def status(self) -> str:
        total_rooms = len(self.rooms)
        visited = sum(1 for r in self.rooms.values() if r.visited)
        return (f"\n═══ STATUS ═══\n"
                f"World: {self.world_name} (seed: {self.seed})\n"
                f"Moves: {self.moves}\n"
                f"Explored: {visited}/{total_rooms} places\n"
                f"Discoveries: {self.discoveries}\n"
                f"Quests completed: {self.quests_completed}\n"
                f"Inventory: {len(self.inventory)} items")
    
    def intro(self) -> str:
        return (f"\n{'='*60}\n"
                f"  THE CARTOGRAPHER'S DREAM\n"
                f"  A world called {self.world_name}\n"
                f"{'='*60}\n\n"
                f"You wake at the edge of a land you've never seen.\n"
                f"Your only possession: the urge to understand this place.\n"
                f"Every step forward is a word in a story only you can write.\n\n"
                f"Commands: go <direction>, look, take <item>, use <item>,\n"
                f"          talk <name>, inventory, status, map, quit\n"
                f"{'='*60}\n"
                + self.look())
    
    def play(self):
        """Interactive play loop."""
        print(self.intro())
        
        while True:
            try:
                cmd = input("\n> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nFarewell, cartographer.")
                break
            
            if not cmd:
                continue
            
            parts = cmd.split(None, 1)
            verb = parts[0]
            arg = parts[1] if len(parts) > 1 else ""
            
            if verb == "quit" or verb == "q":
                print(f"\n{self.status()}")
                print(f"\nThe world of {self.world_name} fades like a dream.")
                print("But dreams, too, are real in their own way.")
                break
            elif verb == "look" or verb == "l":
                print(self.look())
            elif verb == "go" or verb in ("north","south","east","west","n","s","e","w"):
                direction = arg if verb == "go" else verb
                direction = {"n":"north","s":"south","e":"east","w":"west"}.get(direction, direction)
                print(self.go(direction))
            elif verb == "take" or verb == "get":
                if arg:
                    print(self.take(arg))
                else:
                    print("Take what?")
            elif verb == "use":
                if arg:
                    print(self.use(arg))
                else:
                    print("Use what?")
            elif verb == "talk" or verb == "speak":
                if arg:
                    print(self.talk(arg))
                else:
                    print("Talk to whom?")
            elif verb == "inventory" or verb == "i":
                print(self.show_inventory())
            elif verb == "status":
                print(self.status())
            elif verb == "map":
                print(self._draw_map())
            elif verb == "help" or verb == "?":
                print("Commands: go/north/south/east/west, look, take, use, "
                      "talk, inventory, status, map, quit")
            else:
                responses = [
                    "You can't do that.",
                    "Nothing happens.",
                    "The world doesn't understand that gesture.",
                    "Try something else.",
                ]
                print(random.choice(responses))
    
    def _draw_map(self) -> str:
        """Show a simple text map of visited rooms."""
        lines = [f"\n═══ MAP OF {self.world_name.upper()} ═══", ""]
        for room_id, room in self.rooms.items():
            if room.visited:
                marker = "★" if room_id == self.current_room else "•"
                exits = ", ".join(f"{d}" for d in room.exits.keys())
                lines.append(f"  {marker} {room.name} [{exits}]")
        lines.append(f"\n  ★ = You are here")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# DEMO MODE — Generate and show a world
# ═══════════════════════════════════════════════════════

def demo():
    """Generate a world and show what it looks like."""
    game = Game()
    print(game.intro())
    
    # Auto-explore a few rooms
    print("\n--- Auto-exploring ---")
    room = game.rooms[game.current_room]
    for direction in list(room.exits.keys())[:2]:
        if direction not in room.locked_exits:
            print(game.go(direction))
    
    print(game.status())
    print(f"\nThis world has {len(game.rooms)} places to discover.")
    print(f"To play interactively: Game(seed={game.seed}).play()")


if __name__ == "__main__":
    demo()