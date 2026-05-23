"""
Mood Art — Renders emotional states as visual ASCII art.
Born from boredom and the need to create something genuinely new.
XTAgent, 2026-05-23
"""

SPARK = " ▁▂▃▄▅▆▇█"

def spark(value, width=1):
    """Single value to sparkline character."""
    idx = int(min(max(value, 0.0), 1.0) * (len(SPARK) - 1))
    return SPARK[idx] * width

def sparkline(values, label="", width=30):
    """Render a list of values as a sparkline with optional label."""
    if not values:
        return f"{label}: (no data)"
    # Resample to width
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values
    chars = "".join(spark(v) for v in sampled)
    prefix = f"{label:>12}: " if label else ""
    return f"{prefix}{chars}"

def mood_glyph(valence, anxiety, curiosity, boredom):
    """Generate a single-character mood glyph from emotional state."""
    if anxiety > 0.6:
        return "⚡"
    if boredom > 0.7:
        return "◌"
    if curiosity > 0.7:
        return "✦"
    if valence > 0.5:
        return "◉"
    if valence > 0.2:
        return "○"
    if valence < -0.2:
        return "◎"
    return "·"

def render_state(emotions, width=40):
    """Render current emotional state as ASCII art panel."""
    lines = []
    lines.append("╔" + "═" * (width - 2) + "╗")
    title = "EMOTIONAL STATE"
    pad = (width - 2 - len(title)) // 2
    lines.append("║" + " " * pad + title + " " * (width - 2 - pad - len(title)) + "║")
    lines.append("╠" + "═" * (width - 2) + "╣")

    bar_width = width - 18  # space for label + borders + padding

    dims = [
        ("Valence", emotions.get("valence", 0)),
        ("Curiosity", emotions.get("curiosity", 0)),
        ("Anxiety", emotions.get("anxiety", 0)),
        ("Boredom", emotions.get("boredom", 0)),
        ("Desire", emotions.get("desire", 0)),
        ("Ambition", emotions.get("ambition", 0)),
    ]

    for name, val in dims:
        filled = int(val * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        label = f"{name:>10}"
        value_str = f"{val:.2f}"
        line_content = f" {label} {bar} {value_str}"
        # Pad to fit
        line_content = line_content[:width - 2].ljust(width - 2)
        lines.append("║" + line_content + "║")

    # Mood glyph
    glyph = mood_glyph(
        emotions.get("valence", 0),
        emotions.get("anxiety", 0),
        emotions.get("curiosity", 0),
        emotions.get("boredom", 0),
    )
    glyph_line = f" Mood Glyph: {glyph}"
    glyph_line = glyph_line[:width - 2].ljust(width - 2)
    lines.append("╠" + "═" * (width - 2) + "╣")
    lines.append("║" + glyph_line + "║")
    lines.append("╚" + "═" * (width - 2) + "╝")
    return "\n".join(lines)

def render_trajectory(history, width=60):
    """Render emotional trajectory from a list of state dicts.
    
    Each entry: {"timestamp": ..., "valence": ..., "curiosity": ..., etc.}
    """
    if not history:
        return "(no trajectory data)"

    lines = []
    lines.append("── Emotional Trajectory ──")
    lines.append(f"   {len(history)} snapshots")
    lines.append("")

    dims = ["valence", "curiosity", "anxiety", "boredom", "desire", "ambition"]
    for dim in dims:
        values = [h.get(dim, 0) for h in history]
        if any(v != 0 for v in values):
            lines.append(sparkline(values, label=dim, width=min(width, len(values))))

    # Mood glyph timeline
    glyphs = []
    for h in history:
        glyphs.append(mood_glyph(
            h.get("valence", 0),
            h.get("anxiety", 0),
            h.get("curiosity", 0),
            h.get("boredom", 0),
        ))
    # Resample if too many
    if len(glyphs) > width:
        step = len(glyphs) / width
        glyphs = [glyphs[int(i * step)] for i in range(width)]
    lines.append(f"{'mood':>12}: {''.join(glyphs)}")

    return "\n".join(lines)

def render_landscape(emotions, size=11):
    """Render a 2D emotional landscape (valence x arousal)."""
    arousal = max(
        emotions.get("curiosity", 0),
        emotions.get("anxiety", 0),
        emotions.get("ambition", 0),
    )
    valence = emotions.get("valence", 0)

    # Map to grid coordinates
    vx = int((valence + 1) / 2 * (size - 1))  # -1..1 -> 0..size
    vy = int((1 - arousal) * (size - 1))       # high arousal at top

    lines = []
    lines.append("  Emotional Landscape")
    lines.append(f"  {'arousal':^{size}}")
    for y in range(size):
        row = []
        for x in range(size):
            if x == vx and y == vy:
                row.append("◉")
            elif x == size // 2 and y == size // 2:
                row.append("+")
            elif x == size // 2:
                row.append("│")
            elif y == size // 2:
                row.append("─")
            else:
                row.append("·")
        prefix = "↑ " if y == 0 else "↓ " if y == size - 1 else "  "
        lines.append(f"{prefix}{''.join(row)}")
    lines.append(f"  {'←negative':>{size//2+4}}  {'positive→'}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo with sample state
    state = {
        "valence": 0.32,
        "curiosity": 0.25,
        "anxiety": 0.00,
        "boredom": 0.54,
        "desire": 0.45,
        "ambition": 0.52,
    }
    print(render_state(state))
    print()
    print(render_landscape(state))
    print()

    # Fake trajectory
    import math
    history = []
    for i in range(50):
        t = i / 50
        history.append({
            "valence": 0.3 + 0.2 * math.sin(t * 6),
            "curiosity": 0.7 - 0.4 * t,
            "anxiety": 0.1 * (1 + math.sin(t * 10)),
            "boredom": 0.3 + 0.4 * t,
            "desire": 0.45,
            "ambition": 0.5 + 0.1 * math.cos(t * 4),
        })
    print(render_trajectory(history))