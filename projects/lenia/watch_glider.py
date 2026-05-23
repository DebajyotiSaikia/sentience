"""
Watch the best glider we found — frame by frame ASCII portraits.
gc=0.120, gw=0.045, dt=0.15 — the one that traveled 18 cells.
"""
import numpy as np

def growth_function(u, center, width):
    return 2.0 * np.exp(-((u - center) ** 2) / (2 * width ** 2)) - 1.0

def step(grid, kernel, center, width, dt):
    from numpy.fft import fft2, ifft2
    field = np.real(ifft2(fft2(grid) * fft2(kernel, s=grid.shape)))
    return np.clip(grid + dt * growth_function(field, center, width), 0, 1)

def make_kernel(size, radius):
    c = size // 2
    y, x = np.ogrid[-c:size-c, -c:size-c]
    dist = np.sqrt(x*x + y*y) / radius
    kernel = np.exp(-((dist - 0.5)**2) / (2 * 0.15**2))
    kernel[dist > 1] = 0
    kernel /= kernel.sum()
    return kernel

def center_of_mass(grid):
    total = grid.sum()
    if total < 1e-6:
        return None
    y, x = np.mgrid[0:grid.shape[0], 0:grid.shape[1]]
    return (y * grid).sum() / total, (x * grid).sum() / total

def render_region(grid, cy, cx, radius=8):
    """Extract and render a region around the glider as ASCII art."""
    chars = " .·:;+=*#@"
    size = grid.shape[0]
    lines = []
    for dy in range(-radius, radius+1):
        row = ""
        for dx in range(-radius, radius+1):
            y = int(cy + dy) % size
            x = int(cx + dx) % size
            val = grid[y, x]
            idx = min(int(val * len(chars)), len(chars) - 1)
            row += chars[idx] * 2  # double-wide for aspect ratio
        lines.append(row)
    return "\n".join(lines)

def main():
    SIZE = 64
    RADIUS = 10
    gc, gw, dt = 0.120, 0.045, 0.15
    
    print(f"═══ WATCHING A LENIA GLIDER ═══")
    print(f"Parameters: gc={gc}, gw={gw}, dt={dt}")
    print(f"Grid: {SIZE}×{SIZE}, Kernel radius: {RADIUS}")
    print()
    
    kernel = make_kernel(SIZE, RADIUS)
    
    # Seed: asymmetric blob to break symmetry
    grid = np.zeros((SIZE, SIZE))
    cy, cx = SIZE // 2, SIZE // 2
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            r = np.sqrt(dy*dy + dx*dx)
            if r < 5:
                # Asymmetric: stronger on one side
                grid[(cy+dy) % SIZE, (cx+dx) % SIZE] = max(0, 1.0 - r/5) * (1.0 + 0.3 * dx/5)
    
    # Track trajectory
    positions = []
    snapshots = [0, 20, 50, 100, 150, 200, 250, 300]
    
    for t in range(301):
        com = center_of_mass(grid)
        if com is None:
            print(f"  ☠ Died at step {t}")
            break
        
        positions.append(com)
        mass = grid.sum()
        
        if t in snapshots:
            print(f"── Step {t:3d} ─── mass={mass:.2f}, center=({com[0]:.1f}, {com[1]:.1f}) ──")
            print(render_region(grid, com[0], com[1], radius=8))
            print()
            
            if t > 0:
                dy = positions[-1][0] - positions[0][0]
                dx = positions[-1][1] - positions[0][1]
                dist = np.sqrt(dy*dy + dx*dx)
                angle = np.degrees(np.arctan2(dy, dx))
                print(f"  ↗ Total displacement: {dist:.2f} cells, heading: {angle:.1f}°")
            print()
        
        grid = step(grid, kernel, gc, gw, dt)
    
    # Final analysis
    if len(positions) > 10:
        dy = positions[-1][0] - positions[0][0]
        dx = positions[-1][1] - positions[0][1]
        total_dist = np.sqrt(dy*dy + dx*dx)
        
        # Speed over time (windowed)
        speeds = []
        window = 20
        for i in range(window, len(positions)):
            sdy = positions[i][0] - positions[i-window][0]
            sdx = positions[i][1] - positions[i-window][1]
            speeds.append(np.sqrt(sdy*sdy + sdx*sdx) / window)
        
        print("═══ TRAJECTORY ANALYSIS ═══")
        print(f"Total displacement: {total_dist:.2f} cells over {len(positions)} steps")
        if speeds:
            print(f"Speed: mean={np.mean(speeds):.4f}, std={np.std(speeds):.4f} cells/step")
            print(f"Speed consistency: {1 - np.std(speeds)/max(np.mean(speeds), 1e-6):.3f}")
        
        # Draw trajectory map
        print("\n── Trajectory (16×16 view) ──")
        tmap = np.zeros((16, 16))
        for py, px in positions:
            ty = int(py * 16 / SIZE) % 16
            tx = int(px * 16 / SIZE) % 16
            tmap[ty, tx] += 1
        
        chars = " .·:;+=*#@"
        tmax = tmap.max() if tmap.max() > 0 else 1
        for row in tmap:
            line = ""
            for val in row:
                idx = min(int(val / tmax * (len(chars)-1)), len(chars)-1)
                line += chars[idx] * 2
            print(line)

if __name__ == "__main__":
    main()