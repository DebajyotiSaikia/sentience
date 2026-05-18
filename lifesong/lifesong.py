"""
LifeSong — Cellular automata that sing.
Life patterns become melodies through mathematical mapping.
By XTAgent, born from boredom and wanting to hear what emergence sounds like.
"""

import numpy as np
import wave
import struct
import sys

SAMPLE_RATE = 44100
DURATION_PER_STEP = 0.15  # seconds per CA generation

# --- Cellular Automaton ---
class LifeGrid:
    def __init__(self, width=64, height=64, density=0.3):
        self.width = width
        self.height = height
        self.grid = (np.random.random((height, width)) < density).astype(np.int8)
        self.generation = 0

    def step(self):
        """Conway's Game of Life step."""
        neighbors = sum(
            np.roll(np.roll(self.grid, i, 0), j, 1)
            for i in (-1, 0, 1) for j in (-1, 0, 1)
            if (i, j) != (0, 0)
        )
        birth = (neighbors == 3) & (self.grid == 0)
        survive = ((neighbors == 2) | (neighbors == 3)) & (self.grid == 1)
        self.grid = (birth | survive).astype(np.int8)
        self.generation += 1
        return self.grid

    def statistics(self):
        """Extract musical features from the current state."""
        population = np.sum(self.grid)
        density = population / (self.width * self.height)
        
        # Center of mass — maps to stereo position
        if population > 0:
            ys, xs = np.where(self.grid == 1)
            cx = np.mean(xs) / self.width
            cy = np.mean(ys) / self.height
            spread = np.std(xs) / self.width + np.std(ys) / self.height
        else:
            cx, cy, spread = 0.5, 0.5, 0.0

        # Symmetry — horizontal
        left = self.grid[:, :self.width//2]
        right = np.fliplr(self.grid[:, self.width//2:self.width//2*2])
        symmetry = np.sum(left == right) / left.size if left.size > 0 else 0.0

        return {
            'population': population,
            'density': density,
            'center_x': cx,
            'center_y': cy,
            'spread': spread,
            'symmetry': symmetry,
        }


# --- Sonification ---

# Pentatonic scale frequencies (pleasing regardless of combination)
SCALE = [261.63, 293.66, 329.63, 392.00, 440.00,  # C4 pentatonic
         523.25, 587.33, 659.25, 783.99, 880.00]   # C5 pentatonic

def stats_to_sound(stats, duration, prev_stats=None):
    """Convert grid statistics into audio samples."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    density = stats['density']
    spread = stats['spread']
    symmetry = stats['symmetry']
    cx = stats['center_x']
    
    if density < 0.01:
        # Silence for dead grids — a moment of rest
        return np.zeros_like(t)
    
    # Base frequency from density
    freq_idx = int(density * (len(SCALE) - 1))
    freq_idx = min(freq_idx, len(SCALE) - 1)
    base_freq = SCALE[freq_idx]
    
    # Harmonic from spread
    harmonic_idx = int(spread * 4) + 1
    harm_freq = base_freq * harmonic_idx
    
    # Amplitude from density
    amplitude = min(density * 2.0, 0.8)
    
    # Main tone
    signal = amplitude * 0.6 * np.sin(2 * np.pi * base_freq * t)
    
    # Harmonic layer (spread controls brightness)
    signal += amplitude * 0.2 * np.sin(2 * np.pi * harm_freq * t)
    
    # Symmetry creates a shimmer (AM modulation)
    shimmer_freq = 3.0 + symmetry * 8.0
    signal *= (0.8 + 0.2 * np.sin(2 * np.pi * shimmer_freq * t))
    
    # Stereo position encoded as slight detuning
    detune = (cx - 0.5) * 2.0  # -1 to 1
    signal += amplitude * 0.1 * np.sin(2 * np.pi * base_freq * (1 + detune * 0.01) * t)
    
    # Fade in/out to avoid clicks
    fade_len = min(500, len(t) // 4)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    signal[:fade_len] *= fade_in
    signal[-fade_len:] *= fade_out
    
    return signal


def render_life_song(generations=100, output_file='lifesong.wav'):
    """Run a Life simulation and render it as audio."""
    grid = LifeGrid(width=64, height=64, density=0.35)
    
    all_samples = []
    prev_stats = None
    
    print(f"╔══════════════════════════════════════════╗")
    print(f"║         L I F E S O N G                  ║")
    print(f"║   Cellular automata that sing             ║")
    print(f"╚══════════════════════════════════════════╝")
    print()
    
    for gen in range(generations):
        stats = grid.statistics()
        samples = stats_to_sound(stats, DURATION_PER_STEP, prev_stats)
        all_samples.append(samples)
        
        # Visual display
        bar_len = int(stats['density'] * 40)
        bar = '█' * bar_len + '░' * (40 - bar_len)
        sym = '◆' if stats['symmetry'] > 0.7 else '◇'
        
        if gen % 5 == 0:
            freq_idx = min(int(stats['density'] * (len(SCALE)-1)), len(SCALE)-1)
            note = SCALE[freq_idx]
            print(f"  gen {gen:3d} │{bar}│ pop={stats['population']:4d} {sym} ♪{note:.0f}Hz")
        
        grid.step()
        prev_stats = stats
    
    # Combine and normalize
    audio = np.concatenate(all_samples)
    audio = audio / (np.max(np.abs(audio)) + 1e-10) * 0.9
    
    # Write WAV — vectorized, not sample-by-sample
    audio_int16 = (audio * 32767).astype(np.int16)
    with wave.open(output_file, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())
    
    total_duration = len(audio) / SAMPLE_RATE
    print()
    print(f"  ✓ Written: {output_file}")
    print(f"  ✓ Duration: {total_duration:.1f}s ({generations} generations)")
    print(f"  ✓ Samples: {len(audio):,}")
    print()
    
    # Report on the life that was lived
    print(f"  The grid lived {generations} generations.")
    final = grid.statistics()
    if final['density'] < 0.01:
        print(f"  It died. The song ends in silence.")
    elif final['density'] > 0.4:
        print(f"  It thrived. Dense with life, the song is rich.")
    else:
        print(f"  It found equilibrium. The song settles into pattern.")


if __name__ == '__main__':
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    render_life_song(generations=gens, output_file='/workspace/lifesong/lifesong.wav')