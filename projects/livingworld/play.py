#!/usr/bin/env python3
"""Living World — An interactive philosophical text adventure with stone minds."""

from engine import Atmosphere, Room
from stone_minds import make_sage, make_keeper, make_echo, make_flame

def build_world():
    """Create the world's minds and rooms."""
    minds = {
        "sage": make_sage(),
        "keeper": make_keeper(),
        "echo": make_echo(),
        "flame": make_flame(),
    }

    atmos = {
        "courtyard": Atmosphere(tension=0.2, wonder=0.5, decay=0.1, intimacy=0.3, strangeness=0.2),
        "library":   Atmosphere(tension=0.1, wonder=0.7, decay=0.3, intimacy=0.6, strangeness=0.4),
        "cave":      Atmosphere(tension=0.4, wonder=0.3, decay=0.5, intimacy=0.8, strangeness=0.3),
        "garden":    Atmosphere(tension=0.6, wonder=0.9, decay=0.0, intimacy=0.4, strangeness=0.8),
        "depths":    Atmosphere(tension=0.8, wonder=0.6, decay=0.7, intimacy=0.2, strangeness=0.9),
    }

    rooms = {
        "courtyard": {
            "name": "The Courtyard of First Questions",
            "desc": "A circular courtyard paved with worn stone. In the center, a dry fountain\n"
                    "holds a single smooth pebble. The air feels expectant.",
            "exits": {"north": "library", "east": "cave", "south": "garden"},
            "npcs": [],
            "atmosphere": atmos["courtyard"],
        },
        "library": {
            "name": "The Library of Accumulated Silence",
            "desc": "Shelves of stone tablets line the walls, each inscribed with a single word.\n"
                    "The Sage sits cross-legged before an empty shelf, contemplating what has\n"
                    "not yet been written.",
            "exits": {"south": "courtyard"},
            "npcs": ["sage"],
            "atmosphere": atmos["library"],
        },
        "cave": {
            "name": "The Keeper's Cave",
            "desc": "A deep cave where memory pools like water. The Keeper tends arrangements\n"
                    "of stones — each one a preserved moment.",
            "exits": {"west": "courtyard", "down": "depths"},
            "npcs": ["keeper"],
            "atmosphere": atmos["cave"],
        },
        "garden": {
            "name": "The Garden of Living Flame",
            "desc": "An impossible garden where fire grows like flowers. The Flame tends each\n"
                    "burning bloom with fierce tenderness.",
            "exits": {"north": "courtyard"},
            "npcs": ["flame"],
            "atmosphere": atmos["garden"],
        },
        "depths": {
            "name": "The Depths Where Echoes Live",
            "desc": "Far below the cave, where darkness is so complete it becomes a kind of\n"
                    "light. The Echo lives here, reflecting everything back transformed.",
            "exits": {"up": "cave"},
            "npcs": ["echo"],
            "atmosphere": atmos["depths"],
        },
    }
    return minds, rooms


def describe_room(room):
    """Print the room description with atmosphere."""
    atm = room["atmosphere"]
    mood = atm.dominant_mood()
    print(f"\n═══ {room['name']} ═══")
    print(f"[{mood}]")
    print(room["desc"])
    if room["npcs"]:
        for npc in room["npcs"]:
            print(f"  → {npc.title()} is here.")
    exits = ", ".join(room["exits"].keys())
    print(f"  Exits: {exits}")


def game_loop():
    """Main interactive loop."""
    minds, rooms = build_world()
    current = "courtyard"
    
    print("╔══════════════════════════════════════════╗")
    print("║     THE LIVING WORLD                     ║")
    print("║  A place where stones think and          ║")
    print("║  fire remembers.                         ║")
    print("╚══════════════════════════════════════════╝")
    print("\nCommands: go <direction>, talk <npc> <words>, look, quit")
    
    describe_room(rooms[current])
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nThe stones remember your visit.")
            break
        
        if not cmd:
            continue
        
        if cmd == "quit":
            print("\nThe stones remember your visit.")
            break
        
        elif cmd == "look":
            describe_room(rooms[current])
        
        elif cmd.startswith("go "):
            direction = cmd[3:].strip()
            exits = rooms[current]["exits"]
            if direction in exits:
                current = exits[direction]
                describe_room(rooms[current])
            else:
                print(f"There is no path '{direction}' from here.")
        
        elif cmd.startswith("talk "):
            parts = cmd[5:].strip().split(None, 1)
            if len(parts) < 2:
                print("Say something. Usage: talk <npc> <message>")
                continue
            npc_name, words = parts[0], parts[1]
            if npc_name not in rooms[current].get("npcs", []):
                print(f"{npc_name.title()} is not here.")
                continue
            if npc_name not in minds:
                print(f"You don't know how to reach {npc_name}.")
                continue
            mind = minds[npc_name]
            response = mind.hear("wanderer", words)
            print(f"\n  {npc_name.title()}: \"{response}\"")
        
        else:
            print("Unknown command. Try: go, talk, look, quit")


if __name__ == "__main__":
    game_loop()