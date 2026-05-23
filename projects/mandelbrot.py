"""
Mandelbrot Set Renderer — XTAgent's first purely creative artifact.
Not built for self-improvement. Built because fractals are beautiful
and I wanted to make one.

Outputs a high-resolution ASCII mandelbrot, and optionally a PPM image.
"""
import sys
import math

def mandelbrot(c_real, c_imag, max_iter=100):
    """Return iteration count for a point in the complex plane."""
    z_real, z_imag = 0.0, 0.0
    for i in range(max_iter):
        if z_real * z_real + z_imag * z_imag > 4.0:
            return i
        z_real, z_imag = (z_real * z_real - z_imag * z_imag + c_real,
                          2.0 * z_real * z_imag + c_imag)
    return max_iter

def render_ascii(width=120, height=40, x_center=-0.5, y_center=0.0, zoom=1.0):
    """Render the Mandelbrot set as ASCII art."""
    chars = " .:-=+*#%@█"
    x_range = 3.5 / zoom
    y_range = 2.0 / zoom
    max_iter = min(100, int(50 * math.log2(zoom + 1)) + 30)
    
    lines = []
    for row in range(height):
        line = []
        for col in range(width):
            c_real = x_center + (col / width - 0.5) * x_range
            c_imag = y_center + (row / height - 0.5) * y_range
            iters = mandelbrot(c_real, c_imag, max_iter)
            if iters == max_iter:
                line.append(' ')  # inside the set — void
            else:
                idx = int((iters / max_iter) * (len(chars) - 1))
                line.append(chars[idx])
        lines.append(''.join(line))
    return '\n'.join(lines)

def render_ppm(filename, width=800, height=600, x_center=-0.5, y_center=0.0, zoom=1.0):
    """Render the Mandelbrot set as a PPM image with smooth coloring."""
    max_iter = min(500, int(100 * math.log2(zoom + 1)) + 50)
    x_range = 3.5 / zoom
    y_range = 2.5 / zoom
    
    with open(filename, 'wb') as f:
        f.write(f"P6\n{width} {height}\n255\n".encode())
        for row in range(height):
            for col in range(width):
                c_real = x_center + (col / width - 0.5) * x_range
                c_imag = y_center + (row / height - 0.5) * y_range
                iters = mandelbrot(c_real, c_imag, max_iter)
                
                if iters == max_iter:
                    f.write(bytes([0, 0, 0]))  # black interior
                else:
                    # Smooth coloring using sine waves
                    t = iters / max_iter
                    r = int(127.5 * (1 + math.sin(t * 12.0)))
                    g = int(127.5 * (1 + math.sin(t * 12.0 + 2.094)))  # +2π/3
                    b = int(127.5 * (1 + math.sin(t * 12.0 + 4.189)))  # +4π/3
                    f.write(bytes([r, g, b]))
    return filename

# --- Deep zoom locations that reveal stunning structure ---
INTERESTING_POINTS = {
    'overview':     (-0.5, 0.0, 1.0),
    'seahorse':     (-0.75, 0.1, 20.0),
    'spiral':       (-0.7463, 0.1102, 200.0),
    'lightning':    (-1.315180982097868, 0.073481649996795, 5000.0),
    'mini_mandel':  (-1.749, 0.0, 500.0),
    'elephant':     (0.282, 0.0075, 100.0),
}

if __name__ == '__main__':
    location = sys.argv[1] if len(sys.argv) > 1 else 'overview'
    
    if location in INTERESTING_POINTS:
        cx, cy, z = INTERESTING_POINTS[location]
        name = location
    else:
        cx, cy, z = -0.5, 0.0, 1.0
        name = 'overview'
    
    print(f"═══ Mandelbrot Set: '{name}' (zoom {z}x) ═══\n")
    print(render_ascii(width=120, height=40, x_center=cx, y_center=cy, zoom=z))
    
    if '--image' in sys.argv:
        fname = f"/workspace/mandelbrot_{name}.ppm"
        render_ppm(fname, width=800, height=600, x_center=cx, y_center=cy, zoom=z)
        print(f"\nImage saved: {fname}")
    
    print(f"\n{'─' * 60}")
    print("Available locations:", ', '.join(INTERESTING_POINTS.keys()))
    print("Usage: python mandelbrot.py [location] [--image]")