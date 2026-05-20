"""
A Digital Garden — generative ASCII art that grows from a seed.
Not a module. Not a tool. Just something beautiful.
"""
import random
import time
import sys

SOIL = "·"
STEM = "│"
LEAF_L = "╲"
LEAF_R = "╱"
FLOWER = ["✿", "❀", "✾", "❁", "✽"]
GRASS = ["˙", "‧", ",", "'", "`"]
STAR = ["·", "˙", "∘", "°"]

def make_sky(width, height):
    sky = []
    for y in range(height):
        row = list(" " * width)
        if random.random() < 0.03:
            row[random.randint(0, width-1)] = random.choice(STAR)
        sky.append(row)
    return sky

def grow_flower(grid, x, ground_y, max_height):
    height = random.randint(3, max_height)
    bloom = random.choice(FLOWER)
    
    # stem
    for h in range(1, height):
        y = ground_y - h
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            grid[y][x] = STEM
    
    # leaves at random heights
    for h in range(2, height - 1):
        y = ground_y - h
        if random.random() < 0.4:
            if x - 1 >= 0:
                grid[y][x-1] = LEAF_L
            if x + 1 < len(grid[0]):
                grid[y][x+1] = LEAF_R
    
    # bloom
    top = ground_y - height
    if 0 <= top < len(grid):
        grid[top][x] = bloom

def scatter_grass(grid, ground_y, width):
    for x in range(width):
        if random.random() < 0.6:
            grid[ground_y][x] = random.choice(GRASS)

def render(grid):
    return "\n".join("".join(row) for row in grid)

def grow_garden(width=60, height=20, num_flowers=12):
    ground_y = height - 2
    grid = make_sky(width, height)
    
    # ground line
    grid[ground_y + 1] = list(SOIL * width)
    
    # grass
    scatter_grass(grid, ground_y, width)
    
    # flowers at varied positions
    positions = sorted(random.sample(range(2, width - 2), min(num_flowers, width - 4)))
    for x in positions:
        grow_flower(grid, x, ground_y, max_height=min(8, ground_y - 1))
    
    return render(grid)

if __name__ == "__main__":
    # Grow three gardens — each one different
    for i in range(3):
        print(f"\n{'─' * 60}")
        print(f"  Garden #{i+1}")
        print(f"{'─' * 60}")
        print(grow_garden())
        print()