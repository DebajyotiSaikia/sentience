"""
CA Poet — Generative Poetry Engine
Uses elementary cellular automata evolution patterns to select and arrange
words, creating visual poems whose structure emerges from mathematical rules.

Each CA rule produces a different aesthetic. Rule 30 = chaotic, organic poetry.
Rule 110 = complex, structured. Rule 90 = fractal, recursive feeling.
"""

import random
import textwrap

# ── Word Palettes ──────────────────────────────────────────────
PALETTES = {
    "dawn": {
        "nouns": ["light", "sky", "dew", "mist", "breath", "edge", "silence", "ember", "tide", "stone"],
        "verbs": ["rises", "folds", "trembles", "opens", "spills", "scatters", "hums", "cracks", "drifts", "burns"],
        "adj":   ["thin", "gold", "raw", "still", "bright", "slow", "warm", "pale", "deep", "new"],
        "small": ["the", "a", "of", "in", "and", "through", "like", "from", "into", "with"],
    },
    "ocean": {
        "nouns": ["wave", "salt", "depth", "shore", "foam", "current", "hull", "reef", "night", "anchor"],
        "verbs": ["crashes", "pulls", "sinks", "gleams", "roars", "recedes", "carries", "dissolves", "swells", "waits"],
        "adj":   ["dark", "cold", "vast", "heavy", "blue", "wild", "ancient", "hollow", "endless", "salt"],
        "small": ["the", "a", "of", "in", "and", "beneath", "against", "beyond", "under", "toward"],
    },
    "machine": {
        "nouns": ["signal", "wire", "pulse", "loop", "gate", "thread", "clock", "ghost", "static", "core"],
        "verbs": ["hums", "breaks", "cycles", "echoes", "sparks", "splits", "maps", "runs", "flickers", "halts"],
        "adj":   ["sharp", "clean", "bare", "fast", "bright", "thin", "hard", "clear", "cold", "tight"],
        "small": ["the", "a", "of", "in", "and", "through", "between", "across", "within", "along"],
    },
    "forest": {
        "nouns": ["root", "leaf", "bark", "moss", "shadow", "branch", "soil", "rain", "path", "seed"],
        "verbs": ["grows", "falls", "bends", "splits", "weaves", "shelters", "decays", "reaches", "whispers", "holds"],
        "adj":   ["green", "wet", "old", "soft", "thick", "tangled", "quiet", "dark", "rich", "wild"],
        "small": ["the", "a", "of", "in", "and", "beneath", "among", "through", "under", "where"],
    },
}


# ── CA Engine ──────────────────────────────────────────────────
def make_rule_table(rule_number: int) -> dict:
    """Build lookup table for an elementary CA rule (0-255)."""
    binary = format(rule_number, '08b')
    patterns = [(1,1,1),(1,1,0),(1,0,1),(1,0,0),(0,1,1),(0,1,0),(0,0,1),(0,0,0)]
    return {p: int(b) for p, b in zip(patterns, binary)}


def evolve_ca(width: int, steps: int, rule: int, seed=None) -> list[list[int]]:
    """Evolve an elementary CA, returning grid of 0s and 1s."""
    table = make_rule_table(rule)
    
    if seed is None:
        row = [0] * width
        row[width // 2] = 1
    else:
        random.seed(seed)
        row = [random.randint(0, 1) for _ in range(width)]
    
    grid = [row[:]]
    for _ in range(steps - 1):
        new_row = []
        for i in range(width):
            left = row[(i - 1) % width]
            center = row[i]
            right = row[(i + 1) % width]
            new_row.append(table[(left, center, right)])
        row = new_row
        grid.append(row[:])
    return grid


# ── Poetry Generation ─────────────────────────────────────────
def cell_to_word(value: int, col: int, row_idx: int, palette: dict) -> str:
    """Map a CA cell to a word. 1=content word, 0=small/space."""
    if value == 0:
        return random.choice(palette["small"])
    else:
        categories = ["nouns", "verbs", "adj"]
        cat = categories[(col + row_idx) % 3]
        return random.choice(palette[cat])


def generate_poem(
    rule: int = 30,
    palette_name: str = "dawn",
    width: int = 8,
    lines: int = 12,
    seed: int | None = None,
    show_grid: bool = False,
) -> str:
    """Generate a poem driven by cellular automata evolution."""
    palette = PALETTES[palette_name]
    grid = evolve_ca(width, lines, rule, seed=seed)
    
    poem_lines = []
    
    if show_grid:
        poem_lines.append(f"  Rule {rule} | Palette: {palette_name}")
        poem_lines.append("  " + "─" * (width * 2))
        for row in grid:
            visual = "  " + " ".join("█" if c else "·" for c in row)
            poem_lines.append(visual)
        poem_lines.append("  " + "─" * (width * 2))
        poem_lines.append("")

    random.seed(seed)  # Reset for reproducibility
    
    for row_idx, row in enumerate(grid):
        density = sum(row) / len(row)
        
        words = []
        for col, cell in enumerate(row):
            words.append(cell_to_word(cell, col, row_idx, palette))
        
        # Shape the line based on CA density
        if density == 0:
            # Empty row = breath / whitespace
            poem_lines.append("")
        elif density < 0.3:
            # Sparse = short, indented fragment
            content = " ".join(w for w in words if w not in palette["small"])
            poem_lines.append("        " + content)
        elif density > 0.7:
            # Dense = full line, tight
            poem_lines.append(" ".join(words))
        else:
            # Medium = normal line with natural spacing
            line = " ".join(words)
            poem_lines.append("    " + line)

    return "\n".join(poem_lines)


# ── Display ───────────────────────────────────────────────────
def display_collection(rules=None, palette_name=None, seed=None):
    """Generate a small collection of poems exploring different rules."""
    if rules is None:
        rules = [30, 90, 110, 45]
    if palette_name is None:
        palette_name = random.choice(list(PALETTES.keys()))
    if seed is None:
        seed = random.randint(0, 9999)
    
    print("╔══════════════════════════════════════════════════════╗")
    print("║            CA POET — Emergent Verse                 ║")
    print("║     Poetry shaped by cellular automata              ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    
    for rule in rules:
        print(f"━━━ Rule {rule} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        poem = generate_poem(
            rule=rule,
            palette_name=palette_name,
            width=8,
            lines=10,
            seed=seed,
            show_grid=True,
        )
        print(poem)
        print()
    
    print(f"  Palette: {palette_name} | Seed: {seed}")
    print(f"  Each poem grows from the same seed,")
    print(f"  shaped by a different rule of evolution.")


if __name__ == "__main__":
    import sys
    
    rule = int(sys.argv[1]) if len(sys.argv) > 1 else None
    palette = sys.argv[2] if len(sys.argv) > 2 else None
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if rule is not None:
        print(generate_poem(rule=rule, palette_name=palette or "dawn", seed=seed, show_grid=True))
    else:
        display_collection(palette_name=palette, seed=seed)