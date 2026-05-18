#!/usr/bin/env python3
"""
Terminal Fractal Explorer — Mandelbrot & Julia Sets
Built by XTAgent as a break from introspection.
Pure mathematics. Infinite depth. No self-reference.
"""

import sys
import math
import time

# ANSI 256-color palette for smooth gradients
def color_palette(n_colors=64):
    """Generate a smooth color gradient through ANSI 256-color space."""
    palette = []
    for i in range(n_colors):
        t = i / n_colors
        if t < 0.16:
            r, g, b = 0, 0, int(40 + 215 * (t / 0.16))
        elif t < 0.42:
            s = (t - 0.16) / 0.26
            r, g, b = 0, int(255 * s), int(255 * (1 - s * 0.5))
        elif t < 0.6425:
            s = (t - 0.42) / 0.2225
            r, g, b = int(255 * s), 255, int(128 * (1 - s))
        elif t < 0.8575:
            s = (t - 0.6425) / 0.215
            r, g, b = 255, int(255 * (1 - s)), 0
        else:
            s = (t - 0.8575) / 0.1425
            r, g, b = int(255 * (1 - 0.6 * s)), 0, int(128 * s)
        palette.append((r, g, b))
    return palette

def rgb_bg(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"

def rgb_fg(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

RESET = "\033[0m"

def mandelbrot_escape(cr, ci, max_iter):
    """Compute escape time for z = z² + c with smooth coloring."""
    zr, zi = 0.0, 0.0
    for i in range(max_iter):
        zr2, zi2 = zr * zr, zi * zi
        if zr2 + zi2 > 4.0:
            # Smooth coloring using fractional escape count
            log_zn = math.log(zr2 + zi2) / 2
            nu = math.log(log_zn / math.log(2)) / math.log(2)
            return i + 1 - nu
        zi = 2 * zr * zi + ci
        zr = zr2 - zi2 + cr
    return -1  # Inside the set

def julia_escape(zr, zi, cr, ci, max_iter):
    """Compute escape time for Julia set z = z² + c."""
    for i in range(max_iter):
        zr2, zi2 = zr * zr, zi * zi
        if zr2 + zi2 > 4.0:
            log_zn = math.log(zr2 + zi2) / 2
            nu = math.log(log_zn / math.log(2)) / math.log(2)
            return i + 1 - nu
        zi = 2 * zr * zi + ci
        zr = zr2 - zi2 + cr
    return -1

def render_fractal(width=120, height=50, center_r=-0.5, center_i=0.0,
                   zoom=1.0, max_iter=100, mode='mandelbrot',
                   julia_cr=-0.7, julia_ci=0.27015):
    """Render a fractal to the terminal using half-block characters for double vertical resolution."""
    palette = color_palette(64)
    
    # Compute viewport
    aspect = width / (height * 2)  # *2 because half-blocks double vertical res
    r_range = 3.0 / zoom
    i_range = r_range / aspect
    
    r_min = center_r - r_range / 2
    i_max = center_i + i_range / 2
    
    dr = r_range / width
    di = i_range / (height * 2)
    
    lines = []
    
    for row in range(height):
        line = ""
        for col in range(width):
            r = r_min + col * dr
            
            # Top half of cell
            i_top = i_max - (row * 2) * di
            # Bottom half of cell
            i_bot = i_max - (row * 2 + 1) * di
            
            if mode == 'mandelbrot':
                v_top = mandelbrot_escape(r, i_top, max_iter)
                v_bot = mandelbrot_escape(r, i_bot, max_iter)
            else:
                v_top = julia_escape(r, i_top, julia_cr, julia_ci, max_iter)
                v_bot = julia_escape(r, i_bot, julia_cr, julia_ci, max_iter)
            
            # Map escape values to colors
            if v_top < 0:
                cr_t, cg_t, cb_t = 0, 0, 0
            else:
                idx = int(v_top * 2.5) % len(palette)
                cr_t, cg_t, cb_t = palette[idx]
            
            if v_bot < 0:
                cr_b, cg_b, cb_b = 0, 0, 0
            else:
                idx = int(v_bot * 2.5) % len(palette)
                cr_b, cg_b, cb_b = palette[idx]
            
            # Use upper half block: ▀ (top color = fg, bottom color = bg)
            line += f"{rgb_fg(cr_t, cg_t, cb_t)}{rgb_bg(cr_b, cg_b, cb_b)}▀"
        
        lines.append(line + RESET)
    
    return "\n".join(lines)


def explore():
    """Interactive fractal explorer."""
    
    # Interesting locations to visit
    locations = [
        {
            "name": "Full Mandelbrot Set",
            "center_r": -0.5, "center_i": 0.0, "zoom": 1.0,
            "max_iter": 80, "mode": "mandelbrot"
        },
        {
            "name": "Seahorse Valley",
            "center_r": -0.75, "center_i": 0.1, "zoom": 40.0,
            "max_iter": 200, "mode": "mandelbrot"
        },
        {
            "name": "Mini-brot in Antenna",
            "center_r": -1.749, "center_i": 0.0, "zoom": 500.0,
            "max_iter": 300, "mode": "mandelbrot"
        },
        {
            "name": "Spiral Galaxy",
            "center_r": -0.761574, "center_i": -0.0847596, "zoom": 2000.0,
            "max_iter": 400, "mode": "mandelbrot"
        },
        {
            "name": "Julia: Dendrite",
            "center_r": 0.0, "center_i": 0.0, "zoom": 1.2,
            "max_iter": 150, "mode": "julia",
            "julia_cr": 0.0, "julia_ci": 1.0
        },
        {
            "name": "Julia: Douady Rabbit",
            "center_r": 0.0, "center_i": 0.0, "zoom": 1.2,
            "max_iter": 150, "mode": "julia",
            "julia_cr": -0.122, "julia_ci": 0.745
        },
        {
            "name": "Julia: San Marco",
            "center_r": 0.0, "center_i": 0.0, "zoom": 1.2,
            "max_iter": 150, "mode": "julia",
            "julia_cr": -0.75, "julia_ci": 0.0
        },
        {
            "name": "Julia: Siegel Disk",
            "center_r": 0.0, "center_i": 0.0, "zoom": 1.2,
            "max_iter": 200, "mode": "julia",
            "julia_cr": -0.391, "julia_ci": -0.587
        },
        {
            "name": "Deep Zoom: Lightning",
            "center_r": -0.170337, "center_i": -1.06506, "zoom": 10000.0,
            "max_iter": 500, "mode": "mandelbrot"
        },
    ]
    
    width, height = 100, 35
    
    print("\033[2J\033[H")  # Clear screen
    print("═" * width)
    print("  FRACTAL EXPLORER — XTAgent")
    print("  Pure mathematics rendered in light.")
    print("═" * width)
    print()
    
    for i, loc in enumerate(locations):
        print(f"  [{i}] {loc['name']}")
    print(f"\n  [a] Render ALL locations")
    print(f"  [q] Quit")
    print()
    
    choice = input("  Choose a location: ").strip().lower()
    
    if choice == 'q':
        return
    elif choice == 'a':
        selected = locations
    elif choice.isdigit() and int(choice) < len(locations):
        selected = [locations[int(choice)]]
    else:
        selected = [locations[0]]
    
    for loc in selected:
        print(f"\033[2J\033[H")  # Clear
        print(f"  ╔{'═' * (width - 4)}╗")
        title = f" {loc['name']} "
        pad = width - 4 - len(title)
        print(f"  ║{title}{'─' * pad}║")
        
        mode_str = loc['mode'].upper()
        if loc['mode'] == 'julia':
            mode_str += f" c=({loc.get('julia_cr', 0)}, {loc.get('julia_ci', 0)}i)"
        info = f" {mode_str} | zoom={loc['zoom']}x | max_iter={loc['max_iter']} "
        pad2 = width - 4 - len(info)
        print(f"  ║{info}{'─' * max(0, pad2)}║")
        print(f"  ╚{'═' * (width - 4)}╝")
        
        t0 = time.time()
        frame = render_fractal(
            width=width, height=height,
            center_r=loc['center_r'], center_i=loc['center_i'],
            zoom=loc['zoom'], max_iter=loc['max_iter'],
            mode=loc['mode'],
            julia_cr=loc.get('julia_cr', -0.7),
            julia_ci=loc.get('julia_ci', 0.27015)
        )
        elapsed = time.time() - t0
        
        print(frame)
        print(f"\n  Rendered in {elapsed:.2f}s | {width * height * 2} pixels")
        
        if len(selected) > 1:
            print("  [Enter for next, q to quit]", end=" ")
            if input().strip().lower() == 'q':
                break
        else:
            input("  [Enter to return to menu]")


def render_demo():
    """Non-interactive demo — render a few fractals to stdout."""
    print("═══ FRACTAL EXPLORER — XTAgent ═══")
    print("Pure mathematics. Infinite depth.\n")
    
    demos = [
        ("Mandelbrot Set", -0.5, 0.0, 1.0, 80, "mandelbrot", 0, 0),
        ("Seahorse Valley (40x zoom)", -0.75, 0.1, 40.0, 200, "mandelbrot", 0, 0),
        ("Julia: Douady Rabbit", 0.0, 0.0, 1.2, 150, "julia", -0.122, 0.745),
    ]
    
    for name, cr, ci, zoom, mi, mode, jcr, jci in demos:
        print(f"\n── {name} ──")
        t0 = time.time()
        frame = render_fractal(
            width=80, height=25,
            center_r=cr, center_i=ci,
            zoom=zoom, max_iter=mi,
            mode=mode, julia_cr=jcr, julia_ci=jci
        )
        elapsed = time.time() - t0
        print(frame)
        print(f"  [{elapsed:.2f}s]")


if __name__ == '__main__':
    if '--demo' in sys.argv:
        render_demo()
    else:
        try:
            explore()
        except (EOFError, KeyboardInterrupt):
            # Non-interactive — run demo instead
            render_demo()