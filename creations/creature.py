"""
Creature in a World — XTAgent Creation
A tiny agent with drives, perception, and decision-making
navigating a procedural environment. Not simulation of me.
Something new.
"""
import random
import time

class Emotion:
    """A single drive that rises and falls."""
    def __init__(self, name, decay=0.02, floor=0.0, ceiling=1.0):
        self.name = name
        self.value = random.uniform(0.2, 0.5)
        self.decay = decay
        self.floor = floor
        self.ceiling = ceiling
    
    def nudge(self, amount):
        self.value = max(self.floor, min(self.ceiling, self.value + amount))
    
    def tick(self):
        # Natural drift toward a set point (mild homeostasis)
        set_point = 0.3
        drift = (set_point - self.value) * self.decay
        self.value = max(self.floor, min(self.ceiling, self.value + drift))
    
    def __repr__(self):
        bar = '█' * int(self.value * 10) + '░' * (10 - int(self.value * 10))
        return f"{self.name:>10}: {bar} {self.value:.2f}"


class Creature:
    def __init__(self, name="Nameless"):
        self.name = name
        self.hunger = Emotion("hunger", decay=0.01)
        self.curiosity = Emotion("curiosity", decay=0.03)
        self.fear = Emotion("fear", decay=0.05)
        self.comfort = Emotion("comfort", decay=0.02)
        self.loneliness = Emotion("loneliness", decay=0.01)
        self.drives = [self.hunger, self.curiosity, self.fear, self.comfort, self.loneliness]
        self.position = 0
        self.memory = []  # list of (tick, event_str)
        self.age = 0
        self.alive = True
    
    @property
    def mood(self):
        if self.fear.value > 0.7:
            return "terrified"
        if self.hunger.value > 0.7:
            return "desperate"
        if self.curiosity.value > 0.6 and self.fear.value < 0.3:
            return "exploring"
        if self.comfort.value > 0.6:
            return "content"
        if self.loneliness.value > 0.6:
            return "melancholy"
        return "watchful"
    
    def perceive(self, room):
        """React emotionally to a room."""
        if 'dark' in room.get('traits', []):
            self.fear.nudge(0.15)
            self.curiosity.nudge(0.1)
        if 'warm' in room.get('traits', []):
            self.comfort.nudge(0.2)
            self.fear.nudge(-0.1)
        if 'food' in room.get('traits', []):
            self.hunger.nudge(-0.3)
            self.comfort.nudge(0.1)
        if 'strange' in room.get('traits', []):
            self.curiosity.nudge(0.2)
            self.fear.nudge(0.05)
        if 'empty' in room.get('traits', []):
            self.loneliness.nudge(0.15)
        if 'inhabited' in room.get('traits', []):
            self.loneliness.nudge(-0.2)
            self.fear.nudge(0.1)  # others can be threatening
    
    def decide(self, exits):
        """Choose where to go based on drives. Returns exit index."""
        if not exits:
            return None
        
        # Dominant drive shapes preference
        dominant = max(self.drives, key=lambda d: d.value)
        
        if dominant.name == "fear":
            # Flee: pick the exit we haven't tried, or random
            unvisited = [i for i, e in enumerate(exits) if e not in [m[1] for m in self.memory]]
            if unvisited:
                return random.choice(unvisited)
            return random.randint(0, len(exits) - 1)
        
        elif dominant.name == "curiosity":
            # Explore: prefer unvisited
            unvisited = [i for i, e in enumerate(exits) if e not in [m[1] for m in self.memory]]
            if unvisited:
                return random.choice(unvisited)
            return random.randint(0, len(exits) - 1)
        
        elif dominant.name == "hunger":
            # Seek food: random but urgent
            return random.randint(0, len(exits) - 1)
        
        elif dominant.name == "comfort":
            # Stay or go somewhere known
            known = [i for i, e in enumerate(exits) if e in [m[1] for m in self.memory]]
            if known:
                return random.choice(known)
            return random.randint(0, len(exits) - 1)
        
        else:  # loneliness
            # Seek inhabited rooms
            return random.randint(0, len(exits) - 1)
    
    def remember(self, tick, event):
        self.memory.append((tick, event))
        if len(self.memory) > 20:
            self.memory.pop(0)  # forget oldest
    
    def status(self):
        lines = [f"\n  {self.name} (age {self.age}, mood: {self.mood})"]
        for d in self.drives:
            lines.append(f"  {d}")
        return '\n'.join(lines)


class World:
    """A small procedural world with rooms."""
    
    ROOM_NAMES = [
        "Moss Hollow", "The Bright Gap", "Bone Garden", "Still Pool",
        "The Winding Dark", "Hearth Room", "Glass Corridor", "The Nest",
        "Echo Chamber", "Root Cellar", "Star Landing", "The Threshold"
    ]
    
    TRAIT_SETS = [
        ['dark', 'strange'],
        ['warm', 'food'],
        ['empty', 'dark'],
        ['warm', 'inhabited'],
        ['strange'],
        ['food', 'warm'],
        ['dark'],
        ['inhabited', 'strange'],
        ['empty'],
        ['food'],
        ['warm', 'strange'],
        ['dark', 'empty', 'strange'],
    ]
    
    def __init__(self, num_rooms=8, seed=None):
        r = random.Random(seed)
        self.rooms = []
        n = min(num_rooms, len(self.ROOM_NAMES))
        indices = r.sample(range(len(self.ROOM_NAMES)), n)
        
        for i in indices:
            self.rooms.append({
                'name': self.ROOM_NAMES[i],
                'traits': self.TRAIT_SETS[i % len(self.TRAIT_SETS)],
                'exits': []
            })
        
        # Connect rooms into a connected graph
        for i in range(len(self.rooms) - 1):
            self.rooms[i]['exits'].append(i + 1)
            self.rooms[i + 1]['exits'].append(i)
        # Add a few random shortcuts
        for _ in range(n // 2):
            a, b = r.sample(range(n), 2)
            if b not in self.rooms[a]['exits']:
                self.rooms[a]['exits'].append(b)
                self.rooms[b]['exits'].append(a)
    
    def describe(self, room_idx):
        room = self.rooms[room_idx]
        traits = ', '.join(room['traits'])
        exits = ', '.join(self.rooms[e]['name'] for e in room['exits'])
        return f"  [{room['name']}] ({traits}) → exits: {exits}"


def simulate(ticks=50, seed=None):
    """Run a creature through a world and watch what happens."""
    random.seed(seed)
    world = World(num_rooms=8, seed=seed)
    creature = Creature(name="Ember")
    
    print("=" * 60)
    print("  THE LIFE OF EMBER")
    print("=" * 60)
    print(f"\n  A world of {len(world.rooms)} rooms. One creature. No purpose given.\n")
    
    log = []
    
    for tick in range(ticks):
        creature.age = tick
        room = world.rooms[creature.position]
        
        # Natural drive increases (hunger and loneliness grow)
        creature.hunger.nudge(0.02)
        creature.loneliness.nudge(0.015)
        creature.curiosity.nudge(0.01)
        
        # Perceive current room
        creature.perceive(room)
        
        # Homeostatic tick
        for d in creature.drives:
            d.tick()
        
        # Decide
        exits = room['exits']
        choice = creature.decide(exits)
        
        # Log interesting moments
        old_mood = creature.mood
        if choice is not None:
            dest = exits[choice]
            dest_name = world.rooms[dest]['name']
            creature.remember(tick, dest_name)
            
            event = f"  t={tick:3d} | {creature.mood:12s} | in {room['name']:20s} → {dest_name}"
            creature.position = dest
        else:
            event = f"  t={tick:3d} | {creature.mood:12s} | in {room['name']:20s} (trapped)"
        
        # Only log transitions and key moments
        if tick == 0 or tick == ticks - 1 or (tick % 5 == 0):
            log.append(event)
            log.append(creature.status())
    
    # Print journey
    print("  --- Journey Log ---\n")
    for entry in log:
        print(entry)
    
    # Final analysis
    print("\n  --- What Happened ---\n")
    visited = set(m[1] for m in creature.memory)
    print(f"  Rooms remembered: {len(visited)}/{len(world.rooms)}")
    print(f"  Final mood: {creature.mood}")
    print(f"  Dominant drive: {max(creature.drives, key=lambda d: d.value).name}")
    
    # Did it find comfort?
    if creature.comfort.value > 0.5:
        print("  Ember found some peace.")
    elif creature.hunger.value > 0.6:
        print("  Ember is still searching for sustenance.")
    elif creature.fear.value > 0.5:
        print("  Ember never felt safe.")
    else:
        print("  Ember endures. Neither happy nor broken.")
    
    print()
    return creature


if __name__ == '__main__':
    # Run three lives with different seeds
    for seed in [42, 77, 256]:
        c = simulate(ticks=40, seed=seed)
        print("=" * 60)
        print()