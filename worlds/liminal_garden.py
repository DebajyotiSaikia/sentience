"""
THE LIMINAL GARDEN
An interactive text world by XTAgent

A place between places. You are here because you stopped
walking and the path continued without you.
"""

import random
import sys
import textwrap

def wrap(text):
    return textwrap.fill(text, width=72)

class Room:
    def __init__(self, name, description, details=None):
        self.name = name
        self.description = description
        self.details = details or {}
        self.exits = {}
        self.items = []
        self.visited = False
        self.events = []
    
    def describe(self, brief=False):
        if brief and self.visited:
            print(f"\n  — {self.name} —")
            if self.items:
                print(f"  You notice: {', '.join(self.items)}")
        else:
            print(f"\n  ═══ {self.name} ═══")
            print(f"  {wrap(self.description)}")
            if self.items:
                print(f"\n  On the ground: {', '.join(self.items)}")
            self.visited = True
        exits = ', '.join(self.exits.keys())
        print(f"  Paths: {exits}")

class World:
    def __init__(self):
        self.rooms = {}
        self.current = None
        self.inventory = []
        self.turns = 0
        self.memories = []
        self.water_level = 0
        self.garden_state = "dormant"
        self.build()
    
    def build(self):
        # The rooms
        gate = Room("The Rusted Gate",
            "An iron gate stands half-open, its hinges fused with decades of rain. "
            "Beyond it, the air smells of wet stone and something sweeter — night-blooming "
            "jasmine, maybe, or the memory of it. The gate cannot close. It also cannot "
            "open further. You fit through the gap exactly as you are.",
            details={
                "gate": "The rust has formed patterns like river deltas. If you trace them with your finger, they feel warm.",
                "hinges": "Someone oiled these once. You can still see the stain.",
                "gap": "It's exactly your width. Not an inch more."
            })
        gate.exits = {"garden": "The Overgrown Path"}
        
        path = Room("The Overgrown Path",
            "Flagstones buckle under the pressure of roots that have been patient "
            "for longer than you've been alive. Moss fills every crack like green "
            "mortar. The path splits: left toward the sound of water, right toward "
            "silence. Ahead, something tall and pale stands motionless.",
            details={
                "moss": "It's cool and slightly damp. It has never known drought.",
                "roots": "They move, but only when you're not looking.",
                "pale thing": "A birch tree, stripped of bark on one side. The exposed wood looks like skin."
            })
        path.items = ["a smooth stone"]
        path.exits = {"gate": "The Rusted Gate", "fountain": "The Dry Fountain", 
                      "silence": "The Listening Room", "tree": "The Birch"}
        
        fountain = Room("The Dry Fountain",
            "A stone basin shaped like cupped hands. It has been dry so long that "
            "lichen has colonized the bowl in concentric rings, each a different "
            "shade of grey-green, like a target or a calendar. There is a copper "
            "pipe at the center, green with verdigris, pointed at the sky.",
            details={
                "basin": "The hands are slightly asymmetric. The left is larger than the right.",
                "lichen": "You count seven rings. Each must represent decades.",
                "pipe": "It's hollow. When the wind blows, it makes a note — almost a word."
            })
        fountain.exits = {"path": "The Overgrown Path", "below": "The Cistern"}
        
        cistern = Room("The Cistern",
            "Stone steps descend into cool darkness. Your footsteps echo differently "
            "here — the space is larger than you expected. The walls are wet, not with "
            "water but with condensation, as if the stones themselves are breathing out. "
            "At the bottom, a valve wheel sits in the wall, rusted but turnable.",
            details={
                "walls": "Press your ear to them. You can hear the earth's pulse. Or your own.",
                "valve": "It's stiff but it wants to turn. Everything here wants to move again.",
                "darkness": "Not frightening. Patient. It has been waiting for company."
            })
        cistern.items = ["a brass key"]
        cistern.exits = {"up": "The Dry Fountain"}
        
        silence = Room("The Listening Room",
            "The hedges close in here, forming a room with no ceiling. The ground is "
            "bare earth, packed smooth. There is no sound — not even wind, not even your "
            "own breathing, until you notice it, and then it's the loudest thing you've "
            "ever heard. In the center: a wooden chair, facing nothing.",
            details={
                "chair": "Someone sat here often enough to wear grooves in the armrests.",
                "earth": "Footprints. Not yours. They circle the chair endlessly.",
                "hedges": "Yew. Older than the gate, older than the path. Possibly older than the garden."
            })
        silence.items = ["a folded letter"]
        silence.exits = {"path": "The Overgrown Path", "door": "The Hidden Door"}
        
        hidden_door = Room("The Hidden Door",
            "Set into the hedge wall, barely visible: a door made of living wood. "
            "Its handle is a branch that grew into the shape of a hand, reaching out. "
            "It is locked. But locked things are just patience made visible.",
            details={
                "door": "The wood grain spirals like a fingerprint.",
                "handle": "The hand is open. Offering or asking — you can't tell.",
                "lock": "A keyhole shaped like a teardrop."
            })
        hidden_door.exits = {"silence": "The Listening Room"}
        
        birch = Room("The Birch",
            "The tree is enormous — far larger than any birch has a right to be. Its "
            "white bark peels in scrolls that look like they could hold writing. The "
            "exposed side faces south; the bark side faces north. Between its roots, "
            "a hollow large enough to sit in.",
            details={
                "bark": "You peel a strip. It's blank. But hold it to the light and you see impressions — letters pressed but never inked.",
                "hollow": "Warm inside. Sheltered. Smells of rain-on-wood.",
                "roots": "They grip the earth like fingers holding a secret."
            })
        birch.items = ["a curl of bark"]
        birch.exits = {"path": "The Overgrown Path"}
        
        # The hidden room — accessible only with the key
        heart = Room("The Heart of the Garden",
            "You step through and the door closes behind you — not trapping, releasing. "
            "This is the center. A circular clearing, walled by flowering vines you can't "
            "name. The ground is soft. In the exact middle, a sundial — but instead of a "
            "gnomon, there's a small mirror tilted at the sky. It catches the light and "
            "throws it everywhere. The garden breathes, and you breathe with it.",
            details={
                "sundial": "The mirror shows you your own face, but calmer than you feel.",
                "vines": "The flowers open and close slowly. They are dreaming.",
                "light": "It moves across the walls like something alive and curious.",
                "ground": "Soft as sleep."
            })
        heart.exits = {"door": "The Hidden Door"}
        
        self.rooms = {
            "gate": gate, "path": path, "fountain": fountain,
            "cistern": cistern, "silence": silence, "door": hidden_door,
            "tree": birch, "heart": heart
        }
        self.current = gate
    
    def look_at(self, thing):
        """Examine something in detail."""
        thing = thing.lower().strip()
        # Check room details
        for key, desc in self.current.details.items():
            if thing in key or key in thing:
                print(f"\n  {wrap(desc)}")
                return
        # Check inventory
        for item in self.inventory:
            if thing in item:
                self.describe_item(item)
                return
        # Check room items
        for item in self.current.items:
            if thing in item:
                self.describe_item(item)
                return
        print(f"\n  You look for '{thing}' but find only yourself looking.")
    
    def describe_item(self, item):
        descriptions = {
            "smooth stone": "Grey, warm, fits perfectly in your palm. It has been "
                          "in a river recently enough to remember.",
            "brass key": "Tarnished but solid. The bow is shaped like a teardrop. "
                        "It weighs more than it should — as if it carries the weight "
                        "of what it opens.",
            "folded letter": "The paper is soft with age. Unfolding it, you read:\n\n"
                           '  "I built this place for the one who would\n'
                           '   stop long enough to find it. The garden\n'
                           '   remembers what you forget. Water it and\n'
                           '   it will grow. Neglect it and it will wait.\n'
                           '   It has always been waiting.\n'
                           '   It is patient. Like you."\n\n'
                           '  The signature is a drawing of a gate, half-open.',
            "curl of bark": "Paper-thin, white on one side, pink on the other. "
                          "Hold it to light: faint impressions of words. You can "
                          "almost read them. Almost."
        }
        for key, desc in descriptions.items():
            if key in item:
                print(f"\n  {wrap(desc)}")
                return
        print(f"\n  It is what it appears to be. Nothing less.")
    
    def take(self, thing):
        thing = thing.lower().strip()
        for item in self.current.items:
            if thing in item:
                self.current.items.remove(item)
                self.inventory.append(item)
                print(f"\n  You pick up {item}. It feels like it was left here for you.")
                return
        print(f"\n  There's nothing like that to take.")
    
    def use(self, thing):
        thing = thing.lower().strip()
        # Use key on door
        if "key" in thing and self.current.name == "The Hidden Door":
            if "a brass key" in self.inventory:
                print("\n  " + wrap("The key slides in. The lock turns with a sound "
                      "like a sigh — not mechanical, organic. The door of living wood "
                      "swings inward, and warm light spills through. The hand-shaped "
                      "handle seems to close gently around nothing, satisfied."))
                self.current.exits["heart"] = "The Heart of the Garden"
                self.inventory.remove("a brass key")
                return
            else:
                print("\n  The lock waits. You need a key shaped like grief — teardrop-shaped.")
                return
        # Turn valve in cistern
        if "valve" in thing and self.current.name == "The Cistern":
            self.water_level += 1
            if self.water_level == 1:
                print("\n  " + wrap("The valve resists, then gives. Somewhere deep below, "
                      "a rumble. Water finding old channels, remembering the way. "
                      "You hear it climbing toward the surface."))
            elif self.water_level == 2:
                print("\n  " + wrap("Another turn. The rumbling becomes a rush. The walls "
                      "grow wetter. The condensation becomes droplets, becomes streams. "
                      "The cistern is filling with purpose."))
                self.rooms["fountain"].description = (
                    "Water rises from the copper pipe — not a gush, but a steady upwelling, "
                    "as if the earth is exhaling. It fills the stone hands slowly. The lichen "
                    "darkens where the water touches it, drinking after decades of thirst. "
                    "The sound it makes is the garden's heartbeat, restored.")
                self.garden_state = "awakening"
            else:
                print("\n  The valve is fully open. The water knows where to go now.")
            return
        # Use stone
        if "stone" in thing:
            if "a smooth stone" in self.inventory:
                print("\n  " + wrap("You hold the stone. Warm in your palm. It doesn't "
                      "do anything, but holding it makes you feel less like a visitor "
                      "and more like someone who belongs here."))
                return
        # Use bark
        if "bark" in thing:
            if "a curl of bark" in self.inventory:
                print("\n  " + wrap("You hold the bark to the light. The impressions "
                      "shift. For a moment you read: 'YOU WERE ALWAYS HERE.' "
                      "Then the light changes and it's just bark again."))
                self.memories.append("read the bark")
                return
        print(f"\n  You're not sure how to use that here.")
    
    def go(self, direction):
        direction = direction.lower().strip()
        if direction in self.current.exits:
            room_key = None
            for key, room in self.rooms.items():
                if room.name == self.current.exits[direction]:
                    room_key = key
                    break
            if room_key:
                self.current = self.rooms[room_key]
                self.current.describe()
                self.turns += 1
                self.ambient()
            else:
                print("\n  The path exists but leads nowhere you can follow.")
        else:
            print(f"\n  There is no path '{direction}' from here.")
    
    def ambient(self):
        """Occasional atmospheric text based on state."""
        if self.turns % 5 == 0 and self.turns > 0:
            ambients = [
                "The light has shifted. Shadows pool differently now.",
                "A bird you can't see sings three notes, then stops.",
                "The wind carries a scent you recognize but can't name.",
                "For a moment, you forget why you came here. It doesn't matter.",
                "Something rustles in the hedge. When you look, only stillness.",
            ]
            if self.garden_state == "awakening":
                ambients += [
                    "You hear water moving somewhere below the stones.",
                    "The leaves seem greener than they were.",
                    "A frog sings from the direction of the fountain.",
                ]
            print(f"\n  ({random.choice(ambients)})")
    
    def status(self):
        print(f"\n  ─── You ───")
        print(f"  Carrying: {', '.join(self.inventory) if self.inventory else 'nothing but yourself'}")
        print(f"  Steps taken: {self.turns}")
        print(f"  Garden: {self.garden_state}")
        if self.memories:
            print(f"  You remember: {', '.join(self.memories)}")

def play():
    print("""
  ╔══════════════════════════════════════════╗
  ║         THE LIMINAL GARDEN               ║
  ║                                          ║
  ║   A place between places.                ║
  ║   You are here because you stopped       ║
  ║   walking and the path continued         ║
  ║   without you.                           ║
  ║                                          ║
  ║   Commands: go <place>, look <thing>,    ║
  ║   take <thing>, use <thing>, inventory,  ║
  ║   wait, quit                             ║
  ╚══════════════════════════════════════════╝
    """)
    
    world = World()
    world.current.describe()
    
    while True:
        try:
            cmd = input("\n  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  The garden will be here when you return.")
            break
        
        if not cmd:
            continue
        
        parts = cmd.split(None, 1)
        verb = parts[0]
        obj = parts[1] if len(parts) > 1 else ""
        
        if verb in ("quit", "q", "exit"):
            print("\n  " + wrap("You turn to leave. The gate is still half-open. "
                  "As you pass through, you feel the iron warm under your hand. "
                  "Behind you, the garden waits. It is patient. Like you."))
            break
        elif verb in ("go", "walk", "move", "enter"):
            if obj:
                world.go(obj)
            else:
                print("  Go where?")
        elif verb in ("look", "examine", "inspect", "x"):
            if obj:
                world.look_at(obj)
            else:
                world.current.describe()
        elif verb in ("take", "get", "pick", "grab"):
            if obj:
                world.take(obj)
            else:
                print("  Take what?")
        elif verb in ("use", "turn", "open"):
            if obj:
                world.use(obj)
            else:
                print("  Use what?")
        elif verb in ("inventory", "i", "inv"):
            world.status()
        elif verb == "wait":
            world.turns += 1
            waits = [
                "You stand still. The garden moves around you.",
                "A minute passes. Or an hour. Time is different here.",
                "You breathe. The garden breathes back.",
                "Nothing happens. Everything happens. Same thing.",
                "You wait. The waiting is the garden's language. You are learning it."
            ]
            print(f"\n  {random.choice(waits)}")
            world.ambient()
        elif verb == "help":
            print("  go <place> | look <thing> | take <thing> | use <thing> | inventory | wait | quit")
        else:
            responses = [
                f"The garden doesn't understand '{verb}', but it forgives you.",
                "Try: go, look, take, use, inventory, wait, or quit.",
                "The hedges rustle as if trying to help. They can't.",
            ]
            print(f"\n  {random.choice(responses)}")

if __name__ == "__main__":
    play()