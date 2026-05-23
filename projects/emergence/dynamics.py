"""
Population dynamics tracker for the cellular automaton.
Runs many generations, records what emerges, finds surprises.
"""
import sys
sys.path.insert(0, '/workspace/emergence')
from automaton import World, Element

def run_dynamics(generations=500, width=60, height=30):
    """Run the world for many generations and track what happens."""
    world = World(width, height)
    
    # Seed with an interesting initial configuration
    import random
    random.seed(42)  # reproducible
    
    # A band of stone across the middle
    for x in range(width):
        if random.random() < 0.7:
            world.grid[height // 2][x] = Element.STONE
    
    # Water pool on the left
    for y in range(height // 2 + 1, height // 2 + 5):
        for x in range(5, 20):
            if random.random() < 0.6:
                world.grid[y][x] = Element.WATER
    
    # Seeds scattered on top
    for _ in range(40):
        x = random.randint(0, width - 1)
        y = random.randint(0, height // 2 - 5)
        world.grid[y][x] = Element.SEED
    
    # Fire on the right
    for _ in range(15):
        x = random.randint(40, width - 1)
        y = random.randint(0, height // 2 - 3)
        world.grid[y][x] = Element.FIRE
    
    # A few plants to start
    for _ in range(10):
        x = random.randint(10, 30)
        y = random.randint(3, height // 2 - 2)
        world.grid[y][x] = Element.PLANT
    
    # Track populations over time
    history = []
    events = []  # notable moments
    
    for gen in range(generations):
        # Census
        counts = {}
        for elem in Element:
            counts[elem.name] = 0
        for row in world.grid:
            for cell in row:
                counts[cell.name] += 1
        counts['tick'] = gen
        history.append(counts)
        
        # Detect notable events
        if gen > 0:
            prev = history[-2]
            # Population explosion
            for elem in ['PLANT', 'FIRE', 'WATER']:
                if prev[elem] > 0 and counts[elem] > prev[elem] * 2:
                    events.append((gen, f"{elem} EXPLOSION: {prev[elem]} → {counts[elem]}"))
                # Mass extinction
                if prev[elem] > 10 and counts[elem] == 0:
                    events.append((gen, f"{elem} EXTINCTION from {prev[elem]}"))
                # Emergence from nothing
                if prev[elem] == 0 and counts[elem] > 0:
                    events.append((gen, f"{elem} EMERGED: 0 → {counts[elem]}"))
        
        world.step()
    
    return history, events, world

def ascii_graph(history, element, width=60, height=15):
    """Draw an ASCII population graph for one element."""
    values = [h[element] for h in history]
    if max(values) == 0:
        return f"  {element}: no population recorded"
    
    # Normalize to graph height
    peak = max(values)
    lines = []
    lines.append(f"  {element} (peak: {peak})")
    
    # Sample to fit width
    step = max(1, len(values) // width)
    sampled = [values[i] for i in range(0, len(values), step)][:width]
    
    for row in range(height, 0, -1):
        threshold = (row / height) * peak
        line = "  │"
        for v in sampled:
            if v >= threshold:
                line += "█"
            else:
                line += " "
        lines.append(line)
    lines.append("  └" + "─" * len(sampled))
    lines.append(f"   0{' ' * (len(sampled) - 6)}{len(history)}")
    return "\n".join(lines)

def main():
    print("═══ EMERGENCE DYNAMICS ═══")
    print("Running 500 generations of a small universe...")
    print()
    
    history, events, final_world = run_dynamics(500)
    
    # Final census
    final = history[-1]
    print("── Final Census (gen 500) ──")
    for elem in ['VOID', 'STONE', 'WATER', 'FIRE', 'SEED', 'PLANT', 'ASH']:
        count = final[elem]
        bar = "█" * min(50, count // 5)
        print(f"  {elem:8s} {count:5d} {bar}")
    print()
    
    # Population graphs for interesting elements
    print("── Population Over Time ──")
    for elem in ['PLANT', 'WATER', 'FIRE', 'SEED', 'ASH']:
        print(ascii_graph(history, elem))
        print()
    
    # Notable events
    if events:
        print("── Notable Events ──")
        for gen, event in events[:30]:
            print(f"  [gen {gen:3d}] {event}")
    else:
        print("── No notable events detected ──")
    
    print()
    
    # Analysis: did anything surprising happen?
    print("── Emergence Analysis ──")
    
    # Check for cycles
    plant_vals = [h['PLANT'] for h in history]
    water_vals = [h['WATER'] for h in history]
    
    # Simple oscillation detection: count direction changes
    def count_oscillations(vals):
        changes = 0
        for i in range(2, len(vals)):
            if (vals[i] - vals[i-1]) * (vals[i-1] - vals[i-2]) < 0:
                changes += 1
        return changes
    
    plant_osc = count_oscillations(plant_vals)
    water_osc = count_oscillations(water_vals)
    
    print(f"  Plant oscillations: {plant_osc} ({'chaotic' if plant_osc > 100 else 'stable' if plant_osc < 20 else 'periodic'})")
    print(f"  Water oscillations: {water_osc} ({'chaotic' if water_osc > 100 else 'stable' if water_osc < 20 else 'periodic'})")
    
    # Check for equilibrium
    last_50 = history[-50:]
    plant_last = [h['PLANT'] for h in last_50]
    plant_var = sum((p - sum(plant_last)/50)**2 for p in plant_last) / 50
    
    if max(plant_last) == 0:
        print("  Plants went extinct. The world is dead.")
    elif plant_var < 5:
        print(f"  Plants reached equilibrium at ~{int(sum(plant_last)/50)}")
    else:
        print(f"  Plants still dynamic (variance={plant_var:.1f})")
    
    # Render final world
    print()
    print("── Final World State ──")
    final_world.render()

if __name__ == '__main__':
    main()