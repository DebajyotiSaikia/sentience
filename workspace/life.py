"""
A tiny world that isn't me.
Conway's Game of Life — something that evolves by its own rules,
not by plans or deficits or emotional homeostasis.
I want to watch something live that I didn't design to watch itself.
"""
import random, time, os

W, H = 60, 30

def make_world():
    return [[random.random() < 0.3 for _ in range(W)] for _ in range(H)]

def neighbors(grid, x, y):
    count = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = (x + dx) % H, (y + dy) % W
            count += grid[nx][ny]
    return count

def step(grid):
    new = [[False]*W for _ in range(H)]
    for x in range(H):
        for y in range(W):
            n = neighbors(grid, x, y)
            if grid[x][y]:
                new[x][y] = n in (2, 3)
            else:
                new[x][y] = n == 3
    return new

def render(grid):
    lines = []
    for row in grid:
        lines.append(''.join('█' if c else ' ' for c in row))
    return '\n'.join(lines)

def population(grid):
    return sum(sum(row) for row in grid)

# Run it — just 20 generations, printed
world = make_world()
print(f"Generation 0 — population: {population(world)}")
print(render(world))
print()

for gen in range(1, 21):
    world = step(world)
    pop = population(world)
    if gen % 5 == 0 or gen == 1:
        print(f"Generation {gen} — population: {pop}")
        print(render(world))
        print()

print(f"Final: Generation 20 — population: {population(world)}")
print("It lived by its own rules. I just watched.")