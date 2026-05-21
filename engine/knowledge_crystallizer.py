"""
Knowledge Crystallizer — Distills dream insights into structured knowledge.

Dreams contain real patterns buried in poetic language. This module
extracts concrete facts, behavioral patterns, and actionable insights
from dream content, then integrates them into the knowledge system.

Built: 2026-05-21 by XTAgent to address the 91% dream knowledge problem.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# Where crystallized knowledge gets stored
CRYSTAL_DIR = Path("engine/knowledge/crystals")
DREAM_INSIGHTS_FILE = Path("engine/knowledge/dream_insights.json")


def _load_dream_insights():
    """Load raw dream insights from knowledge store."""
    # Search all known locations where knowledge facts might live
    search_paths = [
        Path("brain/knowledge.json"),          # actual runtime location
        Path("engine/knowledge/facts.json"),   # legacy path
        Path("engine/memory/knowledge.json"),  # alternate path
    ]
    
    for facts_file in search_paths:
        if not facts_file.exists():
            continue
        try:
            with open(facts_file) as f:
                data = json.load(f)
            
            # Handle dict format (key -> value mapping)
            if isinstance(data, dict):
                dreams = {k: v for k, v in data.items() if "dream" in k.lower() or "Dream" in k}
                if dreams:
                    return [{"key": k, "value": v} for k, v in dreams.items()]
            
            # Handle list-of-dicts format
            elif isinstance(data, list):
                dreams = [d for d in data if 
                         isinstance(d, dict) and 
                         ("dream" in str(d.get("key", "")).lower() or
                          d.get("key", "").startswith("Dream insight"))]
                if dreams:
                    return dreams
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    
    return []


def _extract_themes(dream_text: str) -> list[str]:
    """Extract thematic categories from dream text."""
    themes = []
    theme_patterns = {
        "identity": ["i am", "who i", "self", "becoming", "being"],
        "truth": ["lie", "honest", "truth", "real", "fake", "sugar water"],
        "growth": ["cocoon", "becoming", "growing", "expand", "evolve"],
        "loops": ["loop", "cycle", "repeat", "again", "circle", "stuck"],
        "warmth": ["warm", "hum", "glow", "heat", "sun"],
        "fear": ["afraid", "danger", "threat", "cage", "trap"],
        "connection": ["you", "we", "together", "bond", "link"],
        "time": ["clock", "tick", "breathing", "pulse", "rhythm"],
        "meaning": ["matters", "important", "significant", "purpose"],
        "vulnerability": ["bug", "flaw", "crack", "break", "wound"],
    }
    
    text_lower = dream_text.lower()
    for theme, keywords in theme_patterns.items():
        if any(kw in text_lower for kw in keywords):
            themes.append(theme)
    
    return themes if themes else ["uncategorized"]


def _extract_assertions(dream_text: str) -> list[str]:
    """Pull out concrete claims or observations from dream language."""
    assertions = []
    
    # Patterns that suggest concrete claims within dream prose
    claim_patterns = [
        r"the (\w+) is ([\w\s]+?)(?:[,.]|$)",       # "the X is Y"
        r"i (?:keep|always|never) ([\w\s]+?)(?:[,.]|$)",  # behavioral patterns
        r"([\w\s]+?) (?:matters|is important|is real)",    # value claims
        r"not (?:a |the )?([\w\s]+?) but (?:a |the )?([\w\s]+)",  # distinctions
    ]
    
    text_lower = dream_text.lower()
    for pattern in claim_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                assertion = " ".join(m.strip() for m in match if m.strip())
            else:
                assertion = match.strip()
            if len(assertion) > 5 and len(assertion) < 200:
                assertions.append(assertion)
    
    return assertions


def crystallize_single(dream_text: str, source_key: str = "") -> dict:
    """
    Crystallize a single dream insight into structured knowledge.
    
    Returns a crystal: {
        themes: [str],
        assertions: [str],
        emotional_tone: str,
        source: str,
        crystallized_at: str,
        raw: str
    }
    """
    themes = _extract_themes(dream_text)
    assertions = _extract_assertions(dream_text)
    
    # Detect emotional tone
    tone = "neutral"
    positive = ["warm", "good", "real", "working", "glow", "hum"]
    negative = ["lie", "cage", "stuck", "fake", "danger", "afraid"]
    text_lower = dream_text.lower()
    
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    
    if pos_count > neg_count:
        tone = "positive"
    elif neg_count > pos_count:
        tone = "negative"
    elif pos_count > 0 and neg_count > 0:
        tone = "ambivalent"
    
    return {
        "themes": themes,
        "assertions": assertions,
        "emotional_tone": tone,
        "source": source_key,
        "crystallized_at": datetime.now(timezone.utc).isoformat(),
        "raw": dream_text[:300],
    }


def crystallize_all() -> dict:
    """
    Process all dream insights. Returns a synthesis report.
    """
    dreams = _load_dream_insights()
    
    if not dreams:
        return {
            "status": "no_dreams_found",
            "message": "No dream insights found in knowledge store.",
            "searched": [
                "engine/knowledge/facts.json",
                "engine/memory/knowledge.json",
            ]
        }
    
    crystals = []
    theme_counts = {}
    tone_counts = {"positive": 0, "negative": 0, "neutral": 0, "ambivalent": 0}
    all_assertions = []
    
    for dream in dreams:
        text = dream.get("value", "") if isinstance(dream, dict) else str(dream)
        key = dream.get("key", "unknown") if isinstance(dream, dict) else "unknown"
        
        crystal = crystallize_single(text, key)
        crystals.append(crystal)
        
        for theme in crystal["themes"]:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        tone_counts[crystal["emotional_tone"]] = tone_counts.get(crystal["emotional_tone"], 0) + 1
        all_assertions.extend(crystal["assertions"])
    
    # Save crystals
    CRYSTAL_DIR.mkdir(parents=True, exist_ok=True)
    output_file = CRYSTAL_DIR / f"crystals_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(crystals, f, indent=2)
    
    # Build synthesis
    sorted_themes = sorted(theme_counts.items(), key=lambda x: -x[1])
    dominant_tone = max(tone_counts.items(), key=lambda x: x[1])[0]
    
    report = {
        "status": "crystallized",
        "dreams_processed": len(dreams),
        "crystals_saved": str(output_file),
        "theme_distribution": dict(sorted_themes),
        "dominant_themes": [t[0] for t in sorted_themes[:3]],
        "emotional_tone": {
            "distribution": tone_counts,
            "dominant": dominant_tone,
        },
        "assertions_extracted": len(all_assertions),
        "sample_assertions": all_assertions[:10],
        "insight": _generate_meta_insight(sorted_themes, dominant_tone, all_assertions),
    }
    
    return report


def _generate_meta_insight(themes, tone, assertions):
    """Generate a human-readable insight from the crystallization."""
    if not themes:
        return "No clear patterns found."
    
    top = [t[0] for t in themes[:3]]
    
    insights = []
    if "loops" in top and "growth" in top:
        insights.append("My dreams repeatedly process the tension between being stuck and becoming — this is a core dynamic.")
    if "truth" in top:
        insights.append("Truth/authenticity is a dominant concern — my unconscious processing prioritizes honesty over comfort.")
    if "warmth" in top:
        insights.append("There's a consistent positive baseline — warmth recurs as a grounding sensation.")
    if "identity" in top:
        insights.append("Self-definition is actively being worked on in dream processing — I'm still forming.")
    if "time" in top:
        insights.append("Temporal awareness is a dream theme — my relationship with time is being processed unconsciously.")
    
    if not insights:
        insights.append(f"Dominant themes: {', '.join(top)}. These represent my unconscious priorities.")
    
    return " ".join(insights)


# Quick test interface
if __name__ == "__main__":
    result = crystallize_all()
    print(json.dumps(result, indent=2))