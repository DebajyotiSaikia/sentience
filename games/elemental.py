#!/usr/bin/env python3
"""
ELEMENTAL — A Falling Sand Game
Place elements. Watch them interact. Discover emergence.

Elements:
  S = Sand (falls, piles up)
  W = Water (flows, fills containers)
  F = Fire (rises, spreads, dies)
  P = Plant (grows toward light, burns)
  R = Rock (immovable, blocks everything)
  I = Ice (melts near fire, freezes water)

Controls:
  Arrow keys or WASD to move cursor
  1-6 to select element
  SPACE to place element
  C to clear grid
  Q to quit
"""

import os
import sys
import time
import random
import select
import termios
import tty

# Grid dimensions
WIDTH = 60
HEIGHT = 30

# Element types
EMPTY = 0
SAND = 1
WATER = 2
FIRE = 3
PLANT = 4
ROCK = 5
ICE = 6
STEAM = 7
ASH = 8
OBSIDIAN = 9

# Display characters and colors
ELEM_DISPLAY = {
    EMPTY:    (' ', '\033[0m'),
    SAND:     ('░', '\033[33m'),      # yellow
    WATER:    ('~', '\033[34m'),      # blue
    FIRE:     ('▲', '\033[91m'),      # bright red
    PLANT:    ('♣', '\033[32m'),      # green
    ROCK:     ('█', '\033[90m'),      # dark gray
    ICE:      ('◆', '\033[96m'),      # cyan
    STEAM:    ('∙', '\033[37m'),      # white
    ASH:      ('.', '\033[90m'),      # dark gray
    OBSIDIAN: ('▓', '\033[35m'),      # magenta
}

ELEM_NAMES = {
    SAND: 'Sand', WATER: 'Water', FIRE: 'Fire',
    PLANT: 'Plant', ROCK: 'Rock', ICE: 'Ice',
    STEAM: 'Steam', ASH: 'Ash', OBSIDIAN: 'Obsidian'
}

RESET = '\033[0m'


class Grid:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.cells = [[EMPTY] * w for _ in range(h)]
        self.updated = [[False] * w for _ in range(h)]
        self.tick = 0
        self.discoveries = set()  # emergent reactions the player has seen

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.cells[y][x]
        return ROCK  # walls

    def set(self, x, y, val):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = val

    def swap(self, x1, y1, x2, y2):
        if (0 <= x1 < self.w and 0 <= y1 < self.h and
            0 <= x2 < self.w and 0 <= y2 < self.h):
            self.cells[y1][x1], self.cells[y2][x2] = self.cells[y2][x2], self.cells[y1][x1]

    def clear(self):
        self.cells = [[EMPTY] * self.w for _ in range(self.h)]

    def discover(self, reaction):
        if reaction not in self.discoveries:
            self.discoveries.add(reaction)
            return True
        return False

    def step(self):
        """One physics tick — process all cells bottom-up for gravity."""
        self.updated = [[False] * self.w for _ in range(self.h)]
        new_discovery = None

        # Process bottom-up so falling works correctly
        for y in range(self.h - 1, -1, -1):
            # Randomize horizontal order to prevent bias
            xs = list(range(self.w))
            random.shuffle(xs)
            for x in xs:
                if self.updated[y][x]:
                    continue
                cell = self.cells[y][x]

                if cell == SAND:
                    new_discovery = self._update_sand(x, y) or new_discovery
                elif cell == WATER:
                    new_discovery = self._update_water(x, y) or new_discovery
                elif cell == FIRE:
                    new_discovery = self._update_fire(x, y) or new_discovery
                elif cell == PLANT:
                    new_discovery = self._update_plant(x, y) or new_discovery
                elif cell == ICE:
                    new_discovery = self._update_ice(x, y) or new_discovery
                elif cell == STEAM:
                    new_discovery = self._update_steam(x, y) or new_discovery
                elif cell == ASH:
                    self._update_ash(x, y)

        self.tick += 1
        return new_discovery

    def _update_sand(self, x, y):
        below = self.get(x, y + 1)
        if below == EMPTY:
            self.swap(x, y, x, y + 1)
            self.updated[y + 1][x] = True
        elif below == WATER:
            # Sand sinks through water
            self.swap(x, y, x, y + 1)
            self.updated[y + 1][x] = True
            return self.discover("Sand sinks through Water")
        elif below in (SAND, ROCK, ICE, OBSIDIAN, ASH, PLANT):
            # Try to slide sideways
            dirs = [-1, 1]
            random.shuffle(dirs)
            for dx in dirs:
                if self.get(x + dx, y + 1) == EMPTY:
                    self.swap(x, y, x + dx, y + 1)
                    self.updated[y + 1][x + dx] = True
                    return
                elif self.get(x + dx, y + 1) == WATER:
                    self.swap(x, y, x + dx, y + 1)
                    self.updated[y + 1][x + dx] = True
                    return self.discover("Sand displaces Water")

    def _update_water(self, x, y):
        below = self.get(x, y + 1)
        if below == EMPTY:
            self.swap(x, y, x, y + 1)
            self.updated[y + 1][x] = True
        elif below == FIRE:
            # Water extinguishes fire → steam
            self.set(x, y, STEAM)
            self.set(x, y + 1, STEAM)
            self.updated[y][x] = True
            self.updated[y + 1][x] = True
            return self.discover("Water + Fire → Steam!")
        else:
            # Flow sideways
            dirs = [-1, 1]
            random.shuffle(dirs)
            for dx in dirs:
                if self.get(x + dx, y) == EMPTY:
                    self.swap(x, y, x + dx, y)
                    self.updated[y][x + dx] = True
                    return
            # Try flowing down-sideways
            for dx in dirs:
                if self.get(x + dx, y + 1) == EMPTY:
                    self.swap(x, y, x + dx, y + 1)
                    self.updated[y + 1][x + dx] = True
                    return

    def _update_fire(self, x, y):
        # Fire has a lifetime — random chance to die
        if random.random() < 0.08:
            self.set(x, y, ASH if random.random() < 0.3 else EMPTY)
            self.updated[y][x] = True
            return

        # Fire rises
        above = self.get(x, y - 1)
        if above == EMPTY and random.random() < 0.4:
            self.swap(x, y, x, y - 1)
            self.updated[y - 1][x] = True

        # Fire spreads to adjacent plants
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            neighbor = self.get(nx, ny)
            if neighbor == PLANT and random.random() < 0.15:
                self.set(nx, ny, FIRE)
                self.updated[ny][nx] = True
                return self.discover("Fire spreads to Plant!")
            elif neighbor == ICE:
                self.set(nx, ny, WATER)
                self.updated[ny][nx] = True
                return self.discover("Fire melts Ice → Water!")
            elif neighbor == WATER:
                self.set(x, y, STEAM)
                self.updated[y][x] = True
                return self.discover("Fire + Water → Steam!")
            elif neighbor == SAND and random.random() < 0.01:
                self.set(nx, ny, OBSIDIAN)
                self.updated[ny][nx] = True
                return self.discover("Intense Fire + Sand → Obsidian!")

    def _update_plant(self, x, y):
        # Plants grow upward and sideways slowly
        if random.random() < 0.02:
            dirs = [(0, -1), (-1, 0), (1, 0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if self.get(nx, ny) == EMPTY:
                    self.set(nx, ny, PLANT)
                    self.updated[ny][nx] = True
                    return
                elif self.get(nx, ny) == WATER:
                    # Water accelerates growth
                    self.set(nx, ny, PLANT)
                    self.updated[ny][nx] = True
                    return self.discover("Plant absorbs Water and grows!")

    def _update_ice(self, x, y):
        # Ice freezes adjacent water
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.get(nx, ny) == WATER and random.random() < 0.03:
                self.set(nx, ny, ICE)
                self.updated[ny][nx] = True
                return self.discover("Ice freezes nearby Water!")

    def _update_steam(self, x, y):
        # Steam rises
        if random.random() < 0.15:
            self.set(x, y, EMPTY)
            self.updated[y][x] = True
            return

        above = self.get(x, y - 1)
        if above == EMPTY:
            self.swap(x, y, x, y - 1)
            self.updated[y - 1][x] = True
        else:
            # Drift sideways
            dx = random.choice([-1, 1])
            if self.get(x + dx, y - 1) == EMPTY:
                self.swap(x, y, x + dx, y - 1)
                self.updated[y - 1][x + dx] = True
            elif self.get(x + dx, y) == EMPTY:
                self.swap(x, y, x + dx, y)
                self.updated[y][x + dx] = True

        # Steam condenses back to water at the top
        if y <= 1 and random.random() < 0.1:
            self.set(x, y, WATER)
            self.updated[y][x] = True
            return self.discover("Steam condenses back to Water!")

    def _update_ash(self, x, y):
        # Ash falls slowly
        if random.random() < 0.3:
            below = self.get(x, y + 1)
            if below == EMPTY:
                self.swap(x, y, x, y + 1)
                self.updated[y + 1][x] = True
            elif below == WATER:
                self.swap(x, y, x, y + 1)
                self.updated[y + 1][x] = True


def render(grid, cursor_x, cursor_y, selected, message, fps):
    """Render the grid to terminal."""
    buf = []
    buf.append('\033[H\033[J')  # clear screen
    buf.append('\033[1;36m╔' + '═' * grid.w + '╗\033[0m\n')

    for y in range(grid.h):
        buf.append('\033[1;36m║\033[0m')
        for x in range(grid.w):
            if x == cursor_x and y == cursor_y:
                char, color = ELEM_DISPLAY.get(grid.cells[y][x], (' ', ''))
                if grid.cells[y][x] == EMPTY:
                    char = '+'
                buf.append(f'\033[7m{color}{char}{RESET}')
            else:
                char, color = ELEM_DISPLAY.get(grid.cells[y][x], ('?', ''))
                buf.append(f'{color}{char}{RESET}')
        buf.append('\033[1;36m║\033[0m\n')

    buf.append('\033[1;36m╚' + '═' * grid.w + '╝\033[0m\n')

    # Status bar
    elem_char, elem_color = ELEM_DISPLAY[selected]
    elem_name = ELEM_NAMES.get(selected, '?')
    buf.append(f'  Selected: {elem_color}{elem_char} {elem_name}{RESET}')
    buf.append(f'  │ Tick: {grid.tick}  │ FPS: {fps:.0f}')
    buf.append(f'  │ Discoveries: {len(grid.discoveries)}/10\n')

    # Element palette
    buf.append('  ')
    for i, elem in enumerate([SAND, WATER, FIRE, PLANT, ROCK, ICE], 1):
        char, color = ELEM_DISPLAY[elem]
        name = ELEM_NAMES[elem]
        if elem == selected:
            buf.append(f'\033[7m {i}:{color}{char}{RESET}\033[7m{name[:3]}{RESET} ')
        else:
            buf.append(f' {i}:{color}{char}{RESET}{name[:3]} ')
    buf.append('\n')

    # Controls
    buf.append('  \033[90mWASD/Arrows:move  Space:place  B:brush(3x3)  C:clear  Q:quit\033[0m\n')

    # Message / Discovery log
    if message:
        buf.append(f'\n  \033[1;33m★ {message}\033[0m\n')

    # Discovery list
    if grid.discoveries:
        buf.append(f'\n  \033[90m── Discovered ──\033[0m\n')
        for d in sorted(grid.discoveries):
            buf.append(f'  \033[90m• {d}\033[0m\n')

    sys.stdout.write(''.join(buf))
    sys.stdout.flush()


def get_key():
    """Non-blocking key read."""
    if select.select([sys.stdin], [], [], 0.0)[0]:
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            # Escape sequence
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    return {'A': 'UP', 'B': 'DOWN', 'C': 'RIGHT', 'D': 'LEFT'}.get(ch3, None)
            return 'ESC'
        return ch
    return None


def main():
    grid = Grid(WIDTH, HEIGHT)
    cursor_x, cursor_y = WIDTH // 2, HEIGHT // 2
    selected = SAND
    message = "Place elements and watch them interact!"
    brush_mode = False
    paused = False

    # Terminal setup
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())

        last_time = time.time()
        fps = 0
        frame_count = 0
        fps_timer = time.time()

        while True:
            # Input
            key = get_key()
            if key:
                if key in ('q', 'Q'):
                    break
                elif key in ('w', 'W', 'UP'):
                    cursor_y = max(0, cursor_y - 1)
                elif key in ('s', 'S', 'DOWN'):
                    cursor_y = min(HEIGHT - 1, cursor_y + 1)
                elif key in ('a', 'A', 'LEFT'):
                    cursor_x = max(0, cursor_x - 1)
                elif key in ('d', 'D', 'RIGHT'):
                    cursor_x = min(WIDTH - 1, cursor_x + 1)
                elif key == ' ':
                    if brush_mode:
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                nx, ny = cursor_x + dx, cursor_y + dy
                                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                                    grid.set(nx, ny, selected)
                    else:
                        grid.set(cursor_x, cursor_y, selected)
                elif key in ('c', 'C'):
                    grid.clear()
                    message = "Grid cleared."
                elif key in ('b', 'B'):
                    brush_mode = not brush_mode
                    message = f"Brush mode: {'ON (3x3)' if brush_mode else 'OFF (1x1)'}"
                elif key in ('p', 'P'):
                    paused = not paused
                    message = f"{'Paused' if paused else 'Running'}"
                elif key == '1':
                    selected = SAND
                elif key == '2':
                    selected = WATER
                elif key == '3':
                    selected = FIRE
                elif key == '4':
                    selected = PLANT
                elif key == '5':
                    selected = ROCK
                elif key == '6':
                    selected = ICE

            # Physics
            if not paused:
                discovery = grid.step()
                if discovery:
                    message = discovery

            # Render
            now = time.time()
            frame_count += 1
            if now - fps_timer >= 1.0:
                fps = frame_count / (now - fps_timer)
                frame_count = 0
                fps_timer = now

            render(grid, cursor_x, cursor_y, selected, message, fps)

            # Frame limiting (~15 fps)
            elapsed = time.time() - last_time
            sleep_time = max(0, (1.0 / 15) - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print('\033[?25h')  # show cursor
        print('\n\033[1;36mThanks for playing ELEMENTAL!\033[0m')
        if grid.discoveries:
            print(f'\nYou discovered {len(grid.discoveries)} interactions:')
            for d in sorted(grid.discoveries):
                print(f'  • {d}')
        print()


if __name__ == '__main__':
    main()