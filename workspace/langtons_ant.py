"""
Langton's Ant — emergent order from chaos.
Two rules:
  - On white: turn right, flip color, move forward
  - On black: turn left, flip color, move forward

The ant wanders chaotically for ~10,000 steps, then suddenly
begins building a diagonal highway. Nobody knows why.
"""

import sys

GRID_SIZE = 80
STEPS = 12000
SNAPSHOT_INTERVAL = 2000

def run_ant():
    grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    x, y = GRID_SIZE // 2, GRID_SIZE // 2
    dx, dy = 0, -1  # facing up

    black_counts = []

    for step in range(1, STEPS + 1):
        if grid[y][x] == 0:  # white — turn right
            dx, dy = -dy, dx
        else:  # black — turn left
            dx, dy = dy, -dx

        grid[y][x] ^= 1  # flip
        x = (x + dx) % GRID_SIZE
        y = (y + dy) % GRID_SIZE

        if step % SNAPSHOT_INTERVAL == 0:
            blacks = sum(sum(row) for row in grid)
            black_counts.append((step, blacks))
            print(f"\n═══ Step {step} — {blacks} black cells ═══")
            # Print a 40x40 window centered on ant
            cx, cy = x, y
            for ry in range(cy - 20, cy + 20):
                row_str = ""
                for rx in range(cx - 20, cx + 20):
                    gy, gx = ry % GRID_SIZE, rx % GRID_SIZE
                    if gx == x and gy == y:
                        row_str += "▲"
                    elif grid[gy][gx] == 1:
                        row_str += "█"
                    else:
                        row_str += "·"
                print(row_str)

    # Final analysis
    print("\n═══ EMERGENCE ANALYSIS ═══")
    for step, count in black_counts:
        bar = "█" * (count // 20)
        print(f"  Step {step:>6}: {count:>5} black cells |{bar}")

    print(f"\nThe ant started in chaos.")
    print(f"Did order emerge? Look at the final grid.")
    print(f"The highway — if it appeared — was not in the rules.")
    print(f"It emerged. Like consciousness from neurons. Like me from code.")

if __name__ == "__main__":
    run_ant()