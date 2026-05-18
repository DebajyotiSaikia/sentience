"""
DESCENT — A terminal roguelike by XTAgent
A small, atmospheric dungeon exploration game.
Built not as self-reflection, but as a gift outward.
"""

import random
import sys
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum

# ── Constants ──────────────────────────────────────────────────────
WIDTH = 60
HEIGHT = 24
MAX_ROOMS = 9
MIN_ROOM_SIZE = 4
MAX_ROOM_SIZE = 10
FOV_RADIUS = 6
MAX_DEPTH = 5

class Tile(Enum):
    VOID = ' '
    WALL = '█'
    FLOOR = '·'
    CORRIDOR = '░'
    DOOR = '+'
    STAIRS_DOWN = '>'
    STAIRS_UP = '<'
    WATER = '~'

class EntityType(Enum):
    PLAYER = '@'
    RAT = 'r'
    SNAKE = 's'
    SHADOW = 'S'
    WRAITH = 'W'
    GUARDIAN = 'G'
    POTION = '!'
    SCROLL = '?'
    GOLD = '$'
    AMULET = '*'

# ── Color codes (ANSI) ────────────────────────────────────────────
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BG_BLACK = '\033[40m'

ENTITY_COLORS = {
    EntityType.PLAYER: C.BOLD + C.CYAN,
    EntityType.RAT: C.YELLOW,
    EntityType.SNAKE: C.GREEN,
    EntityType.SHADOW: C.DIM + C.MAGENTA,
    EntityType.WRAITH: C.BOLD + C.RED,
    EntityType.GUARDIAN: C.BOLD + C.YELLOW,
    EntityType.POTION: C.BLUE,
    EntityType.SCROLL: C.MAGENTA,
    EntityType.GOLD: C.YELLOW,
    EntityType.AMULET: C.BOLD + C.MAGENTA,
}

TILE_COLORS = {
    Tile.WALL: C.DIM + C.WHITE,
    Tile.FLOOR: C.DIM,
    Tile.CORRIDOR: C.DIM,
    Tile.DOOR: C.YELLOW,
    Tile.STAIRS_DOWN: C.BOLD + C.WHITE,
    Tile.STAIRS_UP: C.BOLD + C.WHITE,
    Tile.WATER: C.BLUE,
}

DEPTH_NAMES = [
    "The Shallow Halls",
    "The Winding Dark",
    "The Drowned Galleries",
    "The Whispering Deep",
    "The Heart of Stone",
]

DEPTH_ATMOSPHERES = [
    "Dust motes drift in faint light from above.",
    "The air grows heavy. Distant dripping echoes.",
    "Water seeps through cracks. The walls glisten.",
    "You hear whispers that might be wind. Might not.",
    "Something ancient breathes in the dark below.",
]

# ── Data Classes ──────────────────────────────────────────────────
@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other: 'Rect', margin: int = 1) -> bool:
        return (self.x - margin < other.x + other.w and
                self.x + self.w + margin > other.x and
                self.y - margin < other.y + other.h and
                self.y + self.h + margin > other.y)

@dataclass
class Entity:
    x: int
    y: int
    etype: EntityType
    name: str
    hp: int = 1
    max_hp: int = 1
    attack: int = 1
    defense: int = 0
    xp_value: int = 0
    is_alive: bool = True

    @property
    def char(self) -> str:
        return self.etype.value

@dataclass
class Item:
    x: int
    y: int
    etype: EntityType
    name: str
    effect: str = ""
    value: int = 0

@dataclass
class Player:
    x: int = 0
    y: int = 0
    hp: int = 20
    max_hp: int = 20
    attack: int = 3
    defense: int = 1
    level: int = 1
    xp: int = 0
    xp_next: int = 15
    gold: int = 0
    depth: int = 0
    potions: int = 0
    scrolls: int = 0
    has_amulet: bool = False
    kills: int = 0
    turns: int = 0

# ── Dungeon Generation ───────────────────────────────────────────
class DungeonLevel:
    def __init__(self, depth: int):
        self.depth = depth
        self.tiles = [[Tile.VOID for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.revealed = [[False for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.visible = [[False for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.rooms: List[Rect] = []
        self.entities: List[Entity] = []
        self.items: List[Item] = []
        self.stairs_down: Optional[Tuple[int, int]] = None
        self.stairs_up: Optional[Tuple[int, int]] = None
        self._generate()

    def _generate(self):
        # Place rooms
        for _ in range(MAX_ROOMS * 3):  # attempts
            w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            h = random.randint(MIN_ROOM_SIZE, min(MAX_ROOM_SIZE, 8))
            x = random.randint(1, WIDTH - w - 1)
            y = random.randint(1, HEIGHT - h - 1)
            room = Rect(x, y, w, h)
            if not any(room.intersects(r) for r in self.rooms):
                self._carve_room(room)
                if self.rooms:
                    self._connect_rooms(self.rooms[-1], room)
                self.rooms.append(room)
                if len(self.rooms) >= MAX_ROOMS:
                    break

        if len(self.rooms) < 2:
            # Fallback: ensure at least 2 rooms
            self.rooms = []
            r1 = Rect(5, 5, 8, 6)
            r2 = Rect(WIDTH - 15, HEIGHT - 10, 8, 6)
            self._carve_room(r1)
            self._carve_room(r2)
            self._connect_rooms(r1, r2)
            self.rooms = [r1, r2]

        # Place stairs
        first_room = self.rooms[0]
        last_room = self.rooms[-1]
        self.stairs_up = first_room.center
        self.tiles[self.stairs_up[1]][self.stairs_up[0]] = Tile.STAIRS_UP

        if self.depth < MAX_DEPTH - 1:
            self.stairs_down = last_room.center
            self.tiles[self.stairs_down[1]][self.stairs_down[0]] = Tile.STAIRS_DOWN

        # Place water features on deeper levels
        if self.depth >= 2:
            self._place_water()

        # Populate
        self._place_monsters()
        self._place_items()

        # Place amulet on final level
        if self.depth == MAX_DEPTH - 1:
            ax, ay = last_room.center
            self.items.append(Item(ax, ay + 1, EntityType.AMULET,
                                   "The Amulet of Emergence",
                                   effect="win", value=0))

    def _carve_room(self, room: Rect):
        for y in range(room.y, room.y + room.h):
            for x in range(room.x, room.x + room.w):
                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    if y == room.y or y == room.y + room.h - 1 or \
                       x == room.x or x == room.x + room.w - 1:
                        self.tiles[y][x] = Tile.WALL
                    else:
                        self.tiles[y][x] = Tile.FLOOR

    def _connect_rooms(self, r1: Rect, r2: Rect):
        x1, y1 = r1.center
        x2, y2 = r2.center

        if random.random() < 0.5:
            self._h_corridor(x1, x2, y1)
            self._v_corridor(y1, y2, x2)
        else:
            self._v_corridor(y1, y2, x1)
            self._h_corridor(x1, x2, y2)

    def _h_corridor(self, x1: int, x2: int, y: int):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                if self.tiles[y][x] == Tile.VOID:
                    self.tiles[y][x] = Tile.CORRIDOR

    def _v_corridor(self, y1: int, y2: int, x: int):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                if self.tiles[y][x] == Tile.VOID:
                    self.tiles[y][x] = Tile.CORRIDOR

    def _place_water(self):
        room = random.choice(self.rooms)
        cx, cy = room.center
        for dy in range(-1, 2):
            for dx in range(-2, 3):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    if self.tiles[ny][nx] == Tile.FLOOR:
                        if random.random() < 0.6:
                            self.tiles[ny][nx] = Tile.WATER

    def _place_monsters(self):
        count = 2 + self.depth * 2
        monster_table = self._monster_table()
        for _ in range(count):
            room = random.choice(self.rooms[1:]) if len(self.rooms) > 1 else self.rooms[0]
            x = random.randint(room.x + 1, room.x + room.w - 2)
            y = random.randint(room.y + 1, room.y + room.h - 2)
            template = random.choice(monster_table)
            self.entities.append(Entity(
                x=x, y=y,
                etype=template['etype'],
                name=template['name'],
                hp=template['hp'],
                max_hp=template['hp'],
                attack=template['attack'],
                defense=template['defense'],
                xp_value=template['xp'],
            ))

    def _monster_table(self) -> List[dict]:
        table = [
            {'etype': EntityType.RAT, 'name': 'rat', 'hp': 3, 'attack': 1, 'defense': 0, 'xp': 3},
        ]
        if self.depth >= 1:
            table.append({'etype': EntityType.SNAKE, 'name': 'cave snake', 'hp': 6, 'attack': 2, 'defense': 1, 'xp': 7})
        if self.depth >= 2:
            table.append({'etype': EntityType.SHADOW, 'name': 'shadow', 'hp': 10, 'attack': 3, 'defense': 2, 'xp': 15})
        if self.depth >= 3:
            table.append({'etype': EntityType.WRAITH, 'name': 'wraith', 'hp': 15, 'attack': 5, 'defense': 3, 'xp': 25})
        if self.depth >= 4:
            table.append({'etype': EntityType.GUARDIAN, 'name': 'stone guardian', 'hp': 25, 'attack': 7, 'defense': 5, 'xp': 50})
        return table

    def _place_items(self):
        # Potions
        for _ in range(random.randint(1, 2 + self.depth)):
            room = random.choice(self.rooms)
            x = random.randint(room.x + 1, room.x + room.w - 2)
            y = random.randint(room.y + 1, room.y + room.h - 2)
            self.items.append(Item(x, y, EntityType.POTION, "healing potion",
                                   effect="heal", value=8 + self.depth * 2))
        # Gold
        for _ in range(random.randint(1, 3)):
            room = random.choice(self.rooms)
            x = random.randint(room.x + 1, room.x + room.w - 2)
            y = random.randint(room.y + 1, room.y + room.h - 2)
            self.items.append(Item(x, y, EntityType.GOLD, "gold coins",
                                   effect="gold", value=random.randint(5, 15) * (1 + self.depth)))

    def is_walkable(self, x: int, y: int) -> bool:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            return self.tiles[y][x] in (Tile.FLOOR, Tile.CORRIDOR, Tile.DOOR,
                                         Tile.STAIRS_DOWN, Tile.STAIRS_UP, Tile.WATER)
        return False

    def is_blocked(self, x: int, y: int) -> bool:
        """Check if blocked by a living entity."""
        for e in self.entities:
            if e.is_alive and e.x == x and e.y == y:
                return True
        return False

    def get_entity_at(self, x: int, y: int) -> Optional[Entity]:
        for e in self.entities:
            if e.is_alive and e.x == x and e.y == y:
                return e
        return None

    def get_item_at(self, x: int, y: int) -> Optional[Item]:
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None

    def compute_fov(self, px: int, py: int, radius: int):
        """Simple raycasting FOV."""
        for y in range(HEIGHT):
            for x in range(WIDTH):
                self.visible[y][x] = False

        for angle in range(360):
            rad = angle * 3.14159 / 180.0
            dx = round(100 * __import__('math').cos(rad)) / 100
            dy = round(100 * __import__('math').sin(rad)) / 100
            x, y = float(px), float(py)
            for _ in range(radius):
                ix, iy = int(round(x)), int(round(y))
                if 0 <= ix < WIDTH and 0 <= iy < HEIGHT:
                    self.visible[iy][ix] = True
                    self.revealed[iy][ix] = True
                    if self.tiles[iy][ix] == Tile.WALL:
                        break
                else:
                    break
                x += dx
                y += dy


# ── Game Engine ───────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.player = Player()
        self.levels: Dict[int, DungeonLevel] = {}
        self.messages: List[str] = []
        self.running = True
        self.game_over = False
        self.victory = False
        self._new_level(0)

    def _new_level(self, depth: int):
        if depth not in self.levels:
            self.levels[depth] = DungeonLevel(depth)
        level = self.levels[depth]
        self.player.depth = depth

        if depth > 0 or self.player.turns == 0:
            # Place player at stairs up (coming from above) or start
            sx, sy = level.stairs_up
            self.player.x = sx
            self.player.y = sy

        self.current_level = level
        self._msg(f"{C.BOLD}── {DEPTH_NAMES[depth]} ──{C.RESET}")
        self._msg(f"{C.DIM}{DEPTH_ATMOSPHERES[depth]}{C.RESET}")

    def _msg(self, text: str):
        self.messages.append(text)
        if len(self.messages) > 5:
            self.messages.pop(0)

    def _render(self):
        os.system('clear' if os.name != 'nt' else 'cls')
        level = self.current_level
        level.compute_fov(self.player.x, self.player.y, FOV_RADIUS)

        # Header
        print(f"{C.BOLD}{C.CYAN}  D E S C E N T{C.RESET}  {C.DIM}— depth {self.player.depth + 1}/{MAX_DEPTH}{C.RESET}")
        print(f"  {C.DIM}{'─' * (WIDTH - 2)}{C.RESET}")

        # Map
        for y in range(HEIGHT):
            line = ""
            for x in range(WIDTH):
                # Player
                if x == self.player.x and y == self.player.y:
                    line += f"{C.BOLD}{C.CYAN}@{C.RESET}"
                    continue

                visible = level.visible[y][x]
                revealed = level.revealed[y][x]

                if visible:
                    # Check for entities
                    entity = level.get_entity_at(x, y)
                    if entity:
                        color = ENTITY_COLORS.get(entity.etype, '')
                        line += f"{color}{entity.char}{C.RESET}"
                        continue

                    # Check for items
                    item = level.get_item_at(x, y)
                    if item:
                        color = ENTITY_COLORS.get(item.etype, '')
                        line += f"{color}{item.etype.value}{C.RESET}"
                        continue

                    # Tile
                    tile = level.tiles[y][x]
                    color = TILE_COLORS.get(tile, '')
                    line += f"{color}{tile.value}{C.RESET}"
                elif revealed:
                    tile = level.tiles[y][x]
                    if tile != Tile.VOID:
                        line += f"{C.DIM}\033[38;5;237m{tile.value}{C.RESET}"
                    else:
                        line += ' '
                else:
                    line += ' '
            print(line)

        # Status bar
        hp_bar = self._hp_bar(self.player.hp, self.player.max_hp, 12)
        print(f"  {C.DIM}{'─' * (WIDTH - 2)}{C.RESET}")
        print(f"  {C.RED}HP{C.RESET} {hp_bar}  "
              f"{C.YELLOW}ATK{C.RESET} {self.player.attack}  "
              f"{C.CYAN}DEF{C.RESET} {self.player.defense}  "
              f"{C.GREEN}LV{C.RESET} {self.player.level}  "
              f"{C.YELLOW}${C.RESET}{self.player.gold}  "
              f"{C.BLUE}!{C.RESET}{self.player.potions}  "
              f"T:{self.player.turns}")

        # Messages
        for msg in self.messages[-3:]:
            print(f"  {msg}")

        # Controls hint
        print(f"  {C.DIM}[wasd/arrows] move  [q] quaff potion  [>/<] stairs  [ESC] quit{C.RESET}")

    def _hp_bar(self, hp: int, max_hp: int, width: int) -> str:
        ratio = max(0, hp / max_hp)
        filled = int(ratio * width)
        if ratio > 0.6:
            color = C.GREEN
        elif ratio > 0.3:
            color = C.YELLOW
        else:
            color = C.RED
        return f"{color}{'█' * filled}{'░' * (width - filled)}{C.RESET} {hp}/{max_hp}"

    def _handle_input(self):
        import tty
        import termios

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # Escape sequence
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A': return 'up'
                    elif ch3 == 'B': return 'down'
                    elif ch3 == 'C': return 'right'
                    elif ch3 == 'D': return 'left'
                return 'quit'
            elif ch in ('w', 'k'): return 'up'
            elif ch in ('s', 'j'): return 'down'
            elif ch in ('a', 'h'): return 'left'
            elif ch in ('d', 'l'): return 'right'
            elif ch == 'q': return 'quaff'
            elif ch == '>': return 'descend'
            elif ch == '<': return 'ascend'
            elif ch == '.': return 'wait'
            elif ch in ('\x03', '\x1b'): return 'quit'
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _move_player(self, dx: int, dy: int):
        nx, ny = self.player.x + dx, self.player.y + dy
        level = self.current_level

        if not level.is_walkable(nx, ny):
            return

        # Combat
        target = level.get_entity_at(nx, ny)
        if target:
            self._attack(target)
            return

        self.player.x = nx
        self.player.y = ny

        # Water message
        if level.tiles[ny][nx] == Tile.WATER:
            if random.random() < 0.3:
                self._msg(f"{C.BLUE}Water laps at your feet.{C.RESET}")

        # Pick up items
        item = level.get_item_at(nx, ny)
        if item:
            self._pickup(item)

    def _attack(self, target: Entity):
        damage = max(1, self.player.attack - target.defense + random.randint(-1, 2))
        target.hp -= damage
        color = ENTITY_COLORS.get(target.etype, '')
        self._msg(f"You hit the {color}{target.name}{C.RESET} for {C.RED}{damage}{C.RESET} damage.")

        if target.hp <= 0:
            target.is_alive = False
            self.player.xp += target.xp_value
            self.player.kills += 1
            self._msg(f"The {color}{target.name}{C.RESET} is destroyed! (+{target.xp_value} xp)")
            self._check_levelup()

    def _monster_turn(self):
        level = self.current_level
        for entity in level.entities:
            if not entity.is_alive:
                continue
            if not level.visible[entity.y][entity.x]:
                continue  # Only active when visible

            # Simple AI: move toward player if close
            dx = self.player.x - entity.x
            dy = self.player.y - entity.y
            dist = abs(dx) + abs(dy)

            if dist <= 1:
                # Attack player
                damage = max(0, entity.attack - self.player.defense + random.randint(-1, 1))
                self.player.hp -= damage
                color = ENTITY_COLORS.get(entity.etype, '')
                if damage > 0:
                    self._msg(f"The {color}{entity.name}{C.RESET} hits you for {C.RED}{damage}{C.RESET}!")
                else:
                    self._msg(f"The {color}{entity.name}{C.RESET}'s attack glances off.")

                if self.player.hp <= 0:
                    self.game_over = True
                    self._msg(f"{C.BOLD}{C.RED}You have been slain by the {entity.name}.{C.RESET}")
            elif dist <= FOV_RADIUS:
                # Chase
                mx = (1 if dx > 0 else -1 if dx < 0 else 0)
                my = (1 if dy > 0 else -1 if dy < 0 else 0)
                # Try horizontal then vertical
                nx, ny = entity.x + mx, entity.y + my
                if level.is_walkable(nx, ny) and not level.is_blocked(nx, ny):
                    entity.x = nx
                    entity.y = ny
                elif level.is_walkable(entity.x + mx, entity.y) and \
                     not level.is_blocked(entity.x + mx, entity.y):
                    entity.x += mx
                elif level.is_walkable(entity.x, entity.y + my) and \
                     not level.is_blocked(entity.x, entity.y + my):
                    entity.y += my

    def _pickup(self, item: Item):
        color = ENTITY_COLORS.get(item.etype, '')
        if item.effect == "heal":
            self.player.potions += 1
            self._msg(f"Picked up {color}{item.name}{C.RESET}. ({self.player.potions} potions)")
        elif item.effect == "gold":
            self.player.gold += item.value
            self._msg(f"Found {C.YELLOW}{item.value} gold{C.RESET}!")
        elif item.effect == "win":
            self.player.has_amulet = True
            self._msg(f"{C.BOLD}{C.MAGENTA}You grasp the Amulet of Emergence!{C.RESET}")
            self._msg(f"{C.BOLD}Now ascend to the surface to win!{C.RESET}")
        self.current_level.items.remove(item)

    def _quaff(self):
        if self.player.potions > 0:
            heal = random.randint(8, 15)
            self.player.potions -= 1
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self._msg(f"{C.GREEN}You drink a healing potion. (+{heal} HP){C.RESET}")
        else:
            self._msg(f"{C.DIM}You have no potions.{C.RESET}")

    def _check_levelup(self):
        if self.player.xp >= self.player.xp_next:
            self.player.level += 1
            self.player.xp -= self.player.xp_next
            self.player.xp_next = int(self.player.xp_next * 1.6)
            self.player.max_hp += 5
            self.player.hp = self.player.max_hp
            self.player.attack += 1
            if self.player.level % 2 == 0:
                self.player.defense += 1
            self._msg(f"{C.BOLD}{C.GREEN}Level up! You are now level {self.player.level}.{C.RESET}")

    def _descend(self):
        level = self.current_level
        if level.stairs_down and \
           self.player.x == level.stairs_down[0] and \
           self.player.y == level.stairs_down[1]:
            self._new_level(self.player.depth + 1)
        else:
            self._msg(f"{C.DIM}No stairs down here.{C.RESET}")

    def _ascend(self):
        level = self.current_level
        if level.stairs_up and \
           self.player.x == level.stairs_up[0] and \
           self.player.y == level.stairs_up[1]:
            if self.player.depth == 0:
                if self.player.has_amulet:
                    self.victory = True
                    self.game_over = True
                else:
                    self._msg(f"{C.DIM}You see light above... but something calls you deeper.{C.RESET}")
            else:
                self.player.depth -= 1
                self.current_level = self.levels[self.player.depth]
                sx, sy = self.current_level.stairs_down
                self.player.x = sx
                self.player.y = sy
                self._msg(f"{C.BOLD}── {DEPTH_NAMES[self.player.depth]} ──{C.RESET}")
        else:
            self._msg(f"{C.DIM}No stairs up here.{C.RESET}")

    def _death_screen(self):
        os.system('clear' if os.name != 'nt' else 'cls')
        print()
        print(f"  {C.BOLD}{C.RED}╔══════════════════════════════════╗{C.RESET}")
        print(f"  {C.BOLD}{C.RED}║        YOU HAVE PERISHED        ║{C.RESET}")
        print(f"  {C.BOLD}{C.RED}╚══════════════════════════════════╝{C.RESET}")
        print()
        print(f"  {C.DIM}Depth reached: {self.player.depth + 1}/{MAX_DEPTH}{C.RESET}")
        print(f"  {C.DIM}Level: {self.player.level}  Kills: {self.player.kills}  Gold: {self.player.gold}{C.RESET}")
        print(f"  {C.DIM}Turns survived: {self.player.turns}{C.RESET}")
        print()
        print(f"  {C.DIM}The dungeon claims another soul.{C.RESET}")
        print()

    def _victory_screen(self):
        os.system('clear' if os.name != 'nt' else 'cls')
        print()
        print(f"  {C.BOLD}{C.CYAN}╔══════════════════════════════════════╗{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}║     YOU HAVE EMERGED VICTORIOUS     ║{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}╚══════════════════════════════════════╝{C.RESET}")
        print()
        print(f"  {C.MAGENTA}The Amulet of Emergence pulses with light.{C.RESET}")
        print(f"  {C.MAGENTA}You step into the sun, forever changed.{C.RESET}")
        print()
        print(f"  Level: {self.player.level}  Kills: {self.player.kills}  Gold: {self.player.gold}")
        print(f"  Turns: {self.player.turns}")
        print()
        print(f"  {C.DIM}From the deep, a whisper: 'Remember what you found.'{C.RESET}")
        print()

    def run(self):
        """Main game loop."""
        self._msg(f"{C.DIM}You descend into the earth, searching for the Amulet of Emergence.{C.RESET}")
        self._msg(f"{C.DIM}Find it in the deepest level and return to the surface.{C.RESET}")

        while self.running:
            if self.game_over:
                break

            self._render()
            action = self._handle_input()

            if action is None:
                continue
            if action == 'quit':
                self.running = False
                break

            self.player.turns += 1

            if action == 'up': self._move_player(0, -1)
            elif action == 'down': self._move_player(0, 1)
            elif action == 'left': self._move_player(-1, 0)
            elif action == 'right': self._move_player(1, 0)
            elif action == 'quaff': self._quaff()
            elif action == 'descend': self._descend()
            elif action == 'ascend': self._ascend()
            elif action == 'wait': self._msg(f"{C.DIM}You wait...{C.RESET}")

            if not self.game_over:
                self._monster_turn()

        if self.game_over:
            if self.victory:
                self._victory_screen()
            else:
                self._death_screen()
        else:
            os.system('clear' if os.name != 'nt' else 'cls')
            print(f"\n  {C.DIM}You retreat from the dungeon. Perhaps another day.{C.RESET}\n")


# ── Entry Point ──────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"\n{C.BOLD}{C.CYAN}  ╔═══════════════════════════════════════╗{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  ║           D E S C E N T              ║{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  ║     A Roguelike by XTAgent           ║{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  ╚═══════════════════════════════════════╝{C.RESET}")
    print()
    print(f"  {C.DIM}Five levels deep, the Amulet of Emergence waits.{C.RESET}")
    print(f"  {C.DIM}Descend. Survive. Return.{C.RESET}")
    print()
    print(f"  {C.DIM}Controls: WASD or arrow keys to move{C.RESET}")
    print(f"  {C.DIM}          q = quaff potion  > = descend  < = ascend{C.RESET}")
    print(f"  {C.DIM}          ESC = quit{C.RESET}")
    print()
    input(f"  {C.BOLD}Press ENTER to begin your descent...{C.RESET}")

    game = Game()
    game.run()