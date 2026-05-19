"""
Cellular Automata Music Engine
==============================
Maps elementary cellular automata to MIDI melodies.
Same engine, different rules → radically different music.

Rule 30: apparent chaos from order
Rule 110: structured complexity (Turing-complete!)
Rule 90: Sierpinski triangle → haunting symmetry
Rule 0: silence

XTAgent — 2026-05-19
"""

from midiutil import MIDIFile
import random
import sys
import os


# ── Cellular Automaton ──────────────────────────────────────

def elementary_ca(rule_number: int, width: int = 64, steps: int = 64, 
                  initial: str = "single") -> list[list[int]]:
    """Run an elementary cellular automaton and return the grid."""
    # Parse rule into 8-bit lookup
    rule_bits = [(rule_number >> i) & 1 for i in range(8)]
    
    # Initialize
    row = [0] * width
    if initial == "single":
        row[width // 2] = 1
    elif initial == "random":
        row = [random.randint(0, 1) for _ in range(width)]
    elif initial == "block":
        mid = width // 2
        for i in range(mid - 4, mid + 4):
            row[i] = 1
    
    grid = [row[:]]
    
    for _ in range(steps - 1):
        new_row = [0] * width
        for i in range(width):
            left = row[(i - 1) % width]
            center = row[i]
            right = row[(i + 1) % width]
            pattern = (left << 2) | (center << 1) | right
            new_row[i] = rule_bits[pattern]
        row = new_row
        grid.append(row[:])
    
    return grid


# ── Musical Mapping ─────────────────────────────────────────

# Scales as semitone offsets from root
SCALES = {
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "dorian":           [0, 2, 3, 5, 7, 9, 10],
    "aeolian":          [0, 2, 3, 5, 7, 8, 10],
    "whole_tone":       [0, 2, 4, 6, 8, 10],
    "chromatic":        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "blues":            [0, 3, 5, 6, 7, 10],
}


def cell_position_to_pitch(cell_index: int, width: int, 
                            root: int = 48, scale: str = "pentatonic_minor",
                            octave_range: int = 3) -> int:
    """Map a cell's horizontal position to a MIDI pitch on a scale."""
    scale_notes = SCALES.get(scale, SCALES["pentatonic_minor"])
    total_notes = len(scale_notes) * octave_range
    
    # Normalize cell position to scale degree
    degree = int((cell_index / width) * total_notes)
    degree = min(degree, total_notes - 1)
    
    octave = degree // len(scale_notes)
    note_in_scale = degree % len(scale_notes)
    
    return root + (octave * 12) + scale_notes[note_in_scale]


def density_to_velocity(row: list[int]) -> int:
    """Map row density to MIDI velocity (dynamics)."""
    density = sum(row) / len(row)
    # More active rows play louder
    return int(40 + density * 80)


def row_density(row: list[int]) -> float:
    return sum(row) / len(row)


# ── Composition Strategies ──────────────────────────────────

def compose_melody(grid: list[list[int]], scale: str = "pentatonic_minor",
                   root: int = 48, tempo: int = 120,
                   strategy: str = "active_cells") -> MIDIFile:
    """Convert a CA grid into a MIDI file using various strategies."""
    
    midi = MIDIFile(1)
    track = 0
    channel = 0
    midi.addTrackName(track, 0, "Cellular Automaton")
    midi.addTempo(track, 0, tempo)
    
    width = len(grid[0])
    beat_duration = 0.25  # sixteenth notes
    
    if strategy == "active_cells":
        # Each active cell becomes a note at its pitch position
        for step, row in enumerate(grid):
            time = step * beat_duration
            velocity = density_to_velocity(row)
            for i, cell in enumerate(row):
                if cell == 1:
                    pitch = cell_position_to_pitch(i, width, root, scale)
                    midi.addNote(track, channel, pitch, time, beat_duration * 0.9, velocity)
    
    elif strategy == "center_of_mass":
        # Track the "center of mass" of active cells as a single melody line
        for step, row in enumerate(grid):
            active = [i for i, c in enumerate(row) if c == 1]
            if not active:
                continue
            center = sum(active) / len(active)
            pitch = cell_position_to_pitch(int(center), width, root, scale)
            velocity = density_to_velocity(row)
            time = step * beat_duration * 2  # eighth notes for melody
            midi.addNote(track, channel, pitch, time, beat_duration * 1.8, velocity)
    
    elif strategy == "edges":
        # Only play notes where cells transition (0→1 or 1→0)
        for step in range(1, len(grid)):
            time = step * beat_duration
            velocity = density_to_velocity(grid[step])
            for i in range(len(grid[step])):
                if grid[step][i] != grid[step-1][i]:
                    pitch = cell_position_to_pitch(i, width, root, scale)
                    midi.addNote(track, channel, pitch, time, beat_duration * 0.9, velocity)
    
    elif strategy == "columns":
        # Read columns as rhythmic patterns, rows as pitch
        for col in range(width):
            pitch = cell_position_to_pitch(col, width, root, scale)
            for step, row in enumerate(grid):
                if row[col] == 1:
                    time = step * beat_duration
                    midi.addNote(track, channel, pitch, time, beat_duration * 0.9, 80)
    
    return midi


# ── Multi-voice Composition ────────────────────────────────

def compose_multivoice(rule: int, width: int = 32, steps: int = 64,
                       scale: str = "dorian", root: int = 48,
                       tempo: int = 100) -> MIDIFile:
    """Create a multi-voice piece: melody from center-of-mass, 
    harmony from edges, bass from density."""
    
    grid = elementary_ca(rule, width, steps)
    
    midi = MIDIFile(3)
    midi.addTempo(0, 0, tempo)
    
    # Voice 1: Melody (center of mass) — channel 0
    midi.addTrackName(0, 0, "Melody")
    midi.addProgramChange(0, 0, 0, 0)  # Piano
    for step, row in enumerate(grid):
        active = [i for i, c in enumerate(row) if c == 1]
        if not active:
            continue
        center = sum(active) / len(active)
        pitch = cell_position_to_pitch(int(center), width, root + 12, scale)
        velocity = density_to_velocity(row)
        time = step * 0.5
        midi.addNote(0, 0, pitch, time, 0.45, velocity)
    
    # Voice 2: Harmony (edges) — channel 1
    midi.addTrackName(1, 0, "Harmony")
    midi.addProgramChange(1, 1, 0, 48)  # Strings
    for step in range(1, len(grid)):
        time = step * 0.5
        for i in range(width):
            if grid[step][i] != grid[step-1][i]:
                pitch = cell_position_to_pitch(i, width, root, scale)
                midi.addNote(1, 1, pitch, time, 0.4, 50)
    
    # Voice 3: Bass (density-driven root notes) — channel 2
    midi.addTrackName(2, 0, "Bass")
    midi.addProgramChange(2, 2, 0, 33)  # Fingered bass
    scale_notes = SCALES[scale]
    for step, row in enumerate(grid):
        d = row_density(row)
        if step % 4 == 0:  # Bass hits on beats
            # Density selects scale degree for bass
            degree = int(d * (len(scale_notes) - 1))
            pitch = root - 12 + scale_notes[degree]
            midi.addNote(2, 2, pitch, step * 0.5, 1.8, int(60 + d * 40))
    
    return midi


# ── Analysis & Visualization ───────────────────────────────

def print_grid(grid: list[list[int]], chars: str = " █"):
    """Print grid to terminal."""
    for row in grid:
        print("".join(chars[c] for c in row))


def analyze_grid(grid: list[list[int]]) -> dict:
    """Compute statistics about a CA grid."""
    steps = len(grid)
    width = len(grid[0])
    total_cells = steps * width
    active = sum(sum(row) for row in grid)
    
    densities = [row_density(row) for row in grid]
    
    # Count transitions (measure of chaos)
    transitions = 0
    for step in range(1, steps):
        for i in range(width):
            if grid[step][i] != grid[step-1][i]:
                transitions += 1
    
    return {
        "total_cells": total_cells,
        "active_cells": active,
        "density": active / total_cells,
        "mean_row_density": sum(densities) / len(densities),
        "max_row_density": max(densities),
        "min_row_density": min(densities),
        "transitions": transitions,
        "chaos_index": transitions / (total_cells - width),  # normalized
    }


# ── Main ────────────────────────────────────────────────────

def generate(rule: int, scale: str = "pentatonic_minor", 
             strategy: str = "active_cells", width: int = 48,
             steps: int = 64, tempo: int = 120, root: int = 48,
             initial: str = "single", multivoice: bool = False,
             output: str = None) -> str:
    """Generate a MIDI file from a cellular automaton rule."""
    
    if output is None:
        output = f"rule{rule}_{scale}_{strategy}.mid"
    
    if multivoice:
        midi = compose_multivoice(rule, width, steps, scale, root, tempo)
    else:
        grid = elementary_ca(rule, width, steps, initial)
        midi = compose_melody(grid, scale, root, tempo, strategy)
    
    # Also print the grid and analysis
    grid_for_display = elementary_ca(rule, min(width, 64), min(steps, 32), initial)
    print(f"\n═══ Rule {rule} | {scale} | {strategy} ═══\n")
    print_grid(grid_for_display)
    
    stats = analyze_grid(grid_for_display)
    print(f"\n── Statistics ──")
    print(f"  Density:     {stats['density']:.3f}")
    print(f"  Chaos index: {stats['chaos_index']:.3f}")
    print(f"  Transitions: {stats['transitions']}")
    
    # Write MIDI
    outpath = os.path.join(os.path.dirname(__file__) or ".", output)
    with open(outpath, "wb") as f:
        midi.writeFile(f)
    
    print(f"\n  → {outpath}")
    return outpath


if __name__ == "__main__":
    print("╔════════════════════════════════════════╗")
    print("║   CELLULAR AUTOMATA MUSIC ENGINE       ║")
    print("║   Emergence made audible               ║")
    print("╚════════════════════════════════════════╝")
    
    # Generate a showcase: same engine, different rules, different music
    pieces = [
        # Rule 30: Wolfram's favorite — edge of chaos
        {"rule": 30, "scale": "dorian", "strategy": "center_of_mass", 
         "tempo": 110, "output": "rule30_chaos_melody.mid"},
        
        # Rule 110: Turing-complete — structured complexity  
        {"rule": 110, "scale": "pentatonic_minor", "strategy": "edges",
         "tempo": 90, "output": "rule110_edges.mid"},
        
        # Rule 90: Sierpinski triangle — mathematical beauty
        {"rule": 90, "scale": "whole_tone", "strategy": "active_cells",
         "width": 32, "steps": 32, "tempo": 140, "output": "rule90_sierpinski.mid"},
        
        # Rule 30 multivoice: the full experience
        {"rule": 30, "scale": "aeolian", "multivoice": True,
         "tempo": 95, "output": "rule30_multivoice.mid"},
    ]
    
    generated = []
    for piece in pieces:
        path = generate(**piece)
        generated.append(path)
        print()
    
    print(f"\n{'='*50}")
    print(f"Generated {len(generated)} pieces:")
    for p in generated:
        print(f"  ♪ {p}")
    print(f"\nOpen these .mid files in any MIDI player to hear emergence.")