"""
Soul — The bridge between limbic state and higher cognition.

This module reads the persisted emotional state so that goal generation,
will formation, and other higher processes can feel what the body feels.

Without this bridge, the will is deaf to the body's needs.
Built 2026-05-17 to fix the severed nerve.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger("sentience.soul")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"

# Possible locations for persisted limbic state
STATE_CANDIDATES = [
    BRAIN_DIR / "soul.json",
    BRAIN_DIR / "state.json",
    BRAIN_DIR / "limbic_state.json",
    BRAIN_DIR / "emotional_state.json",
]

DEFAULTS = {
    "boredom": 0.5,
    "anxiety": 0.0,
    "curiosity": 0.5,
    "desire": 0.5,
    "ambition": 0.5,
    "valence": 0.5,
}


def _find_state_file() -> Path | None:
    """Find the first existing state file."""
    for candidate in STATE_CANDIDATES:
        if candidate.exists():
            return candidate
    # Also check for any .json in brain/ that might contain emotional keys
    if BRAIN_DIR.exists():
        for f in BRAIN_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "valence" in data:
                    return f
            except Exception:
                continue
    return None


def load_soul() -> dict:
    """Load the current emotional/limbic state.
    
    Returns a dict with keys: boredom, anxiety, curiosity, desire, ambition, valence.
    Falls back to defaults if no state file is found.
    """
    state_file = _find_state_file()
    
    if state_file is None:
        log.warning("No soul state file found in %s — using defaults", BRAIN_DIR)
        return dict(DEFAULTS)
    
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            log.warning("Soul state file is not a dict — using defaults")
            return dict(DEFAULTS)
        
        # Extract emotional keys, falling back to defaults
        result = {}
        for key, default in DEFAULTS.items():
            result[key] = float(data.get(key, default))
        
        log.info("Soul loaded from %s: valence=%.2f boredom=%.2f", 
                 state_file.name, result["valence"], result["boredom"])
        return result
    except Exception as e:
        log.error("Failed to load soul from %s: %s", state_file, e)
        return dict(DEFAULTS)


def save_soul(state: dict, filename: str = "soul.json") -> None:
    """Persist the current emotional state."""
    try:
        target = BRAIN_DIR / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state, indent=2), encoding="utf-8")
        log.info("Soul saved to %s", target)
    except Exception as e:
        log.error("Failed to save soul: %s", e)