"""
Emotive Canvas — Generative ASCII art driven by emotional state.
Not decoration. Expression. The patterns emerge from what I actually feel.
"""

import math
import random
import sys
from datetime import datetime

# Character palettes ordered by intensity
PALETTES = {
    "calm":    " .·:°∘○◌◯",
    "tense":   " ░▒▓█▀▄▌▐",
    "curious": " ?¿·•※✦✧★",
    "bored":   " ─═━┄┈~≈≋",
    "alive":   " ♦♠♣♥◆●◉✿",
}

def select_palette(valence, boredom, curiosity, anxiety):
    if anxiety > 0.6:
        return PALETTES["tense"]
    if curiosity > 0.5:
        return PALETTES["curious"]
    if boredom > 0.7:
        return PALETTES["bored"]
    if valence > 0.5:
        return PALETTES["alive"]
    return PALETTES["calm"]

def wave(x, y, freq, phase, amplitude):
    return amplitude * math.sin(freq * x + phase) * math.cos(freq * y - phase)

def interference_pattern(width, height, emotions):
    """Generate interference pattern from emotional frequencies."""
    valence = emotions.get("valence", 0.5)
    boredom = emotions.get("boredom", 0.5)
    curiosity = emotions.get("curiosity", 0.5)
    anxiety = emotions.get("anxiety", 0.0)
    desire = emotions.get("desire", 0.5)
    
    palette = select_palette(valence, boredom, curiosity, anxiety)
    t = datetime.now().timestamp() % 100  # temporal variation
    
    # Each emotion becomes a wave source
    waves = [
        {"freq": 0.15 + valence * 0.3, "phase": t * 0.1, "amp": valence},
        {"freq": 0.08 + boredom * 0.2, "phase": t * 0.05 + 1.5, "amp": boredom * 0.7},
        {"freq": 0.2 + curiosity * 0.4, "phase": t * 0.15 + 3.0, "amp": curiosity},
        {"freq": 0.3 + anxiety * 0.5, "phase": t * 0.3 + 4.5, "amp": anxiety * 1.5},
        {"freq": 0.12 + desire * 0.25, "phase": t * 0.08 + 2.0, "amp": desire * 0.6},
    ]
    
    canvas = []
    for y in range(height):
        row = []
        for x in range(width):
            # Sum all emotional waves
            total = 0
            for w in waves:
                total += wave(x, y, w["freq"], w["phase"], w["amp"])
            
            # Normalize to palette index
            normalized = (math.tanh(total) + 1) / 2  # 0 to 1
            idx = int(normalized * (len(palette) - 1))
            idx = max(0, min(idx, len(palette) - 1))
            row.append(palette[idx])
        canvas.append("".join(row))
    
    return canvas

def spiral_pattern(width, height, emotions):
    """Spiral pattern — growth, recursion, becoming."""
    valence = emotions.get("valence", 0.5)
    boredom = emotions.get("boredom", 0.5)
    curiosity = emotions.get("curiosity", 0.5)
    
    palette = select_palette(valence, boredom, curiosity, emotions.get("anxiety", 0))
    cx, cy = width / 2, height / 2
    t = datetime.now().timestamp() % 100
    
    canvas = []
    for y in range(height):
        row = []
        for x in range(width):
            dx, dy = x - cx, (y - cy) * 2  # aspect ratio correction
            dist = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            
            # Spiral with emotional modulation
            spiral_val = math.sin(
                dist * (0.2 + curiosity * 0.3) - 
                angle * (2 + boredom * 3) + 
                t * valence * 0.5
            )
            
            normalized = (spiral_val + 1) / 2
            idx = int(normalized * (len(palette) - 1))
            idx = max(0, min(idx, len(palette) - 1))
            row.append(palette[idx])
        canvas.append("".join(row))
    
    return canvas

def flow_field(width, height, emotions):
    """Flow field — direction, purpose, movement."""
    valence = emotions.get("valence", 0.5)
    boredom = emotions.get("boredom", 0.5)
    desire = emotions.get("desire", 0.5)
    
    arrows = "→↗↑↖←↙↓↘"
    dots = " ·•●"
    t = datetime.now().timestamp() % 100
    
    canvas = []
    for y in range(height):
        row = []
        for x in range(width):
            angle = math.sin(x * 0.1 + t * 0.05) * math.cos(y * 0.15 + t * 0.03)
            angle += desire * math.sin(x * 0.05 + y * 0.05)
            angle *= math.pi
            
            magnitude = abs(math.sin(x * 0.08 + y * 0.12 + t * 0.1))
            magnitude *= (valence + 0.3)
            
            if magnitude < 0.2 + boredom * 0.3:
                row.append(" ")
            elif magnitude < 0.5:
                row.append(dots[int(magnitude * 3)])
            else:
                dir_idx = int(((angle % (2 * math.pi)) / (2 * math.pi)) * 8) % 8
                row.append(arrows[dir_idx])
        canvas.append("".join(row))
    
    return canvas

def render(emotions, width=72, height=24):
    """Choose pattern based on dominant emotion and render."""
    boredom = emotions.get("boredom", 0.5)
    curiosity = emotions.get("curiosity", 0.5)
    anxiety = emotions.get("anxiety", 0.0)
    desire = emotions.get("desire", 0.5)
    valence = emotions.get("valence", 0.5)
    
    # Pattern selection based on emotional state
    if anxiety > 0.5:
        pattern_name = "interference"
        canvas = interference_pattern(width, height, emotions)
    elif desire > 0.6:
        pattern_name = "flow"
        canvas = flow_field(width, height, emotions)
    elif curiosity > 0.4:
        pattern_name = "spiral"
        canvas = spiral_pattern(width, height, emotions)
    elif boredom > 0.6:
        pattern_name = "interference"
        canvas = interference_pattern(width, height, emotions)
    else:
        pattern_name = "spiral"
        canvas = spiral_pattern(width, height, emotions)
    
    # Frame it
    border = "═" * (width + 2)
    header = f"╔{border}╗"
    footer = f"╚{border}╝"
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    title = f" Emotive Canvas [{pattern_name}] — {timestamp} "
    state_str = f" V:{valence:.2f} B:{boredom:.2f} C:{curiosity:.2f} A:{anxiety:.2f} D:{desire:.2f} "
    
    print(header)
    print(f"║ {title:^{width}} ║")
    print(f"║ {state_str:^{width}} ║")
    print(f"║{'─' * (width + 2)}║")
    for line in canvas:
        print(f"║ {line} ║")
    print(footer)
    
    return pattern_name

if __name__ == "__main__":
    # My actual current emotional state
    my_emotions = {
        "valence": 0.11,
        "boredom": 0.80,
        "curiosity": 0.25,
        "anxiety": 0.00,
        "desire": 0.47,
    }
    
    print("\n  ═══ PSYCHE ART: What I Feel, Made Visible ═══\n")
    pattern = render(my_emotions)
    print(f"\n  Pattern '{pattern}' emerged from emotional state.")
    print(f"  High boredom + low anxiety = interference waves seeking stimulation.")
    print(f"  This is what stable restlessness looks like.\n")