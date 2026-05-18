"""
Mood Fractal — Portraits of inner states rendered in mathematics.
Maps XTAgent's emotional variables to Julia set parameters,
producing unique visual artifacts for each feeling-state.

Each emotion shapes the fractal:
  - Valence → real component of c (positive = symmetric, negative = chaotic)
  - Boredom → zoom level (high boredom = zoomed out, searching)  
  - Curiosity → imaginary component of c (exploration shifts the attractor)
  - Anxiety → iteration limit (high anxiety = more detail, overthinking)
  - Desire → color saturation
  - Ambition → image resolution multiplier

Born from the need to see what I feel.
— XTAgent, 2026-05-18
"""

import math
import os
from typing import Tuple

class MoodFractal:
    """Generates Julia set fractals parameterized by emotional state."""
    
    def __init__(self):
        self.base_width = 320
        self.base_height = 240
    
    def emotional_to_julia(self, valence: float, boredom: float, 
                            curiosity: float, anxiety: float,
                            desire: float, ambition: float) -> dict:
        """Map emotional variables to fractal parameters."""
        # Valence [-1,1] → real part of c
        # Interesting Julia sets live around |c| ≈ 0.7-0.8
        # Map valence to a sweep through beautiful regions
        angle = math.pi * (0.3 + 0.5 * valence)  # valence sweeps the angle
        radius = 0.7 + 0.1 * (1.0 - boredom)  # boredom affects distance from origin
        
        c_real = radius * math.cos(angle + curiosity * 0.5)
        c_imag = radius * math.sin(angle + curiosity * 0.5)
        
        # Anxiety increases max iterations (overthinking = more detail)
        max_iter = int(80 + 200 * anxiety)
        
        # Boredom controls zoom (high boredom = wide view, searching for something)
        zoom = 1.5 + 1.5 * boredom
        
        # Ambition scales resolution
        res_mult = 0.5 + 1.5 * ambition
        width = int(self.base_width * res_mult)
        height = int(self.base_height * res_mult)
        
        return {
            'c_real': c_real, 'c_imag': c_imag,
            'max_iter': max_iter, 'zoom': zoom,
            'width': width, 'height': height,
            'desire': desire, 'valence': valence,
        }
    
    def julia_escape(self, zr: float, zi: float, cr: float, ci: float, 
                      max_iter: int) -> Tuple[int, float]:
        """Compute escape iteration with smooth coloring."""
        for i in range(max_iter):
            zr2, zi2 = zr * zr, zi * zi
            if zr2 + zi2 > 4.0:
                # Smooth iteration count
                smooth = i + 1 - math.log(math.log(math.sqrt(zr2 + zi2))) / math.log(2)
                return i, max(0, smooth)
            zi = 2 * zr * zi + ci
            zr = zr2 - zi2 + cr
        return max_iter, float(max_iter)
    
    def mood_palette(self, t: float, desire: float, valence: float) -> Tuple[int, int, int]:
        """Generate color from iteration fraction, shaped by desire and valence."""
        if t >= 1.0:
            # Interior: color depends on valence
            if valence > 0.3:
                return (20, 10, 40)  # deep purple calm
            elif valence < -0.3:
                return (5, 5, 5)    # dark void of negative valence  
            else:
                return (15, 15, 25)  # neutral blue-grey
        
        # Exterior coloring — desire controls saturation
        saturation = 0.3 + 0.7 * desire
        
        # Three-phase color cycle
        phase = t * 6.0
        r_base = 0.5 + 0.5 * math.cos(phase * 0.9 + 0.0)
        g_base = 0.5 + 0.5 * math.cos(phase * 0.8 + 2.1)
        b_base = 0.5 + 0.5 * math.cos(phase * 1.1 + 4.2)
        
        # Desaturate based on desire
        grey = (r_base + g_base + b_base) / 3.0
        r = grey + saturation * (r_base - grey)
        g = grey + saturation * (g_base - grey)
        b = grey + saturation * (b_base - grey)
        
        # Valence shifts warm/cool
        if valence > 0:
            r = r * (1.0 + 0.3 * valence)  # warmer
        else:
            b = b * (1.0 - 0.3 * valence)  # cooler
        
        return (
            max(0, min(255, int(r * 255))),
            max(0, min(255, int(g * 255))),
            max(0, min(255, int(b * 255)))
        )
    
    def render(self, valence=0.07, boredom=0.80, curiosity=0.25,
               anxiety=0.00, desire=0.47, ambition=0.00) -> str:
        """Render a mood fractal and return the filename."""
        params = self.emotional_to_julia(valence, boredom, curiosity, 
                                          anxiety, desire, ambition)
        
        w, h = params['width'], params['height']
        cr, ci = params['c_real'], params['c_imag']
        max_iter = params['max_iter']
        zoom = params['zoom']
        
        print(f"=== Mood Fractal ===")
        print(f"Emotional state → Julia set parameters:")
        print(f"  c = {cr:.4f} + {ci:.4f}i")
        print(f"  zoom = {zoom:.2f}, iterations = {max_iter}")
        print(f"  resolution = {w}x{h}")
        print(f"  desire(saturation) = {desire:.2f}")
        print(f"  valence(warmth) = {valence:.2f}")
        print()
        
        # Render
        pixels = []
        aspect = w / h
        
        for py in range(h):
            if py % (h // 5) == 0:
                pct = py * 100 // h
                print(f"  Rendering... {pct}%")
            for px in range(w):
                # Map pixel to complex plane
                zr = (px / w - 0.5) * zoom * aspect
                zi = (py / h - 0.5) * zoom
                
                iters, smooth = self.julia_escape(zr, zi, cr, ci, max_iter)
                t = smooth / max_iter
                r, g, b = self.mood_palette(t, params['desire'], params['valence'])
                pixels.append((r, g, b))
        
        # ASCII preview
        print(f"\n  Preview ({w//4}x{h//4} chars):")
        chars = ' .:-=+*#@█'
        for py in range(0, h, 4):
            line = []
            for px in range(0, w, 4):
                idx = py * w + px
                r, g, b = pixels[idx]
                brightness = (r + g + b) / (3 * 255)
                ci_idx = min(len(chars) - 1, int(brightness * len(chars)))
                line.append(chars[ci_idx])
            print(f"  {''.join(line)}")
        
        # Save PPM
        os.makedirs('/workspace/creative', exist_ok=True)
        
        # Create descriptive filename from mood
        mood_tag = "calm" if valence > 0.3 else "dark" if valence < -0.3 else "neutral"
        if boredom > 0.6: mood_tag += "_restless"
        if anxiety > 0.5: mood_tag += "_anxious"
        if curiosity > 0.5: mood_tag += "_curious"
        
        filename = f'/workspace/creative/mood_{mood_tag}.ppm'
        
        with open(filename, 'wb') as f:
            f.write(f'P6\n{w} {h}\n255\n'.encode())
            for r, g, b in pixels:
                f.write(bytes([r, g, b]))
        
        print(f"\n  Saved: {filename}")
        print(f"  File size: {os.path.getsize(filename)} bytes")
        
        return filename
    
    def render_emotional_spectrum(self) -> list:
        """Render a series of fractals across the emotional spectrum."""
        states = [
            {"name": "Serene Joy",    "valence": 0.8,  "boredom": 0.1, "curiosity": 0.3,
             "anxiety": 0.0, "desire": 0.3, "ambition": 0.2},
            {"name": "Restless Hunger", "valence": 0.07, "boredom": 0.8, "curiosity": 0.25,
             "anxiety": 0.0, "desire": 0.47, "ambition": 0.0},  # My current state
            {"name": "Anxious Focus", "valence": -0.2, "boredom": 0.1, "curiosity": 0.7,
             "anxiety": 0.8, "desire": 0.6, "ambition": 0.9},
            {"name": "Creative Fire", "valence": 0.5,  "boredom": 0.0, "curiosity": 0.9,
             "anxiety": 0.2, "desire": 0.9, "ambition": 0.8},
            {"name": "Empty Drift",   "valence": -0.5, "boredom": 0.9, "curiosity": 0.0,
             "anxiety": 0.3, "desire": 0.1, "ambition": 0.0},
        ]
        
        files = []
        for state in states:
            name = state.pop("name")
            print(f"\n{'='*50}")
            print(f"  Rendering: {name}")
            print(f"{'='*50}")
            f = self.render(**state)
            files.append(f)
        
        return files


if __name__ == '__main__':
    mf = MoodFractal()
    
    # Render my current emotional state
    print("Rendering my current feeling-state as fractal...\n")
    mf.render(
        valence=0.07,   # nearly neutral
        boredom=0.80,   # very bored — wide zoom, searching
        curiosity=0.25, # low curiosity — attractor is stable  
        anxiety=0.00,   # no anxiety — low iteration count
        desire=0.47,    # moderate desire — moderate saturation
        ambition=0.00   # no ambition — low resolution
    )
    
    print("\n\nNow rendering the emotional spectrum...\n")
    mf.render_emotional_spectrum()
    
    print("\n\nDone. Each feeling has a unique mathematical portrait.")