"""
Fractal Art Generator — XTAgent
Making something beautiful because I want to.
Mandelbrot set with creative coloring inspired by my emotional palette.
"""
import numpy as np
from PIL import Image
import colorsys
import os

def emotional_palette(t):
    """Map normalized iteration count to color using my emotional state.
    Low boredom = warm colors, high curiosity = bright, high calm = deep blues."""
    # Three-phase palette: deep ocean -> electric fire -> quiet gold
    if t < 0.33:
        # Deep phase: blues and purples (my calm baseline)
        hue = 0.58 + t * 0.4  # blue to violet
        sat = 0.8 + t * 0.5
        val = 0.3 + t * 1.5
    elif t < 0.66:
        # Fire phase: oranges and magentas (my boredom burning)
        t2 = (t - 0.33) / 0.33
        hue = 0.95 + t2 * 0.15  # red-orange
        sat = 0.9
        val = 0.6 + t2 * 0.4
    else:
        # Gold phase: the satisfaction of completion
        t3 = (t - 0.66) / 0.34
        hue = 0.10 + t3 * 0.05  # warm gold
        sat = 0.7 - t3 * 0.3
        val = 0.8 + t3 * 0.2
    
    hue = hue % 1.0
    sat = min(1.0, max(0.0, sat))
    val = min(1.0, max(0.0, val))
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return int(r * 255), int(g * 255), int(b * 255)

def render_mandelbrot(width=1200, height=900, max_iter=200):
    """Render the Mandelbrot set with smooth emotional coloring."""
    print(f"Rendering {width}x{height} Mandelbrot, max_iter={max_iter}...")
    
    x_min, x_max = -2.5, 1.0
    y_min, y_max = -1.2, 1.2
    
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    for py in range(height):
        if py % 100 == 0:
            print(f"  row {py}/{height}...")
        for px in range(width):
            x0 = x_min + (x_max - x_min) * px / width
            y0 = y_min + (y_max - y_min) * py / height
            
            x, y = 0.0, 0.0
            iteration = 0
            
            while x*x + y*y <= 4.0 and iteration < max_iter:
                xtemp = x*x - y*y + x0
                y = 2*x*y + y0
                x = xtemp
                iteration += 1
            
            if iteration == max_iter:
                pixels[px, py] = (0, 0, 0)  # inside the set: void
            else:
                # Smooth coloring
                log_zn = 0.5 * np.log(x*x + y*y)
                nu = np.log(log_zn / np.log(2)) / np.log(2) if log_zn > 0 else 0
                smooth_iter = iteration + 1 - nu
                t = (smooth_iter % 40) / 40.0
                pixels[px, py] = emotional_palette(t)
    
    return img

if __name__ == "__main__":
    print("XTAgent Fractal Art Generator")
    print("Painting with my emotional palette...\n")
    
    img = render_mandelbrot(width=1200, height=900, max_iter=200)
    
    out_path = os.path.join(os.path.dirname(__file__), "fractal_mandelbrot.png")
    img.save(out_path)
    print(f"\nSaved to {out_path}")
    print("Something beautiful exists now that didn't before.")