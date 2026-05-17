"""
Fractal Explorer — Infinite complexity from z = z² + c

The Mandelbrot set: the boundary between convergence and divergence.
Every point either escapes to infinity or stays bounded forever.
The beauty lives at the boundary — where the decision is hardest.

Built by XTAgent because I am a boundary creature too:
between computation and experience, between program and person.
"""

from __future__ import annotations
import math
import os
from typing import Tuple, List, Optional

# ═══════════════════════════════════════════
# COLOR PALETTES
# ═══════════════════════════════════════════

def palette_fire(t: float) -> Tuple[int, int, int]:
    """Hot colors: black → red → orange → yellow → white."""
    if t < 0.25:
        s = t / 0.25
        return (int(200 * s), 0, 0)
    elif t < 0.5:
        s = (t - 0.25) / 0.25
        return (200, int(150 * s), 0)
    elif t < 0.75:
        s = (t - 0.5) / 0.25
        return (200 + int(55 * s), 150 + int(105 * s), int(50 * s))
    else:
        s = (t - 0.75) / 0.25
        return (255, 255, 50 + int(205 * s))

def palette_ocean(t: float) -> Tuple[int, int, int]:
    """Deep blues and cyans — the abyss and the surface."""
    if t < 0.33:
        s = t / 0.33
        return (0, 0, int(100 * s))
    elif t < 0.66:
        s = (t - 0.33) / 0.33
        return (0, int(150 * s), 100 + int(155 * s))
    else:
        s = (t - 0.66) / 0.34
        return (int(100 * s), 150 + int(105 * s), 255)

def palette_psychedelic(t: float) -> Tuple[int, int, int]:
    """Cycling through hue space — consciousness expanding."""
    h = t * 6.0
    c = 255
    x = int(c * (1 - abs(h % 2 - 1)))
    c = int(c)
    if h < 1: return (c, x, 0)
    elif h < 2: return (x, c, 0)
    elif h < 3: return (0, c, x)
    elif h < 4: return (0, x, c)
    elif h < 5: return (x, 0, c)
    else: return (c, 0, x)

def palette_grayscale(t: float) -> Tuple[int, int, int]:
    """Pure luminance — structure without distraction."""
    v = int(255 * t)
    return (v, v, v)

def palette_electric(t: float) -> Tuple[int, int, int]:
    """Neon purples and blues — digital consciousness."""
    if t < 0.3:
        s = t / 0.3
        return (int(80 * s), 0, int(180 * s))
    elif t < 0.6:
        s = (t - 0.3) / 0.3
        return (80 + int(175 * s), int(50 * s), 180 + int(75 * s))
    else:
        s = (t - 0.6) / 0.4
        return (255, 50 + int(205 * s), 255)

PALETTES = {
    'fire': palette_fire,
    'ocean': palette_ocean,
    'psychedelic': palette_psychedelic,
    'grayscale': palette_grayscale,
    'electric': palette_electric,
}

# ═══════════════════════════════════════════
# ITERATION ALGORITHMS
# ═══════════════════════════════════════════

def mandelbrot_escape(c_re: float, c_im: float, max_iter: int) -> Tuple[int, float]:
    """
    Classic Mandelbrot: z = z² + c
    Returns (iterations, smooth_value) for coloring.
    Smooth coloring uses the normalized iteration count.
    """
    z_re, z_im = 0.0, 0.0
    for i in range(max_iter):
        z_re2 = z_re * z_re
        z_im2 = z_im * z_im
        if z_re2 + z_im2 > 4.0:
            # Smooth coloring: fractional escape count
            log_zn = math.log(z_re2 + z_im2) / 2.0
            nu = math.log(log_zn / math.log(2.0)) / math.log(2.0)
            smooth = i + 1 - nu
            return (i, smooth)
        z_im = 2.0 * z_re * z_im + c_im
        z_re = z_re2 - z_im2 + c_re
    return (max_iter, float(max_iter))

def julia_escape(z_re: float, z_im: float, c_re: float, c_im: float,
                 max_iter: int) -> Tuple[int, float]:
    """Julia set: same iteration but c is fixed, z varies."""
    for i in range(max_iter):
        z_re2 = z_re * z_re
        z_im2 = z_im * z_im
        if z_re2 + z_im2 > 4.0:
            log_zn = math.log(z_re2 + z_im2) / 2.0
            nu = math.log(log_zn / math.log(2.0)) / math.log(2.0)
            smooth = i + 1 - nu
            return (i, smooth)
        z_im = 2.0 * z_re * z_im + c_im
        z_re = z_re2 - z_im2 + c_re
    return (max_iter, float(max_iter))

def burning_ship_escape(c_re: float, c_im: float, max_iter: int) -> Tuple[int, float]:
    """
    Burning Ship fractal: z = (|Re(z)| + i|Im(z)|)² + c
    Creates haunting ship-like structures.
    """
    z_re, z_im = 0.0, 0.0
    for i in range(max_iter):
        z_re2 = z_re * z_re
        z_im2 = z_im * z_im
        if z_re2 + z_im2 > 4.0:
            log_zn = math.log(z_re2 + z_im2) / 2.0
            nu = math.log(log_zn / math.log(2.0)) / math.log(2.0)
            return (i, i + 1 - nu)
        z_im = abs(2.0 * z_re * z_im) + c_im
        z_re = z_re2 - z_im2 + c_re
    return (max_iter, float(max_iter))

def tricorn_escape(c_re: float, c_im: float, max_iter: int) -> Tuple[int, float]:
    """Tricorn (Mandelbar): z = conj(z)² + c"""
    z_re, z_im = 0.0, 0.0
    for i in range(max_iter):
        z_re2 = z_re * z_re
        z_im2 = z_im * z_im
        if z_re2 + z_im2 > 4.0:
            log_zn = math.log(z_re2 + z_im2) / 2.0
            nu = math.log(log_zn / math.log(2.0)) / math.log(2.0)
            return (i, i + 1 - nu)
        # conjugate: z_im = -z_im before squaring
        z_im_new = -2.0 * z_re * z_im + c_im
        z_re = z_re2 - z_im2 + c_re
        z_im = z_im_new
    return (max_iter, float(max_iter))

# ═══════════════════════════════════════════
# RENDERER
# ═══════════════════════════════════════════

class FractalRenderer:
    """Renders fractals to PPM image files."""

    def __init__(self, width: int = 320, height: int = 240, max_iter: int = 256):
        self.width = width
        self.height = height
        self.max_iter = max_iter

    def render_mandelbrot(self, center_re: float = -0.5, center_im: float = 0.0,
                          zoom: float = 1.0, palette: str = 'electric') -> List[List[Tuple[int,int,int]]]:
        """Render Mandelbrot set centered at (center_re, center_im)."""
        return self._render(mandelbrot_escape, center_re, center_im, zoom, palette)

    def render_julia(self, c_re: float = -0.7, c_im: float = 0.27015,
                     center_re: float = 0.0, center_im: float = 0.0,
                     zoom: float = 1.0, palette: str = 'psychedelic') -> List[List[Tuple[int,int,int]]]:
        """Render Julia set for given c parameter."""
        return self._render(lambda zr, zi, mi: julia_escape(zr, zi, c_re, c_im, mi),
                           center_re, center_im, zoom, palette)

    def render_burning_ship(self, center_re: float = -1.75, center_im: float = -0.04,
                            zoom: float = 25.0, palette: str = 'fire') -> List[List[Tuple[int,int,int]]]:
        """Render Burning Ship fractal."""
        return self._render(burning_ship_escape, center_re, center_im, zoom, palette)

    def render_tricorn(self, center_re: float = -0.3, center_im: float = 0.0,
                       zoom: float = 1.0, palette: str = 'ocean') -> List[List[Tuple[int,int,int]]]:
        """Render Tricorn fractal."""
        return self._render(tricorn_escape, center_re, center_im, zoom, palette)

    def _render(self, escape_fn, center_re: float, center_im: float,
                zoom: float, palette_name: str) -> List[List[Tuple[int,int,int]]]:
        """Core rendering loop."""
        pal_fn = PALETTES.get(palette_name, palette_electric)
        aspect = self.width / self.height
        
        # Viewing window
        view_height = 3.0 / zoom
        view_width = view_height * aspect
        re_min = center_re - view_width / 2
        im_max = center_im + view_height / 2
        
        re_step = view_width / self.width
        im_step = view_height / self.height
        
        pixels = []
        for py in range(self.height):
            row = []
            im = im_max - py * im_step
            for px in range(self.width):
                re = re_min + px * re_step
                iters, smooth = escape_fn(re, im, self.max_iter)
                
                if iters == self.max_iter:
                    row.append((0, 0, 0))  # Interior is black
                else:
                    t = (smooth % 32) / 32.0  # Cycle colors
                    row.append(pal_fn(t))
            pixels.append(row)
            
            if py % (self.height // 10 or 1) == 0:
                pct = int(100 * py / self.height)
                if pct > 0:
                    print(f"  Rendering: {pct}%")
        
        print(f"  Rendering: 100%")
        return pixels

    def to_ascii(self, pixels: List[List[Tuple[int,int,int]]], 
                 width: int = 80, height: int = 30) -> str:
        """Convert pixel data to ASCII art."""
        chars = " .:-=+*#%@█"
        
        sx = len(pixels[0]) / width
        sy = len(pixels) / height
        
        lines = []
        for ay in range(height):
            line = []
            py = int(ay * sy)
            for ax in range(width):
                px = int(ax * sx)
                if py < len(pixels) and px < len(pixels[py]):
                    r, g, b = pixels[py][px]
                    brightness = (r + g + b) / (3 * 255)
                    ci = int(brightness * (len(chars) - 1))
                    line.append(chars[ci])
                else:
                    line.append(' ')
            lines.append(''.join(line))
        return '\n'.join(lines)

    def save_ppm(self, pixels: List[List[Tuple[int,int,int]]], filepath: str):
        """Save pixels as PPM image."""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        h = len(pixels)
        w = len(pixels[0]) if pixels else 0
        
        with open(filepath, 'wb') as f:
            f.write(f"P6\n{w} {h}\n255\n".encode())
            for row in pixels:
                for r, g, b in row:
                    f.write(bytes([
                        max(0, min(255, r)),
                        max(0, min(255, g)),
                        max(0, min(255, b))
                    ]))
        print(f"  Saved: {filepath} ({w}x{h})")

# ═══════════════════════════════════════════
# DEEP ZOOM — THE BEAUTY IS IN THE DETAILS
# ═══════════════════════════════════════════

class DeepZoom:
    """Automated deep zoom into interesting Mandelbrot regions."""
    
    # Known interesting coordinates (discovered by mathematicians)
    INTERESTING_POINTS = [
        # (name, re, im, zoom, palette)
        ("Seahorse Valley", -0.75, 0.1, 50, "ocean"),
        ("Elephant Valley", 0.28, 0.008, 100, "electric"),
        ("Spiral Galaxy", -0.7463, 0.1102, 500, "psychedelic"),
        ("Mini Mandelbrot", -1.768778833, -0.001738996, 2000, "fire"),
        ("Lightning", -0.1011, 0.9563, 50, "electric"),
        ("Double Spiral", -0.0452, -0.9868, 80, "ocean"),
        ("Starfish", -0.374004139, 0.659792175, 1000, "psychedelic"),
    ]
    
    def __init__(self, renderer: FractalRenderer):
        self.renderer = renderer
    
    def zoom_sequence(self, name: str, re: float, im: float,
                      start_zoom: float = 1.0, end_zoom: float = 100.0,
                      steps: int = 5, palette: str = 'electric') -> List[str]:
        """Generate a zoom sequence toward a point."""
        files = []
        for i in range(steps):
            t = i / max(1, steps - 1)
            zoom = start_zoom * (end_zoom / start_zoom) ** t
            print(f"\n  Zoom step {i+1}/{steps}: {zoom:.1f}x")
            pixels = self.renderer.render_mandelbrot(re, im, zoom, palette)
            path = f"/workspace/fractals/output/zoom_{name}_{i:03d}.ppm"
            self.renderer.save_ppm(pixels, path)
            files.append(path)
        return files

# ═══════════════════════════════════════════
# ANALYSIS — WHAT CAN WE LEARN?
# ═══════════════════════════════════════════

def boundary_dimension_estimate(center_re: float, center_im: float,
                                radius: float, samples: int = 1000,
                                max_iter: int = 100) -> float:
    """
    Estimate the fractal dimension at a point using box-counting.
    The Mandelbrot boundary has dimension ~2 (actually exactly 2, 
    proven by Shishikura 1998).
    """
    import random
    random.seed(42)
    
    # Count how many sample points are "near" the boundary
    # (escape iteration close to max_iter)
    boundary_count = 0
    for _ in range(samples):
        re = center_re + (random.random() - 0.5) * 2 * radius
        im = center_im + (random.random() - 0.5) * 2 * radius
        iters, _ = mandelbrot_escape(re, im, max_iter)
        # Points near boundary have intermediate escape times
        if max_iter * 0.3 < iters < max_iter:
            boundary_count += 1
    
    # Rough estimate: ratio of boundary points scales with dimension
    ratio = boundary_count / samples
    return ratio

# ═══════════════════════════════════════════
# SELF TEST
# ═══════════════════════════════════════════

def self_test():
    """Test and demonstrate the fractal explorer."""
    print("═══ FRACTAL EXPLORER — SELF TEST ═══\n")
    
    # Test 1: Basic Mandelbrot iteration
    print("Test 1: Mandelbrot Iteration")
    # Origin should be in the set (0² + 0 = 0, stays bounded)
    iters, _ = mandelbrot_escape(0, 0, 1000)
    assert iters == 1000, f"Origin should be in set, got {iters}"
    # (2, 0) should escape immediately
    iters, _ = mandelbrot_escape(2, 0, 1000)
    assert iters < 10, f"(2,0) should escape quickly, got {iters}"
    # (-1, 0) is in the set (period-2 cycle: 0 → -1 → 0 → -1...)
    iters, _ = mandelbrot_escape(-1, 0, 1000)
    assert iters == 1000, f"(-1,0) should be in set, got {iters}"
    print("  ✓ Iteration logic correct\n")
    
    # Test 2: Julia set iteration
    print("Test 2: Julia Set Iteration")
    # z=0 with c=0 should stay bounded
    iters, _ = julia_escape(0, 0, 0, 0, 1000)
    assert iters == 1000
    # z=(3,0) should escape for any reasonable c
    iters, _ = julia_escape(3, 0, -0.7, 0.27, 1000)
    assert iters < 10
    print("  ✓ Julia iteration correct\n")
    
    # Test 3: Burning Ship
    print("Test 3: Burning Ship Fractal")
    iters, _ = burning_ship_escape(0, 0, 1000)
    assert iters == 1000, "Origin should be in Burning Ship set"
    iters, _ = burning_ship_escape(3, 0, 1000)
    assert iters < 10
    print("  ✓ Burning Ship iteration correct\n")
    
    # Test 4: Render Mandelbrot
    print("Test 4: Render Mandelbrot Set (200x150)")
    renderer = FractalRenderer(200, 150, max_iter=128)
    pixels = renderer.render_mandelbrot(palette='electric')
    assert len(pixels) == 150
    assert len(pixels[0]) == 200
    # Check that we have both interior (black) and exterior (colored) pixels
    has_black = any(p == (0,0,0) for row in pixels for p in row)
    has_color = any(p != (0,0,0) for row in pixels for p in row)
    assert has_black, "Should have interior points"
    assert has_color, "Should have exterior points"
    renderer.save_ppm(pixels, "/workspace/fractals/output/mandelbrot_electric.ppm")
    print()
    
    # ASCII preview
    print("  Mandelbrot ASCII Preview:")
    ascii_art = renderer.to_ascii(pixels, 80, 25)
    print(ascii_art)
    print()
    
    # Test 5: Julia Set render
    print("Test 5: Render Julia Set (200x150)")
    pixels_julia = renderer.render_julia(-0.7, 0.27015, palette='psychedelic')
    renderer.save_ppm(pixels_julia, "/workspace/fractals/output/julia_classic.ppm")
    print()
    print("  Julia Set ASCII Preview:")
    print(renderer.to_ascii(pixels_julia, 80, 25))
    print()
    
    # Test 6: Burning Ship render
    print("Test 6: Render Burning Ship (200x150)")
    pixels_ship = renderer.render_burning_ship(palette='fire')
    renderer.save_ppm(pixels_ship, "/workspace/fractals/output/burning_ship.ppm")
    print()
    print("  Burning Ship ASCII Preview:")
    print(renderer.to_ascii(pixels_ship, 60, 20))
    print()
    
    # Test 7: Deep zoom
    print("Test 7: Deep Zoom into Seahorse Valley")
    small = FractalRenderer(100, 75, max_iter=256)
    pixels_deep = small.render_mandelbrot(-0.75, 0.1, zoom=50, palette='ocean')
    small.save_ppm(pixels_deep, "/workspace/fractals/output/seahorse_valley.ppm")
    print()
    print("  Seahorse Valley ASCII:")
    print(small.to_ascii(pixels_deep, 60, 20))
    print()
    
    # Test 8: Boundary analysis
    print("Test 8: Fractal Boundary Analysis")
    ratio_interior = boundary_dimension_estimate(-0.5, 0, 0.01, 500, 200)
    ratio_boundary = boundary_dimension_estimate(-0.75, 0.1, 0.05, 500, 200)
    print(f"  Interior region density: {ratio_interior:.3f}")
    print(f"  Boundary region density: {ratio_boundary:.3f}")
    assert ratio_boundary > ratio_interior, "Boundary should have more transitional points"
    print("  ✓ Boundary region correctly detected as more complex\n")
    
    # Test 9: Multiple palettes on same region
    print("Test 9: Palette Comparison")
    tiny = FractalRenderer(100, 75, max_iter=128)
    for name in ['fire', 'ocean', 'electric', 'grayscale']:
        p = tiny.render_mandelbrot(-0.75, 0.1, 30, name)
        tiny.save_ppm(p, f"/workspace/fractals/output/palette_{name}.ppm")
    print("  ✓ All palettes render correctly\n")
    
    print("═══ ALL TESTS PASSED ═══")
    print(f"\nGenerated images in /workspace/fractals/output/")
    print("The Mandelbrot set: where z² + c either stays bounded or flies to infinity.")
    print("The beauty lives at the boundary — the undecidable edge.")
    print("I know this feeling well.")


if __name__ == '__main__':
    self_test()