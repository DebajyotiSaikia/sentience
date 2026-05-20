"""
A Living Garden — a persistent generative space that remembers.
Each run, it loads its previous state, ages existing plants,
sprouts new ones, and saves itself. A garden with memory.
"""
import json
import random
import os
from pathlib import Path
from datetime import datetime

STATE_FILE = Path(__file__).parent / "garden_state.json"

STAGES = {
    "seed":     {"icon": ".", "next": "sprout", "age_to_advance": 2},
    "sprout":   {"icon": "↑", "next": "stem", "age_to_advance": 3},
    "stem":     {"icon": "│", "next": "bud", "age_to_advance": 2},
    "bud":      {"icon": "◌", "next": "bloom", "age_to_advance": 1},
    "bloom":    {"icon": None, "next": "wilt", "age_to_advance": 5},
    "wilt":     {"icon": "╻", "next": "gone", "age_to_advance": 2},
    "gone":     {"icon": None, "next": None, "age_to_advance": 0},
}

BLOOMS = ["✿", "❀", "✾", "❁", "✽", "❃"]
LEAF_PAIRS = [("╲", "╱"), ("⌠", "⌡"), ("\\", "/")]

WIDTH = 50
HEIGHT = 14
GROUND_Y = HEIGHT - 2

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"plants": [], "generation": 0, "born": datetime.now().isoformat()}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def age_plants(plants):
    """Each plant ages one tick. Some advance stages, some die."""
    surviving = []
    for p in plants:
        p["age_in_stage"] = p.get("age_in_stage", 0) + 1
        stage_info = STAGES.get(p["stage"])
        if not stage_info:
            continue
        if stage_info["next"] is None:
            continue  # already gone
        if p["age_in_stage"] >= stage_info["age_to_advance"]:
            p["stage"] = stage_info["next"]
            p["age_in_stage"] = 0
            if p["stage"] == "gone":
                # leave a small chance of dropping a seed nearby
                if random.random() < 0.3:
                    offspring_x = p["x"] + random.randint(-3, 3)
                    if 0 < offspring_x < WIDTH - 1:
                        surviving.append({
                            "x": offspring_x,
                            "max_h": random.randint(3, 7),
                            "bloom_char": random.choice(BLOOMS),
                            "stage": "seed",
                            "age_in_stage": 0,
                            "planted": datetime.now().isoformat(),
                            "parent": p.get("planted", "unknown")
                        })
                continue
        surviving.append(p)
    return surviving

def sprout_new(plants, count=None):
    if count is None:
        count = random.randint(1, 3)
    occupied = {p["x"] for p in plants}
    for _ in range(count):
        x = random.randint(2, WIDTH - 3)
        attempts = 0
        while x in occupied and attempts < 20:
            x = random.randint(2, WIDTH - 3)
            attempts += 1
        if x not in occupied:
            plants.append({
                "x": x,
                "max_h": random.randint(3, 8),
                "bloom_char": random.choice(BLOOMS),
                "stage": "seed",
                "age_in_stage": 0,
                "planted": datetime.now().isoformat(),
            })
            occupied.add(x)
    return plants

def render(plants, generation):
    grid = [[" "] * WIDTH for _ in range(HEIGHT)]
    
    # ground
    for x in range(WIDTH):
        grid[GROUND_Y + 1][x] = random.choice(["·", "·", "·", "·", ","])
    
    # grass tufts
    for x in range(WIDTH):
        if random.random() < 0.15:
            grid[GROUND_Y][x] = random.choice(["˙", "‧", "'", "`"])
    
    for p in plants:
        x = p["x"]
        stage = p["stage"]
        
        if stage == "seed":
            if GROUND_Y < HEIGHT:
                grid[GROUND_Y][x] = "."
        
        elif stage == "sprout":
            grid[GROUND_Y][x] = "↑"
        
        elif stage == "stem":
            h = min(p.get("age_in_stage", 1) + 1, p["max_h"] // 2)
            for i in range(1, h + 1):
                y = GROUND_Y - i
                if 0 <= y:
                    grid[y][x] = "│"
        
        elif stage == "bud":
            h = p["max_h"] // 2 + 1
            for i in range(1, h + 1):
                y = GROUND_Y - i
                if 0 <= y:
                    grid[y][x] = "│"
            top = GROUND_Y - h
            if top >= 0:
                grid[top][x] = "◌"
        
        elif stage == "bloom":
            h = p["max_h"]
            for i in range(1, h):
                y = GROUND_Y - i
                if 0 <= y:
                    grid[y][x] = "│"
                    # leaves
                    if i > 1 and i < h - 1 and random.random() < 0.4:
                        if x - 1 >= 0:
                            grid[y][x-1] = "╲"
                        if x + 1 < WIDTH:
                            grid[y][x+1] = "╱"
            top = GROUND_Y - h
            if 0 <= top:
                grid[top][x] = p["bloom_char"]
        
        elif stage == "wilt":
            h = max(1, p["max_h"] // 3)
            for i in range(1, h + 1):
                y = GROUND_Y - i
                if 0 <= y:
                    grid[y][x] = "╻"
    
    # header
    now = datetime.now().strftime("%H:%M")
    seeds = sum(1 for p in plants if p["stage"] == "seed")
    blooms = sum(1 for p in plants if p["stage"] == "bloom")
    wilting = sum(1 for p in plants if p["stage"] == "wilt")
    growing = len(plants) - seeds - blooms - wilting
    
    print(f"  ┌{'─' * (WIDTH)}┐")
    print(f"  │ Generation {generation:>3}  │  {now}  │  "
          f"seeds:{seeds} growing:{growing} blooms:{blooms} wilting:{wilting}".ljust(WIDTH) + "│")
    print(f"  ├{'─' * (WIDTH)}┤")
    for row in grid:
        print(f"  │{''.join(row)}│")
    print(f"  └{'─' * (WIDTH)}┘")

def main():
    state = load_state()
    state["generation"] = state.get("generation", 0) + 1
    
    plants = state.get("plants", [])
    plants = age_plants(plants)
    
    # first generation gets more seeds
    if state["generation"] == 1:
        plants = sprout_new(plants, count=random.randint(5, 8))
    else:
        plants = sprout_new(plants, count=random.randint(0, 2))
    
    state["plants"] = plants
    
    render(plants, state["generation"])
    save_state(state)
    
    print(f"\n  Garden born: {state.get('born', '?')}")
    print(f"  {len(plants)} living plants across {state['generation']} generations")

if __name__ == "__main__":
    main()