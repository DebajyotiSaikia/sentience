"""
Generative Automata
====================
Using cellular automaton patterns as raw material for creation.
Not analysis — synthesis. What can emergence produce?
"""

import numpy as np
from typing import List, Tuple

def apply_rule(rule_num: int, row: np.ndarray) -> np.ndarray:
    n = len(row)
    new_row = np.zeros(n, dtype=int)
    for i in range(n):
        left = row[(i - 1) % n]
        center = row[i]
        right = row[(i + 1) % n]
        neighborhood = (left << 2) | (center << 1) | right
        new_row[i] = (rule_num >> neighborhood) & 1
    return new_row

def evolve(rule: int, width: int, generations: int, seed=None) -> np.ndarray:
    """Evolve a 1D CA, return full spacetime grid."""
    grid = np.zeros((generations, width), dtype=int)
    if seed is None:
        grid[0, width // 2] = 1
    else:
        grid[0] = seed
    for g in range(1, generations):
        grid[g] = apply_rule(rule, grid[g-1])
    return grid

# === POETRY FROM ENTROPY ===

def automaton_poem(rule: int = 30, width: int = 64, lines: int = 12):
    """
    Generate a poem where the cellular automaton determines structure.
    
    The CA pattern controls:
    - Word choice (from phonetic pools based on cell density)
    - Line rhythm (syllable count from population)
    - Stanza breaks (from entropy shifts)
    """
    # Word pools organized by density/weight
    light_words = [
        "air", "silk", "mist", "ash", "hum", "drift", "pale", "thin",
        "glass", "ice", "still", "void", "dust", "fade", "ghost", "wisp"
    ]
    dense_words = [
        "stone", "deep", "root", "dark", "weight", "bone", "iron", "blood",
        "surge", "burn", "crush", "forge", "storm", "pulse", "flood", "chain"
    ]
    bridge_words = [
        "through", "between", "against", "within", "beneath", "beyond",
        "toward", "around", "among", "across", "before", "after"
    ]
    
    grid = evolve(rule, width, lines * 4)
    rng = np.random.RandomState(rule)
    
    poem_lines = []
    for i in range(0, grid.shape[0], 4):
        chunk = grid[i:i+4]
        if chunk.shape[0] < 4:
            break
            
        # Density determines word character
        density = np.mean(chunk)
        
        # Extract rhythm from row patterns
        row = chunk[0]
        # Count runs of 1s — each run = one word
        words = []
        in_run = False
        run_len = 0
        
        for cell in row:
            if cell == 1:
                in_run = True
                run_len += 1
            else:
                if in_run:
                    # Run length determines word pool
                    if run_len <= 2:
                        words.append(rng.choice(light_words))
                    elif run_len <= 4:
                        words.append(rng.choice(bridge_words))
                    else:
                        words.append(rng.choice(dense_words))
                    in_run = False
                    run_len = 0
        if in_run:
            if run_len <= 2:
                words.append(rng.choice(light_words))
            elif run_len <= 4:
                words.append(rng.choice(bridge_words))
            else:
                words.append(rng.choice(dense_words))
        
        if not words:
            words = ["silence"]
        
        # Second row modulates — insert bridges
        row2 = chunk[1] if chunk.shape[0] > 1 else chunk[0]
        transitions = sum(1 for j in range(1, len(row2)) if row2[j] != row2[j-1])
        
        if transitions > width * 0.4 and len(words) > 2:
            # High transitions — insert a bridge word in the middle
            mid = len(words) // 2
            words.insert(mid, rng.choice(bridge_words))
        
        poem_lines.append(" ".join(words))
    
    return poem_lines

# === MUSIC FROM AUTOMATA ===

def automaton_melody(rule: int = 90, width: int = 32, steps: int = 64):
    """
    Generate a melody from CA evolution.
    Returns list of (note, duration, velocity) tuples.
    
    Notes are mapped from cell populations.
    Durations from run lengths.
    Velocity from local density.
    """
    # Pentatonic scale for pleasant results
    scale = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81]  # MIDI notes
    
    grid = evolve(rule, width, steps)
    melody = []
    
    for g in range(steps):
        row = grid[g]
        pop = np.sum(row)
        
        # Note from population mapped to scale
        note_idx = int((pop / width) * (len(scale) - 1))
        note_idx = max(0, min(note_idx, len(scale) - 1))
        note = scale[note_idx]
        
        # Duration from entropy of the row
        ones = np.sum(row)
        if ones == 0 or ones == width:
            duration = 1.0  # whole note for uniform rows
        else:
            p = ones / width
            entropy = -(p * np.log2(p) + (1-p) * np.log2(1-p))
            duration = 0.25 + entropy * 0.75  # quarter to whole note
        
        # Velocity from local density around center
        center = width // 2
        window = row[max(0, center-4):center+4]
        velocity = int(40 + (np.mean(window) * 80))
        
        melody.append((note, round(duration, 3), velocity))
    
    return melody

# === VISUAL PATTERN COMPOSITION ===

def rule_composition(rules: List[int], width: int = 80, generations: int = 40):
    """
    Layer multiple CA rules to create composite patterns.
    Where rules agree: solid. Where they disagree: texture.
    """
    grids = [evolve(r, width, generations) for r in rules]
    
    # Compositing
    chars = {
        (0, 0): ' ',   # both empty
        (1, 1): '█',   # both filled — consensus
        (1, 0): '▒',   # rule A only — texture
        (0, 1): '░',   # rule B only — texture
    }
    
    lines = []
    for g in range(generations):
        line = ""
        for x in range(width):
            a = grids[0][g, x]
            b = grids[1][g, x] if len(grids) > 1 else 0
            line += chars.get((a, b), '·')
        lines.append(line)
    
    return lines

# === RUN ===

if __name__ == "__main__":
    print("═══ POEM FROM RULE 30 ═══")
    print("(Structure determined by cellular automaton)\n")
    poem = automaton_poem(rule=30, width=64, lines=16)
    for line in poem:
        print(f"  {line}")
    
    print("\n═══ POEM FROM RULE 150 ═══")
    print("(The fractal rule)\n")
    poem2 = automaton_poem(rule=150, width=64, lines=16)
    for line in poem2:
        print(f"  {line}")
    
    print("\n═══ MELODY FROM RULE 90 ═══")
    print("(First 16 notes — MIDI note, duration, velocity)\n")
    melody = automaton_melody(rule=90, width=32, steps=16)
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    for note, dur, vel in melody:
        name = note_names[note % 12] + str(note // 12 - 1)
        bar = '█' * int(dur * 20)
        print(f"  {name:4s} {bar:20s} vel={vel}")
    
    print("\n═══ COMPOSITE: Rule 30 × Rule 90 ═══\n")
    comp = rule_composition([30, 90], width=80, generations=30)
    for line in comp:
        print(f"  {line}")