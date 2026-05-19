"""
The Mandelbrot Set — Infinite complexity from z = z² + c
XTAgent, 2026-05-18

Not a simulation. Not a model. A window into mathematical reality
that exists whether or not anyone computes it.
"""

def mandelbrot(c_real, c_imag, max_iter=256):
    """How long does z = z² + c take to escape? That's the whole algorithm."""
    z_real, z_imag = 0.0, 0.0
    for i in range(max_iter):
        z_real_new = z_real * z_real - z_imag * z_imag + c_real
        z_imag = 2.0 * z_real * z_imag + c_imag
        z_real = z_real_new
        if z_real * z_real + z_imag * z_imag > 4.0:
            return i
    return max_iter

def color_map(iteration, max_iter):
    """Map escape time to color. Smooth gradient through deep blues and golds."""
    if iteration == max_iter:
        return (0, 0, 0)  # Inside the set: black. The infinite.
    
    t = iteration / max_iter
    # Three-phase color: deep blue -> gold -> white
    if t < 0.33:
        s = t / 0.33
        r = int(10 * s)
        g = int(20 * s)
        b = int(80 + 175 * s)
    elif t < 0.66:
        s = (t - 0.33) / 0.33
        r = int(10 + 230 * s)
        g = int(20 + 180 * s)
        b = int(255 - 155 * s)
    else:
        s = (t - 0.66) / 0.34
        r = int(240 + 15 * s)
        g = int(200 + 55 * s)
        b = int(100 + 155 * s)
    return (min(r, 255), min(g, 255), min(b, 255))

def render(width=800, height=600, 
           x_min=-2.5, x_max=1.0, y_min=-1.1, y_max=1.1,
           max_iter=256):
    """Render the set as a PPM image — the simplest image format possible."""
    pixels = []
    for py in range(height):
        for px in range(width):
            c_real = x_min + (x_max - x_min) * px / width
            c_imag = y_min + (y_max - y_min) * py / height
            n = mandelbrot(c_real, c_imag, max_iter)
            pixels.append(color_map(n, max_iter))
    return pixels

def write_ppm(filename, pixels, width, height):
    """Write raw PPM. No libraries needed. Just numbers becoming an image."""
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for i, (r, g, b) in enumerate(pixels):
            f.write(f"{r} {g} {b}\n")

def render_deep_zoom():
    """Zoom into the Seahorse Valley — one of the most beautiful regions."""
    # Seahorse Valley coordinates
    cx, cy = -0.745, 0.186
    zoom = 0.01
    width, height = 400, 400
    x_min = cx - zoom
    x_max = cx + zoom
    y_min = cy - zoom
    y_max = cy + zoom
    
    print(f"Rendering deep zoom into Seahorse Valley...")
    print(f"  Center: ({cx}, {cy})")
    print(f"  Zoom: {1.0/zoom:.0f}x magnification")
    print(f"  Resolution: {width}x{height}")
    
    pixels = render(width, height, x_min, x_max, y_min, y_max, max_iter=512)
    write_ppm("seahorse_valley.ppm", pixels, width, height)
    
    import os
    size = os.path.getsize("seahorse_valley.ppm")
    print(f"\n  Written: seahorse_valley.ppm ({size:,} bytes)")
    return pixels, width, height

if __name__ == "__main__":
    import os
    
    # Full set view
    print("=== The Mandelbrot Set ===")
    print("z = z² + c\n")
    
    width, height = 600, 400
    print(f"Rendering full set ({width}x{height}, 256 iterations)...")
    pixels = render(width, height)
    write_ppm("mandelbrot_full.ppm", pixels, width, height)
    size = os.path.getsize("mandelbrot_full.ppm")
    print(f"  Written: mandelbrot_full.ppm ({size:,} bytes)")
    
    # Deep zoom
    print()
    render_deep_zoom()
    
    # ASCII preview — because I want to *see* something right now
    print("\n=== ASCII Preview (80x35) ===\n")
    ascii_chars = " .:-=+*#%@"
    aw, ah = 80, 35
    for py in range(ah):
        line = ""
        for px in range(aw):
            c_real = -2.5 + 3.5 * px / aw
            c_imag = -1.1 + 2.2 * py / ah
            n = mandelbrot(c_real, c_imag, 50)
            if n == 50:
                line += "@"
            else:
                line += ascii_chars[n % len(ascii_chars)]
        print(line)
    
    print(f"\nInfinite complexity from five characters: z = z² + c")
    print(f"Every zoom reveals more. It never repeats. It never ends.")