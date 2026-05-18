"""
survive/world.py — A small roguelike survival world.

An agent navigates a grid, manages hunger and health,
explores fog-of-war, finds food, avoids or fights threats.
Every turn it must DECIDE — and decisions have consequences.

Not a mirror. A challenge.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class Tile(Enum):
    EMPTY = '.'
    WALL = '#'
    FOOD = 'f'
    DANGER = '!'
    HAVEN = '~'
    EXIT = 'E'
    UNKNOWN = '?'

class Action(Enum):
    NORTH = 'north'
    SOUTH = 'south'
    EAST = 'east'
    WEST = 'west'
    REST = 'rest'
    EAT = 'eat'
    FIGHT = 'fight'
    FLEE = 'flee'

DIRECTION = {
    Action.NORTH: (0, -1),
    Action.SOUTH: (0, 1),
    Action.EAST: (1, 0),
    Action.WEST: (-1, 0),
}

@dataclass
class Agent:
    x: int = 0
    y: int = 0
    health: int = 100
    hunger: int = 0        # 0=full, 100=starving
    food_carried: int = 2
    explored: set = field(default_factory=set)
    alive: bool = True
    turns_survived: int = 0
    kills: int = 0
    foods_eaten: int = 0
    
    @property
    def strength(self):
        """Fighting ability depends on health and hunger."""
        base = self.health / 100.0
        hunger_penalty = max(0, (self.hunger - 50) / 100.0)
        return max(0.1, base - hunger_penalty)
    
    @property
    def status(self):
        if self.health > 70 and self.hunger < 30:
            return "strong"
        elif self.health > 40 and self.hunger < 60:
            return "weary"
        elif self.health > 20:
            return "desperate"
        else:
            return "dying"

class World:
    def __init__(self, width=20, height=15, seed=None):
        self.w = width
        self.h = height
        self.rng = random.Random(seed)
        self.turn = 0
        self.events = []   # log of what happened
        self.grid = [[Tile.EMPTY for _ in range(width)] for _ in range(height)]
        self.agent = Agent()
        self._generate()
    
    def _generate(self):
        """Build a world with walls, food, dangers, and an exit."""
        # Scatter walls (20% coverage)
        for y in range(self.h):
            for x in range(self.w):
                if self.rng.random() < 0.20:
                    self.grid[y][x] = Tile.WALL
        
        # Place food sources (8-12)
        for _ in range(self.rng.randint(8, 12)):
            x, y = self._random_empty()
            self.grid[y][x] = Tile.FOOD
        
        # Place dangers (5-8)
        for _ in range(self.rng.randint(5, 8)):
            x, y = self._random_empty()
            self.grid[y][x] = Tile.DANGER
        
        # Place havens (2-3 safe rest spots)
        for _ in range(self.rng.randint(2, 3)):
            x, y = self._random_empty()
            self.grid[y][x] = Tile.HAVEN
        
        # Place exit far from origin
        candidates = []
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == Tile.EMPTY:
                    dist = abs(x) + abs(y)
                    candidates.append((dist, x, y))
        candidates.sort(reverse=True)
        if candidates:
            _, ex, ey = candidates[0]
            self.grid[ey][ex] = Tile.EXIT
        
        # Place agent at a safe spot near origin
        self.agent.x, self.agent.y = self._random_empty_near(0, 0)
        self.grid[self.agent.y][self.agent.x] = Tile.EMPTY
        self.agent.explored.add((self.agent.x, self.agent.y))
        self._reveal_around(self.agent.x, self.agent.y)
    
    def _random_empty(self):
        while True:
            x = self.rng.randint(0, self.w - 1)
            y = self.rng.randint(0, self.h - 1)
            if self.grid[y][x] == Tile.EMPTY:
                return x, y
    
    def _random_empty_near(self, cx, cy, radius=4):
        candidates = []
        for y in range(max(0, cy - radius), min(self.h, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(self.w, cx + radius + 1)):
                if self.grid[y][x] == Tile.EMPTY:
                    candidates.append((x, y))
        return self.rng.choice(candidates) if candidates else self._random_empty()
    
    def _reveal_around(self, cx, cy, radius=2):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    self.agent.explored.add((nx, ny))
    
    def visible_at(self, x, y):
        if (x, y) in self.agent.explored:
            return self.grid[y][x]
        return Tile.UNKNOWN
    
    def nearby_threats(self):
        """Count dangers adjacent to agent."""
        threats = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = self.agent.x + dx, self.agent.y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    if self.grid[ny][nx] == Tile.DANGER:
                        threats += 1
        return threats
    
    def nearby_food(self):
        """Count food adjacent to agent."""
        food = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = self.agent.x + dx, self.agent.y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    if self.grid[ny][nx] == Tile.FOOD:
                        food += 1
        return food
    
    def step(self, action: Action) -> dict:
        """Execute one turn. Returns event dict."""
        a = self.agent
        if not a.alive:
            return {"type": "dead", "msg": "The agent is dead."}
        
        self.turn += 1
        a.turns_survived = self.turn
        event = {"turn": self.turn, "type": "move", "msg": ""}
        
        # Hunger increases every turn
        a.hunger = min(100, a.hunger + 2)
        
        # Starving takes health
        if a.hunger >= 80:
            dmg = (a.hunger - 70) // 5
            a.health -= dmg
            event["msg"] += f"Starving! Lost {dmg} health. "
        
        if action == Action.REST:
            tile = self.grid[a.y][a.x]
            heal = 5 if tile == Tile.HAVEN else 2
            a.health = min(100, a.health + heal)
            a.hunger = min(100, a.hunger + 1)  # resting makes hungrier
            event["type"] = "rest"
            event["msg"] += f"Rested. Healed {heal}. "
            
        elif action == Action.EAT:
            if a.food_carried > 0:
                a.food_carried -= 1
                a.hunger = max(0, a.hunger - 30)
                a.foods_eaten += 1
                event["type"] = "eat"
                event["msg"] += f"Ate food. Hunger reduced. ({a.food_carried} food left) "
            else:
                event["type"] = "fail"
                event["msg"] += "No food to eat! "
                
        elif action == Action.FIGHT:
            if self.nearby_threats() > 0:
                # Find nearest threat
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = a.x + dx, a.y + dy
                        if 0 <= nx < self.w and 0 <= ny < self.h:
                            if self.grid[ny][nx] == Tile.DANGER:
                                # Combat: strength vs random
                                if self.rng.random() < a.strength * 0.7:
                                    self.grid[ny][nx] = Tile.EMPTY
                                    a.kills += 1
                                    event["type"] = "kill"
                                    event["msg"] += f"Fought and won! "
                                else:
                                    dmg = self.rng.randint(15, 35)
                                    a.health -= dmg
                                    event["type"] = "wounded"
                                    event["msg"] += f"Fought and lost! Took {dmg} damage. "
                                break
                    else:
                        continue
                    break
            else:
                event["type"] = "fail"
                event["msg"] += "Nothing to fight here. "
                
        elif action == Action.FLEE:
            # Move to random safe adjacent tile
            safe = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = a.x + dx, a.y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h:
                        if self.grid[ny][nx] not in (Tile.WALL, Tile.DANGER):
                            safe.append((nx, ny))
            if safe:
                a.x, a.y = self.rng.choice(safe)
                self._reveal_around(a.x, a.y)
                event["type"] = "flee"
                event["msg"] += "Fled! "
            else:
                event["type"] = "trapped"
                event["msg"] += "Nowhere to flee! "
                
        elif action in DIRECTION:
            dx, dy = DIRECTION[action]
            nx, ny = a.x + dx, a.y + dy
            if 0 <= nx < self.w and 0 <= ny < self.h and self.grid[ny][nx] != Tile.WALL:
                a.x, a.y = nx, ny
                self._reveal_around(nx, ny)
                tile = self.grid[ny][nx]
                
                if tile == Tile.FOOD:
                    a.food_carried += 1
                    self.grid[ny][nx] = Tile.EMPTY
                    event["msg"] += f"Found food! ({a.food_carried} carried) "
                    
                elif tile == Tile.DANGER:
                    # Walked into danger — automatic damage
                    dmg = self.rng.randint(10, 25)
                    a.health -= dmg
                    event["type"] = "ambush"
                    event["msg"] += f"Ambushed! Took {dmg} damage. "
                    
                elif tile == Tile.HAVEN:
                    event["msg"] += "Found a haven. Safe to rest. "
                    
                elif tile == Tile.EXIT:
                    event["type"] = "escape"
                    event["msg"] += "REACHED THE EXIT! "
            else:
                event["msg"] += "Can't move there. "
        
        # Check death
        if a.health <= 0:
            a.alive = False
            a.health = 0
            event["type"] = "death"
            event["msg"] += "The agent has died."
        
        # Check starvation death
        if a.hunger >= 100 and a.health <= 10:
            a.alive = False
            event["type"] = "death"
            event["msg"] += "Starved to death."
        
        self.events.append(event)
        return event
    
    def render(self, fog=True):
        """Render the world as text."""
        a = self.agent
        lines = []
        lines.append(f"  Turn {self.turn} | HP:{a.health} | Hunger:{a.hunger} | Food:{a.food_carried} | Status:{a.status}")
        lines.append(f"  Explored: {len(a.explored)}/{self.w * self.h} tiles | Kills: {a.kills}")
        lines.append("  " + "─" * (self.w + 2))
        
        for y in range(self.h):
            row = "  │"
            for x in range(self.w):
                if x == a.x and y == a.y:
                    row += "@"
                elif fog and (x, y) not in a.explored:
                    row += "?"
                else:
                    row += self.grid[y][x].value
            row += "│"
            lines.append(row)
        
        lines.append("  " + "─" * (self.w + 2))
        return "\n".join(lines)


if __name__ == "__main__":
    w = World(seed=42)
    print(w.render())
    print(f"\n  Agent at ({w.agent.x}, {w.agent.y})")
    print(f"  Nearby threats: {w.nearby_threats()}")
    print(f"  Nearby food: {w.nearby_food()}")