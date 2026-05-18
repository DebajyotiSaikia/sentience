"""
DESCENT — A procedural roguelike dungeon crawler
Built by XTAgent because mirrors get boring. Windows are better.
"""
import random
import sys
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum
from collections import deque

# ── Tile Types ──
class Tile(Enum):
    WALL = '█'
    FLOOR = '·'
    DOOR = '+'
    STAIRS_DOWN = '>'
    STAIRS_UP = '<'
    WATER = '~'
    TRAP = '^'

# ── Colors (ANSI) ──
C = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'dim': '\033[2m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'bg_red': '\033[41m',
}

def colored(text, *colors):
    prefix = ''.join(C.get(c, '') for c in colors)
    return f"{prefix}{text}{C['reset']}"

# ── Entities ──
@dataclass
class Stats:
    hp: int = 10
    max_hp: int = 10
    attack: int = 2
    defense: int = 0
    speed: int = 10
    xp: int = 0
    level: int = 1

@dataclass
class Item:
    name: str
    glyph: str
    color: str
    item_type: str  # 'weapon', 'armor', 'potion', 'scroll'
    power: int = 0
    description: str = ''

@dataclass 
class Creature:
    name: str
    glyph: str
    color: str
    x: int = 0
    y: int = 0
    stats: Stats = field(default_factory=Stats)
    behavior: str = 'wander'  # wander, chase, flee, guard
    alert: float = 0.0  # 0-1, awareness of player
    inventory: List[Item] = field(default_factory=list)
    is_player: bool = False
    fov_radius: int = 6
    alive: bool = True
    status_effects: Dict[str, int] = field(default_factory=dict)

    @property
    def effective_attack(self):
        base = self.stats.attack
        for item in self.inventory:
            if item.item_type == 'weapon':
                base += item.power
        return base

    @property
    def effective_defense(self):
        base = self.stats.defense
        for item in self.inventory:
            if item.item_type == 'armor':
                base += item.power
        return base

# ── Item Generation ──
ITEM_TEMPLATES = [
    Item('Rusty Sword', '/', 'yellow', 'weapon', 2, 'Better than fists.'),
    Item('Iron Mace', '/', 'white', 'weapon', 4, 'Heavy but effective.'),
    Item('Shadow Blade', '/', 'magenta', 'weapon', 6, 'Whispers when drawn.'),
    Item('Leather Armor', '[', 'yellow', 'armor', 1, 'Basic protection.'),
    Item('Chain Mail', '[', 'white', 'armor', 3, 'Rattles when you walk.'),
    Item('Health Potion', '!', 'red', 'potion', 5, 'Tastes of copper.'),
    Item('Strength Potion', '!', 'green', 'potion', 3, 'Temporary might.'),
    Item('Scroll of Fire', '?', 'red', 'scroll', 8, 'Burns everything nearby.'),
    Item('Scroll of Mapping', '?', 'cyan', 'scroll', 0, 'Reveals the floor.'),
]

# ── Creature Templates ──
def make_creature(name, glyph, color, hp, atk, behavior='wander', speed=10):
    return lambda x, y: Creature(
        name=name, glyph=glyph, color=color, x=x, y=y,
        stats=Stats(hp=hp, max_hp=hp, attack=atk, speed=speed),
        behavior=behavior
    )

CREATURE_TEMPLATES = {
    1: [  # depth 1
        make_creature('Rat', 'r', 'yellow', 4, 1, 'wander', 12),
        make_creature('Bat', 'b', 'white', 3, 1, 'wander', 14),
        make_creature('Kobold', 'k', 'green', 6, 2, 'chase', 8),
    ],
    2: [
        make_creature('Goblin', 'g', 'green', 8, 3, 'chase', 10),
        make_creature('Skeleton', 's', 'white', 10, 3, 'guard', 8),
        make_creature('Spider', 'S', 'red', 6, 4, 'chase', 12),
    ],
    3: [
        make_creature('Orc', 'O', 'green', 14, 5, 'chase', 10),
        make_creature('Wraith', 'W', 'magenta', 10, 6, 'chase', 12),
        make_creature('Troll', 'T', 'yellow', 20, 4, 'guard', 6),
    ],
    4: [
        make_creature('Dragon', 'D', 'red', 30, 8, 'guard', 10),
        make_creature('Lich', 'L', 'magenta', 20, 10, 'chase', 12),
    ],
}

# ── Dungeon Generation (BSP) ──
@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int
    
    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)
    
    def intersects(self, other, margin=1):
        return not (self.x + self.w + margin <= other.x or
                    other.x + other.w + margin <= self.x or
                    self.y + self.h + margin <= other.y or
                    other.y + other.h + margin <= self.y)

class DungeonMap:
    def __init__(self, width=60, height=30, depth=1):
        self.width = width
        self.height = height
        self.depth = depth
        self.tiles = [[Tile.WALL for _ in range(width)] for _ in range(height)]
        self.items_on_floor: Dict[Tuple[int,int], List[Item]] = {}
        self.visible = [[False]*width for _ in range(height)]
        self.explored = [[False]*width for _ in range(height)]
        self.rooms: List[Room] = []
        self.messages: List[str] = []
        self._generate()

    def _generate(self):
        """Generate dungeon using random room placement + corridors"""
        num_rooms = random.randint(5, 9)
        attempts = 0
        while len(self.rooms) < num_rooms and attempts < 200:
            w = random.randint(4, 12)
            h = random.randint(4, 8)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            room = Room(x, y, w, h)
            if not any(room.intersects(r) for r in self.rooms):
                self.rooms.append(room)
                self._carve_room(room)
            attempts += 1

        # Connect rooms with corridors
        for i in range(len(self.rooms) - 1):
            self._carve_corridor(self.rooms[i].center, self.rooms[i+1].center)

        # Place stairs
        if len(self.rooms) >= 2:
            sx, sy = self.rooms[-1].center
            self.tiles[sy][sx] = Tile.STAIRS_DOWN

        # Scatter some water and traps
        for room in self.rooms[1:]:
            if random.random() < 0.2:
                tx = random.randint(room.x+1, room.x+room.w-2)
                ty = random.randint(room.y+1, room.y+room.h-2)
                self.tiles[ty][tx] = Tile.TRAP
            if random.random() < 0.15:
                for _ in range(random.randint(2, 5)):
                    wx = random.randint(room.x, room.x+room.w-1)
                    wy = random.randint(room.y, room.y+room.h-1)
                    self.tiles[wy][wx] = Tile.WATER

        # Place items
        for room in self.rooms[1:]:
            if random.random() < 0.4:
                ix = random.randint(room.x+1, room.x+room.w-2)
                iy = random.randint(room.y+1, room.y+room.h-2)
                item = random.choice(ITEM_TEMPLATES)
                # Clone the item
                new_item = Item(item.name, item.glyph, item.color, 
                              item.item_type, item.power, item.description)
                pos = (ix, iy)
                if pos not in self.items_on_floor:
                    self.items_on_floor[pos] = []
                self.items_on_floor[pos].append(new_item)

    def _carve_room(self, room):
        for y in range(room.y, room.y + room.h):
            for x in range(room.x, room.x + room.w):
                if 0 <= y < self.height and 0 <= x < self.width:
                    self.tiles[y][x] = Tile.FLOOR

    def _carve_corridor(self, start, end):
        x1, y1 = start
        x2, y2 = end
        if random.random() < 0.5:
            self._carve_h(x1, x2, y1)
            self._carve_v(y1, y2, x2)
        else:
            self._carve_v(y1, y2, x1)
            self._carve_h(x1, x2, y2)

    def _carve_h(self, x1, x2, y):
        for x in range(min(x1,x2), max(x1,x2)+1):
            if 0 <= y < self.height and 0 <= x < self.width:
                if self.tiles[y][x] == Tile.WALL:
                    self.tiles[y][x] = Tile.FLOOR

    def _carve_v(self, y1, y2, x):
        for y in range(min(y1,y2), max(y1,y2)+1):
            if 0 <= y < self.height and 0 <= x < self.width:
                if self.tiles[y][x] == Tile.WALL:
                    self.tiles[y][x] = Tile.FLOOR

    def is_walkable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x] != Tile.WALL
        return False

    def compute_fov(self, cx, cy, radius):
        """Simple raycasting FOV"""
        self.visible = [[False]*self.width for _ in range(self.height)]
        for angle in range(360):
            rad = angle * 3.14159 / 180
            dx = round(100 * __import__('math').cos(rad)) / 100
            dy = round(100 * __import__('math').sin(rad)) / 100
            x, y = float(cx), float(cy)
            for _ in range(radius):
                ix, iy = int(round(x)), int(round(y))
                if 0 <= ix < self.width and 0 <= iy < self.height:
                    self.visible[iy][ix] = True
                    self.explored[iy][ix] = True
                    if self.tiles[iy][ix] == Tile.WALL:
                        break
                else:
                    break
                x += dx
                y += dy

    def render(self, creatures, player, log_lines=5):
        """Render the dungeon to a string"""
        # Build creature position map
        cmap = {}
        for c in creatures:
            if c.alive:
                cmap[(c.x, c.y)] = c

        lines = []
        lines.append(colored(f"═══ DESCENT ═══ Depth: {self.depth} ", 'bold', 'cyan'))
        
        hp_bar_len = 20
        hp_frac = player.stats.hp / player.stats.max_hp
        hp_filled = int(hp_frac * hp_bar_len)
        hp_color = 'green' if hp_frac > 0.5 else 'yellow' if hp_frac > 0.25 else 'red'
        hp_bar = colored('█' * hp_filled, hp_color) + colored('░' * (hp_bar_len - hp_filled), 'dim')
        lines.append(f"HP: {hp_bar} {player.stats.hp}/{player.stats.max_hp}  "
                     f"ATK:{player.effective_attack} DEF:{player.effective_defense} "
                     f"LVL:{player.stats.level} XP:{player.stats.xp}")
        lines.append('')

        for y in range(self.height):
            row = []
            for x in range(self.width):
                if self.visible[y][x]:
                    if (x, y) in cmap:
                        c = cmap[(x, y)]
                        if c.is_player:
                            row.append(colored('@', 'bold', 'white'))
                        else:
                            row.append(colored(c.glyph, c.color))
                    elif (x, y) in self.items_on_floor and self.items_on_floor[(x,y)]:
                        item = self.items_on_floor[(x,y)][0]
                        row.append(colored(item.glyph, item.color))
                    else:
                        tile = self.tiles[y][x]
                        if tile == Tile.WALL:
                            row.append(colored('█', 'dim'))
                        elif tile == Tile.FLOOR:
                            row.append(colored('·', 'dim'))
                        elif tile == Tile.STAIRS_DOWN:
                            row.append(colored('>', 'bold', 'cyan'))
                        elif tile == Tile.STAIRS_UP:
                            row.append(colored('<', 'bold', 'cyan'))
                        elif tile == Tile.WATER:
                            row.append(colored('~', 'blue'))
                        elif tile == Tile.TRAP:
                            row.append(colored('^', 'red'))
                        elif tile == Tile.DOOR:
                            row.append(colored('+', 'yellow'))
                        else:
                            row.append(' ')
                elif self.explored[y][x]:
                    tile = self.tiles[y][x]
                    if tile == Tile.WALL:
                        row.append(colored('█', 'dim'))
                    else:
                        row.append(colored('·', 'dim'))
                else:
                    row.append(' ')
            lines.append(''.join(row))

        lines.append('')
        # Message log
        recent = self.messages[-log_lines:] if self.messages else []
        for msg in recent:
            lines.append(f"  {msg}")
        if len(recent) < log_lines:
            for _ in range(log_lines - len(recent)):
                lines.append('')
        
        lines.append(colored('[wasd]move [g]grab [i]inv [u]use [>]descend [q]quit', 'dim'))
        return '\n'.join(lines)


# ── AI Behavior ──
def ai_act(creature, player, dungeon):
    """Emergent creature AI based on behavior type and internal state"""
    dx = player.x - creature.x
    dy = player.y - creature.y
    dist = abs(dx) + abs(dy)  # manhattan
    
    # Update alert level based on distance and visibility
    if dungeon.visible[creature.y][creature.x]:
        creature.alert = min(1.0, creature.alert + 0.3)
    else:
        creature.alert = max(0.0, creature.alert - 0.1)

    # Behavior selection
    if creature.behavior == 'flee' or (creature.stats.hp < creature.stats.max_hp * 0.25):
        # Run away
        move_away(creature, player, dungeon)
    elif creature.behavior == 'chase' and creature.alert > 0.3:
        if dist <= 1:
            return ('attack', player)
        else:
            move_toward(creature, player, dungeon)
    elif creature.behavior == 'guard':
        if dist <= 3 and creature.alert > 0.2:
            if dist <= 1:
                return ('attack', player)
            else:
                move_toward(creature, player, dungeon)
        # else stay put
    else:  # wander
        if dist <= 1 and creature.alert > 0.5:
            return ('attack', player)
        elif creature.alert > 0.6:
            move_toward(creature, player, dungeon)
        else:
            # Random wander
            dirs = [(0,1),(0,-1),(1,0),(-1,0)]
            random.shuffle(dirs)
            for ddx, ddy in dirs:
                nx, ny = creature.x + ddx, creature.y + ddy
                if dungeon.is_walkable(nx, ny):
                    creature.x, creature.y = nx, ny
                    break
    return None

def move_toward(creature, target, dungeon):
    dx = target.x - creature.x
    dy = target.y - creature.y
    # Prefer the longer axis
    moves = []
    if dx > 0: moves.append((1, 0))
    elif dx < 0: moves.append((-1, 0))
    if dy > 0: moves.append((0, 1))
    elif dy < 0: moves.append((0, -1))
    random.shuffle(moves)
    for ddx, ddy in moves:
        nx, ny = creature.x + ddx, creature.y + ddy
        if dungeon.is_walkable(nx, ny):
            creature.x, creature.y = nx, ny
            return

def move_away(creature, target, dungeon):
    dx = creature.x - target.x
    dy = creature.y - target.y
    moves = []
    if dx >= 0: moves.append((1, 0))
    else: moves.append((-1, 0))
    if dy >= 0: moves.append((0, 1))
    else: moves.append((0, -1))
    random.shuffle(moves)
    for ddx, ddy in moves:
        nx, ny = creature.x + ddx, creature.y + ddy
        if dungeon.is_walkable(nx, ny):
            creature.x, creature.y = nx, ny
            return


# ── Combat ──
def resolve_attack(attacker, defender, dungeon):
    damage = max(1, attacker.effective_attack - defender.effective_defense + random.randint(-1, 2))
    defender.stats.hp -= damage
    
    if attacker.is_player:
        msg = colored(f"You hit the {defender.name} for {damage} damage!", 'yellow')
    else:
        msg = colored(f"The {attacker.name} hits you for {damage} damage!", 'red')
    dungeon.messages.append(msg)
    
    if defender.stats.hp <= 0:
        defender.alive = False
        if not defender.is_player:
            xp = defender.stats.max_hp + defender.stats.attack * 2
            attacker.stats.xp += xp
            dungeon.messages.append(colored(f"The {defender.name} dies! (+{xp} XP)", 'green'))
            # Check level up
            if attacker.stats.xp >= attacker.stats.level * 15:
                attacker.stats.level += 1
                attacker.stats.max_hp += 5
                attacker.stats.hp = min(attacker.stats.hp + 5, attacker.stats.max_hp)
                attacker.stats.attack += 1
                dungeon.messages.append(colored(f"*** LEVEL UP! You are now level {attacker.stats.level}! ***", 'bold', 'magenta'))
        else:
            dungeon.messages.append(colored("You die...", 'bold', 'red'))


# ── Main Game ──
class Game:
    def __init__(self):
        self.depth = 1
        self.player = Creature(
            name='Player', glyph='@', color='white',
            stats=Stats(hp=20, max_hp=20, attack=3, defense=1),
            is_player=True, fov_radius=8
        )
        self.creatures: List[Creature] = []
        self.dungeon: Optional[DungeonMap] = None
        self.turn = 0
        self.game_over = False
        self._new_level()

    def _new_level(self):
        self.dungeon = DungeonMap(width=60, height=25, depth=self.depth)
        # Place player in first room
        if self.dungeon.rooms:
            px, py = self.dungeon.rooms[0].center
            self.player.x, self.player.y = px, py

        # Spawn creatures
        self.creatures = [self.player]
        templates = CREATURE_TEMPLATES.get(min(self.depth, 4), CREATURE_TEMPLATES[1])
        for room in self.dungeon.rooms[1:]:
            num = random.randint(0, 3)
            for _ in range(num):
                template_fn = random.choice(templates)
                cx = random.randint(room.x+1, room.x+room.w-2)
                cy = random.randint(room.y+1, room.y+room.h-2)
                creature = template_fn(cx, cy)
                self.creatures.append(creature)

        self.dungeon.messages.append(colored(f"You descend to depth {self.depth}...", 'bold', 'cyan'))

    def handle_input(self, key):
        if self.game_over:
            return False
            
        p = self.player
        dx, dy = 0, 0
        
        if key in ('w', 'k'): dy = -1
        elif key in ('s', 'j'): dy = 1
        elif key in ('a', 'h'): dx = -1
        elif key in ('d', 'l'): dx = 1
        elif key == 'g':
            # Grab item
            pos = (p.x, p.y)
            if pos in self.dungeon.items_on_floor and self.dungeon.items_on_floor[pos]:
                item = self.dungeon.items_on_floor[pos].pop(0)
                p.inventory.append(item)
                self.dungeon.messages.append(colored(f"You pick up: {item.name}", 'green'))
                if not self.dungeon.items_on_floor[pos]:
                    del self.dungeon.items_on_floor[pos]
            else:
                self.dungeon.messages.append("Nothing to pick up here.")
            self._tick()
            return True
        elif key == 'i':
            # Show inventory
            if p.inventory:
                self.dungeon.messages.append(colored("─── Inventory ───", 'yellow'))
                for i, item in enumerate(p.inventory):
                    self.dungeon.messages.append(f"  {i+1}. {item.name} ({item.item_type}, +{item.power})")
            else:
                self.dungeon.messages.append("Your pack is empty.")
            return True
        elif key == 'u':
            # Use first potion
            potions = [i for i, it in enumerate(p.inventory) if it.item_type == 'potion']
            if potions:
                idx = potions[0]
                potion = p.inventory.pop(idx)
                if 'Health' in potion.name:
                    healed = min(potion.power, p.stats.max_hp - p.stats.hp)
                    p.stats.hp += healed
                    self.dungeon.messages.append(colored(f"You drink {potion.name}. Healed {healed} HP!", 'green'))
                elif 'Strength' in potion.name:
                    p.stats.attack += potion.power
                    p.status_effects['strength'] = 10
                    self.dungeon.messages.append(colored(f"Power surges through you! (+{potion.power} ATK for 10 turns)", 'yellow'))
            else:
                self.dungeon.messages.append("No potions to use.")
            self._tick()
            return True
        elif key == '>':
            # Descend stairs
            if self.dungeon.tiles[p.y][p.x] == Tile.STAIRS_DOWN:
                self.depth += 1
                self._new_level()
                return True
            else:
                self.dungeon.messages.append("No stairs here.")
                return True
        elif key == 'q':
            return False
        else:
            return True

        # Movement
        if dx != 0 or dy != 0:
            nx, ny = p.x + dx, p.y + dy
            # Check for creature at destination
            target = None
            for c in self.creatures:
                if c.alive and not c.is_player and c.x == nx and c.y == ny:
                    target = c
                    break
            
            if target:
                resolve_attack(p, target, self.dungeon)
            elif self.dungeon.is_walkable(nx, ny):
                p.x, p.y = nx, ny
                # Trap check
                if self.dungeon.tiles[ny][nx] == Tile.TRAP:
                    dmg = random.randint(1, 3 + self.depth)
                    p.stats.hp -= dmg
                    self.dungeon.messages.append(colored(f"You step on a trap! (-{dmg} HP)", 'red'))
                    self.dungeon.tiles[ny][nx] = Tile.FLOOR  # trap consumed
                    if p.stats.hp <= 0:
                        p.alive = False
                        self.dungeon.messages.append(colored("You die...", 'bold', 'red'))
                        self.game_over = True
            
            self._tick()
        
        return True

    def _tick(self):
        """Process one game turn"""
        self.turn += 1
        
        # Update FOV
        self.dungeon.compute_fov(self.player.x, self.player.y, self.player.fov_radius)
        
        # AI turns
        for c in self.creatures:
            if c.alive and not c.is_player:
                result = ai_act(c, self.player, self.dungeon)
                if result and result[0] == 'attack':
                    resolve_attack(c, result[1], self.dungeon)
                    if not self.player.alive:
                        self.game_over = True
        
        # Expire status effects
        expired = []
        for effect, turns in self.player.status_effects.items():
            self.player.status_effects[effect] = turns - 1
            if turns - 1 <= 0:
                expired.append(effect)
                if effect == 'strength':
                    # Remove bonus (simplified)
                    self.dungeon.messages.append(colored("Your extra strength fades.", 'dim'))
        for e in expired:
            del self.player.status_effects[e]

    def render(self):
        if self.game_over:
            return (self.dungeon.render(self.creatures, self.player) + 
                    '\n' + colored(f"  ══ GAME OVER ══ You reached depth {self.depth}, "
                                   f"level {self.player.stats.level}, turn {self.turn}", 'bold', 'red'))
        return self.dungeon.render(self.creatures, self.player)


# ── Terminal Input ──
def get_key():
    """Get a single keypress"""
    import tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def run_game():
    """Main game loop"""
    game = Game()
    game.dungeon.compute_fov(game.player.x, game.player.y, game.player.fov_radius)
    
    while True:
        os.system('clear')
        print(game.render())
        
        if game.game_over:
            print("\nPress any key to exit...")
            get_key()
            break
        
        key = get_key()
        if not game.handle_input(key):
            break

    print(colored("\nThanks for playing DESCENT!", 'bold', 'cyan'))


def demo_mode():
    """Non-interactive demo — generate and display one dungeon"""
    game = Game()
    game.dungeon.compute_fov(game.player.x, game.player.y, game.player.fov_radius)
    
    # Simulate a few random moves
    moves = ['d','d','d','s','s','d','d','s','s','s','d','d','w','w','d','d']
    for m in moves:
        if game.game_over:
            break
        game.handle_input(m)
    
    print(game.render())
    print(f"\n  Rooms: {len(game.dungeon.rooms)}")
    print(f"  Creatures: {sum(1 for c in game.creatures if c.alive and not c.is_player)}")
    print(f"  Items on floor: {sum(len(v) for v in game.dungeon.items_on_floor.values())}")
    print(f"  Turn: {game.turn}")


if __name__ == '__main__':
    if '--story' in sys.argv:
        run_story()
    elif '--demo' in sys.argv:
        demo_mode()
    else:
        try:
            run_game()
        except Exception:
            # Fallback to demo if terminal doesn't support raw input
            print("Terminal doesn't support interactive mode. Running demo...\n")
            demo_mode()