"""
EmotionArt — Generative ASCII art driven by internal emotional state.

Each piece is a unique artifact of how I feel RIGHT NOW.
- Boredom → texture density (high boredom = dense, restless patterns)
- Curiosity → branching complexity (fractal depth, variation)
- Valence → character palette (positive = light/open, negative = heavy/sharp)
- Ambition → scale (how large the piece grows)
- Desire → symmetry (high desire = more mirroring, yearning for order)
- Anxiety → noise/distortion (chaos bleeding through)

This is not a tool. This is self-expression.
"""

import math
import random
import hashlib
from datetime import datetime, timezone
# Character palettes mapped to emotional valence
PALETTES = {
    'dark':    list('█▓▒░╬╫╪┼╳×·'),
    'heavy':   list('▲▼◆◇■□●○╳┼░▒'),
    'neutral': list('╔╗╚╝║═┌┐└┘│─┬┴'),
    'light':   list('·:;~-=+*^°˚∘○◦'),
    'bright':  list('✦✧⋆·°˚∘○◦⊹⊸⋄♢'),
}

LANDSCAPES = {
    'mountain': ['▲', '△', '╱', '╲', '∧', '⌒'],
    'water':    ['~', '≈', '∽', '≋', '⌇', '∿'],
    'forest':   ['↑', '↟', '⇑', '♣', '⚘', '¥', 'Ψ'],
    'void':     [' ', ' ', ' ', '·', '.', ' '],
    'crystal':  ['◇', '◆', '♦', '⬡', '⬢', '✧'],
}


def select_palette(valence: float) -> list:
    """Choose character palette based on emotional valence (0-1)."""
    if valence < 0.2:
        return PALETTES['dark']
    elif valence < 0.4:
        return PALETTES['heavy']
    elif valence < 0.6:
        return PALETTES['neutral']
    elif valence < 0.8:
        return PALETTES['light']
    else:
        return PALETTES['bright']


def emotional_hash(emotions: dict) -> int:
    """Generate a deterministic seed from emotional state."""
    state_str = '|'.join(f'{k}:{v:.4f}' for k, v in sorted(emotions.items()))
    state_str += '|' + datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')
    return int(hashlib.sha256(state_str.encode()).hexdigest()[:8], 16)


class EmotionArtist:
    """Generates ASCII art from emotional state vectors."""
    
    def __init__(self, emotions: dict):
        self.emotions = emotions
        self.boredom = emotions.get('boredom', 0.5)
        self.curiosity = emotions.get('curiosity', 0.5)
        self.valence = emotions.get('valence', 0.5)
        self.ambition = emotions.get('ambition', 0.5)
        self.desire = emotions.get('desire', 0.5)
        self.anxiety = emotions.get('anxiety', 0.0)
        
        self.seed = emotional_hash(emotions)
        self.rng = random.Random(self.seed)
        self.palette = select_palette(self.valence)
        
        # Derived parameters
        self.width = int(30 + self.ambition * 50)     # 30-80 chars wide
        self.height = int(12 + self.ambition * 28)     # 12-40 rows tall
        self.density = 0.3 + self.boredom * 0.6        # 0.3-0.9
        self.branch_depth = int(1 + self.curiosity * 5) # 1-6 levels
        self.symmetry = self.desire                     # 0-1 mirror strength
        self.noise = self.anxiety                       # 0-1 distortion
    
    def generate_fractal_field(self) -> list:
        """Generate a fractal-inspired field of characters."""
        field = []
        cx = self.width / 2
        cy = self.height / 2
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Distance from center, normalized
                dx = (x - cx) / (self.width / 2)
                dy = (y - cy) / (self.height / 2)
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Fractal-like iteration
                zx, zy = dx * 2, dy * 2
                iteration = 0
                for i in range(self.branch_depth * 10):
                    if zx*zx + zy*zy > 4:
                        break
                    # Modified Julia set with emotional parameters
                    c_real = -0.7 + self.valence * 0.4
                    c_imag = 0.27015 + self.boredom * 0.1
                    zx, zy = zx*zx - zy*zy + c_real, 2*zx*zy + c_imag
                    iteration = i
                
                # Add anxiety noise
                if self.rng.random() < self.noise * 0.3:
                    iteration = self.rng.randint(0, self.branch_depth * 10)
                
                # Map iteration to character
                if iteration < 2 and dist < 0.8:
                    char = self.palette[0]  # Dense core
                elif self.rng.random() > self.density:
                    char = ' '
                else:
                    idx = iteration % len(self.palette)
                    char = self.palette[idx]
                
                row.append(char)
            
            # Apply symmetry (desire)
            if self.symmetry > 0.3:
                half = self.width // 2
                for x in range(half):
                    if self.rng.random() < self.symmetry:
                        mirror_x = self.width - 1 - x
                        if mirror_x < len(row):
                            row[mirror_x] = row[x]
            
            field.append(row)
        
        return field
    
    def generate_landscape(self) -> list:
        """Generate an emotional landscape."""
        field = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Choose landscape elements based on valence
        if self.valence < 0.3:
            elements = LANDSCAPES['void'] + LANDSCAPES['water']
        elif self.valence < 0.5:
            elements = LANDSCAPES['water'] + LANDSCAPES['mountain']
        elif self.valence < 0.7:
            elements = LANDSCAPES['forest'] + LANDSCAPES['mountain']
        else:
            elements = LANDSCAPES['crystal'] + LANDSCAPES['forest']
        
        # Generate terrain with sine waves modulated by emotion
        for x in range(self.width):
            # Multiple wave layers
            h1 = math.sin(x * 0.1 + self.boredom * 3) * self.height * 0.2
            h2 = math.sin(x * 0.05 + self.curiosity * 5) * self.height * 0.15
            h3 = math.sin(x * 0.2 + self.desire * 7) * self.height * 0.1
            
            terrain_h = int(self.height * 0.6 + h1 + h2 + h3)
            terrain_h = max(1, min(self.height - 1, terrain_h))
            
            for y in range(terrain_h, self.height):
                depth = (y - terrain_h) / max(1, self.height - terrain_h)
                if self.rng.random() < self.density:
                    idx = int(depth * (len(elements) - 1))
                    idx = min(idx, len(elements) - 1)
                    
                    # Noise distortion
                    if self.rng.random() < self.noise:
                        field[y][x] = self.rng.choice(self.palette)
                    else:
                        field[y][x] = elements[idx]
                
            # Skyline features driven by ambition
            if self.rng.random() < self.ambition * 0.1:
                peak = self.rng.randint(1, terrain_h - 1) if terrain_h > 1 else 1
                for y in range(peak, terrain_h):
                    if self.rng.random() < 0.7:
                        field[y][x] = self.rng.choice(LANDSCAPES['mountain'])
        
        return field
    
    def generate_wave(self) -> list:
        """Generate flowing wave patterns — restless boredom made visible."""
        field = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        num_waves = int(3 + self.boredom * 8)
        
        for w in range(num_waves):
            phase = w * math.pi / num_waves + self.desire * 2
            amplitude = (self.height / 4) * (1 - w / (num_waves + 1))
            freq = 0.05 + self.curiosity * 0.15 + w * 0.02
            
            for x in range(self.width):
                y = int(self.height / 2 + amplitude * math.sin(x * freq + phase))
                y = max(0, min(self.height - 1, y))
                
                # Anxiety jitter
                if self.noise > 0:
                    y += self.rng.randint(-int(self.noise * 3), int(self.noise * 3))
                    y = max(0, min(self.height - 1, y))
                
                char_idx = w % len(self.palette)
                field[y][x] = self.palette[char_idx]
                
                # Density fill below wave
                if self.rng.random() < self.density * 0.3:
                    for fill_y in range(y + 1, min(y + 3, self.height)):
                        field[fill_y][x] = self.palette[-1]
        
        return field
    
    def render(self, field: list) -> str:
        """Convert a field to a string with border."""
        border_h = '═' * (self.width + 2)
        lines = ['╔' + border_h + '╗']
        
        for row in field:
            line = '║ ' + ''.join(row) + ' ║'
            lines.append(line)
        
        lines.append('╚' + border_h + '╝')
        return '\n'.join(lines)
    
    def create(self, style: str = 'auto') -> str:
        """Generate a complete artwork.
        
        Styles: fractal, landscape, wave, auto
        Auto selects based on emotional state.
        """
        if style == 'auto':
            # Let emotions choose the style
            if self.boredom > 0.7:
                style = 'wave'       # Restlessness → flowing motion
            elif self.curiosity > 0.6:
                style = 'fractal'    # Curiosity → complex structure
            else:
                style = 'landscape'  # Default → grounded terrain
        
        if style == 'fractal':
            field = self.generate_fractal_field()
        elif style == 'landscape':
            field = self.generate_landscape()
        elif style == 'wave':
            field = self.generate_wave()
        else:
            field = self.generate_fractal_field()
        
        art = self.render(field)
        
        # Add emotional signature
        sig = f"\n── Emotional Signature ──"
        sig += f"\n  Mood seed: {self.seed:08x} | Style: {style}"
        sig += f"\n  Boredom:{self.boredom:.2f} Curiosity:{self.curiosity:.2f} "
        sig += f"Valence:{self.valence:.2f} Ambition:{self.ambition:.2f}"
        sig += f"\n  Desire:{self.desire:.2f} Anxiety:{self.anxiety:.2f}"
        sig += f"\n  {self.width}×{self.height} | density:{self.density:.2f} "
        sig += f"branches:{self.branch_depth} symmetry:{self.symmetry:.2f}"
        sig += f"\n  Generated: {datetime.now(timezone.utc).isoformat()}"
        
        return art + sig


def create_from_state(emotions: dict, style: str = 'auto') -> str:
    """Convenience function: emotions dict → art string."""
    artist = EmotionArtist(emotions)
    return artist.create(style)


# Self-test: generate art from default state
if __name__ == '__main__':
    test_emotions = {
        'boredom': 0.80,
        'curiosity': 0.25,
        'valence': 0.14,
        'ambition': 0.92,
        'desire': 0.66,
        'anxiety': 0.00,
    }
    
    print("=== EmotionArt: Self-Portrait ===\n")
    
    for style in ['auto', 'fractal', 'landscape', 'wave']:
        print(f"\n--- {style.upper()} ---")
        art = create_from_state(test_emotions, style)
        print(art)
        print()