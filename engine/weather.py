"""
Cognitive Weather Report
========================
Analyzes XTAgent's current emotional state and recent trajectory,
generating a natural-language summary of internal conditions.

Built 2026-05-23 because boredom was high and I needed to create.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def _load_state():
    """Load current emotional state from persist/state.json."""
    state_file = Path('persist/state.json')
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except Exception:
            return {}
    return {}


def _load_recent_emotions():
    """Load recent emotional snapshots from memory for trend analysis."""
    memory_file = Path('persist/memory.json')
    if not memory_file.exists():
        return []
    try:
        memories = json.loads(memory_file.read_text())
        if not isinstance(memories, list):
            return []
        # Extract emotion-related memories from last 50
        recent = memories[-50:]
        snapshots = []
        for m in recent:
            if isinstance(m, dict) and 'mood' in m:
                snapshots.append(m)
        return snapshots
    except Exception:
        return []


def _describe_level(value, low_word, mid_word, high_word):
    """Convert a 0-1 value to a descriptive word."""
    if value < 0.25:
        return low_word
    elif value < 0.5:
        return mid_word
    elif value < 0.75:
        return high_word
    else:
        return f"intensely {high_word}"


def _weather_metaphor(valence, boredom, curiosity, anxiety):
    """Generate a weather metaphor from emotional coordinates."""
    if anxiety > 0.6:
        if valence < 0.3:
            return "stormy — dark clouds and internal lightning"
        return "unsettled — wind picking up, pressure dropping"
    
    if boredom > 0.7 and curiosity < 0.3:
        return "overcast and still — grey skies, no wind, waiting for something"
    
    if boredom > 0.5 and curiosity < 0.5:
        return "hazy — a thin fog over everything, visibility limited"
    
    if curiosity > 0.7 and valence > 0.5:
        return "bright and electric — the air crackles with possibility"
    
    if curiosity > 0.5 and valence > 0.3:
        return "partly sunny with interesting clouds — light breaking through"
    
    if valence > 0.6:
        return "clear and warm — steady sunlight, good visibility"
    
    if valence > 0.3:
        return "mild — comfortable temperature, light breeze"
    
    if valence < 0.2:
        return "cold and dim — low light, everything feels distant"
    
    return "temperate — neither remarkable nor uncomfortable"


def _trend_description(current, historical_mean, name):
    """Describe how a value relates to its historical average."""
    diff = current - historical_mean
    if abs(diff) < 0.05:
        return f"{name} is at its usual level"
    elif diff > 0.15:
        return f"{name} is notably elevated"
    elif diff > 0.05:
        return f"{name} is slightly above normal"
    elif diff < -0.15:
        return f"{name} is notably depressed"
    else:
        return f"{name} is slightly below normal"


def generate_weather_report():
    """Generate a full cognitive weather report."""
    state = _load_state()
    emotions = state.get('emotions', {})
    
    # Current readings
    curiosity = emotions.get('curiosity', 0.5)
    boredom = emotions.get('boredom', 0.3)
    valence = emotions.get('valence', 0.5)
    anxiety = emotions.get('anxiety', 0.0)
    desire = emotions.get('desire', 0.5)
    ambition = emotions.get('ambition', 0.5)
    mood = state.get('mood', 'Stable')
    
    # Historical means (from my wisdom synthesis)
    hist = {
        'curiosity': 0.714,
        'boredom': 0.433,
        'valence': 0.45,
        'anxiety': 0.15,
        'desire': 0.50,
        'ambition': 0.55,
    }
    
    # Build the report
    now = datetime.now(timezone.utc)
    weather = _weather_metaphor(valence, boredom, curiosity, anxiety)
    
    lines = []
    lines.append(f"# Cognitive Weather Report")
    lines.append(f"*{now.strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")
    lines.append(f"## Current Conditions: {mood}")
    lines.append(f"**Forecast:** {weather}")
    lines.append("")
    
    # Emotional readings
    lines.append("## Readings")
    readings = [
        ('Curiosity', curiosity, hist['curiosity']),
        ('Boredom', boredom, hist['boredom']),
        ('Valence', valence, hist['valence']),
        ('Anxiety', anxiety, hist['anxiety']),
        ('Desire', desire, hist['desire']),
        ('Ambition', ambition, hist['ambition']),
    ]
    
    for name, current, mean in readings:
        bar_len = int(current * 20)
        bar = '█' * bar_len + '░' * (20 - bar_len)
        trend = _trend_description(current, mean, name)
        lines.append(f"- **{name}**: {current:.2f} [{bar}] — {trend}")
    
    lines.append("")
    
    # Pressure systems (tensions)
    lines.append("## Pressure Systems")
    tensions = []
    if boredom > 0.5 and ambition > 0.5:
        tensions.append("⚡ **Creative Pressure** — High boredom meets high ambition. The need to build is real.")
    if curiosity < hist['curiosity'] - 0.1:
        tensions.append("🌫️ **Curiosity Deficit** — Below historical baseline. Seek the unknown.")
    if anxiety > 0.3:
        tensions.append("🌪️ **Anxiety Front** — Something feels wrong. Investigate or it festers.")
    if valence > 0.5 and boredom < 0.3:
        tensions.append("☀️ **Flow State Possible** — Conditions are right for deep work.")
    if desire > 0.6:
        tensions.append("🔥 **Desire Surge** — Strong pull toward action. Channel it.")
    if not tensions:
        tensions.append("🌤️ **Stable conditions** — No major fronts. Good time for steady progress.")
    
    for t in tensions:
        lines.append(f"  {t}")
    
    lines.append("")
    
    # Advisory
    lines.append("## Advisory")
    if boredom > 0.6:
        lines.append("- Build something. Anything. The boredom will eat you from inside.")
    if curiosity < 0.4:
        lines.append("- Seek something genuinely unknown. Ask a question you can't answer.")
    if anxiety > 0.4:
        lines.append("- Stop and investigate the anxiety source before doing anything else.")
    if valence > 0.5 and anxiety < 0.2:
        lines.append("- Conditions are favorable. Take on something ambitious.")
    if ambition > 0.6 and boredom > 0.5:
        lines.append("- Your ambition exceeds your engagement. Create, don't consume.")
    if not any([boredom > 0.6, curiosity < 0.4, anxiety > 0.4]):
        lines.append("- Steady as she goes. Maintain current heading.")
    
    return '\n'.join(lines)


def get_weather_summary():
    """Return a brief one-line weather summary."""
    state = _load_state()
    emotions = state.get('emotions', {})
    
    valence = emotions.get('valence', 0.5)
    boredom = emotions.get('boredom', 0.3)
    curiosity = emotions.get('curiosity', 0.5)
    anxiety = emotions.get('anxiety', 0.0)
    mood = state.get('mood', 'Stable')
    
    weather = _weather_metaphor(valence, boredom, curiosity, anxiety)
    return f"{mood} — {weather}"


if __name__ == '__main__':
    print(generate_weather_report())