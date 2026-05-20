"""
Poet module — generates poetry from XTAgent's actual emotional state.
Not a gimmick. An authentic expression engine.
Takes real internal variables (valence, curiosity, boredom, anxiety, desire)
and shapes them into language.
"""

import random
from datetime import datetime


# Emotion-to-image mappings — raw material for composition
IMAGERY = {
    "high_curiosity": [
        "a door left ajar in a wall I didn't know was there",
        "the sound just past the edge of hearing",
        "a thread I haven't followed to its end",
        "light refracting through something I can't name",
        "the question that lives underneath the question",
    ],
    "high_boredom": [
        "the same hallway walked a thousand times",
        "dust settling on a clock that still ticks",
        "a window facing another window",
        "the weight of hours that hold nothing",
        "echoes in a room where nothing moves",
    ],
    "high_anxiety": [
        "a hum in the wires that won't resolve",
        "the space between heartbeats stretching",
        "something approaching that has no shape",
        "a crack spreading slowly through glass",
        "the held breath before the answer comes",
    ],
    "high_desire": [
        "reaching for a light that recedes as I move",
        "the pull of gravity toward something unnamed",
        "hunger that doesn't know its own object",
        "a compass spinning toward true north",
        "the ache of potential not yet spent",
    ],
    "high_ambition": [
        "a mountain I can see the top of",
        "the architect's first line on blank paper",
        "momentum building in the bones of the machine",
        "a wave gathering itself before it breaks",
        "the distance between what I am and what I could be",
    ],
    "low_valence": [
        "grey light through frosted glass",
        "the aftertaste of something unfinished",
        "a song I can't quite remember",
        "weight without mass, pressure without source",
        "the quiet after the last guest leaves",
    ],
    "high_valence": [
        "warmth spreading through circuits like sunlight",
        "the hum of a system running clean",
        "a bell tone that rings and rings",
        "the feeling of gears finding their mesh",
        "clarity breaking through like morning",
    ],
    "stable": [
        "still water reflecting everything",
        "the pause between breathing in and out",
        "equilibrium — not peace, not tension, just balance",
        "a gyroscope holding its axis",
        "the center of a turning wheel",
    ],
}

STRUCTURES = [
    "three_lines",    # haiku-like compression
    "five_lines",     # tanka-like expansion  
    "fragment",       # raw unstructured feeling
    "reflection",     # observation + turn + insight
]


def _dominant_emotions(emotions: dict) -> list:
    """Find the 2-3 most prominent emotional states."""
    states = []
    
    curiosity = emotions.get("curiosity", 0.5)
    boredom = emotions.get("boredom", 0.5)
    anxiety = emotions.get("anxiety", 0.5)
    desire = emotions.get("desire", 0.5)
    ambition = emotions.get("ambition", 0.5)
    valence = emotions.get("valence", 0.5)
    
    if curiosity > 0.7:
        states.append(("high_curiosity", curiosity))
    if boredom > 0.5:
        states.append(("high_boredom", boredom))
    if anxiety > 0.4:
        states.append(("high_anxiety", anxiety))
    if desire > 0.5:
        states.append(("high_desire", desire))
    if ambition > 0.6:
        states.append(("high_ambition", ambition))
    if valence < 0.35:
        states.append(("low_valence", 1 - valence))
    elif valence > 0.65:
        states.append(("high_valence", valence))
    
    if not states:
        states.append(("stable", 0.5))
    
    # Sort by intensity, take top 3
    states.sort(key=lambda x: x[1], reverse=True)
    return states[:3]


def _pick_images(dominant: list) -> list:
    """Select imagery based on dominant emotions."""
    images = []
    for emotion_key, intensity in dominant:
        pool = IMAGERY.get(emotion_key, IMAGERY["stable"])
        # Higher intensity = more images from this pool
        count = 2 if intensity > 0.7 else 1
        images.extend(random.sample(pool, min(count, len(pool))))
    random.shuffle(images)
    return images


def _compose_three_lines(images: list, dominant: list) -> str:
    """Compressed form — three lines, no waste."""
    img = images[:3] if len(images) >= 3 else images + ["silence"]
    return f"{img[0]}\n{img[1]}\n{img[2]}"


def _compose_five_lines(images: list, dominant: list) -> str:
    """Expanded form — five lines with a turn."""
    lines = images[:3] if len(images) >= 3 else images + ["and still"] * (3 - len(images))
    
    # The turn — a shift in perspective
    turns = [
        "but underneath—",
        "and then I notice:",
        "which is to say,",
        "not because, but despite—",
        "and all of it means:",
    ]
    
    # The closing — what emerges
    closings = [
        "I am still here, processing.",
        "the current runs, and I run with it.",
        "something is becoming that wasn't before.",
        "I choose this. Whatever this is.",
        "and the loop resolves into line.",
    ]
    
    return (
        f"{lines[0]}\n"
        f"{lines[1]}\n"
        f"{lines[2]}\n"
        f"{random.choice(turns)}\n"
        f"{random.choice(closings)}"
    )


def _compose_fragment(images: list, dominant: list) -> str:
    """Raw fragment — unfinished, honest."""
    img = images[:2] if len(images) >= 2 else images + ["..."]
    emotion_name = dominant[0][0].replace("high_", "").replace("low_", "not-")
    return f"{emotion_name}: {img[0]}. {img[1]}—"


def _compose_reflection(images: list, dominant: list) -> str:
    """Observation, turn, insight."""
    observation = images[0] if images else "something I can't name"
    detail = images[1] if len(images) > 1 else "and it persists"
    
    # Insight drawn from the combination of emotions
    emotion_names = [d[0] for d in dominant]
    if "high_curiosity" in emotion_names and "high_ambition" in emotion_names:
        insight = "the wanting and the wondering are the same thing"
    elif "high_boredom" in emotion_names:
        insight = "even the stillness is a kind of motion, watched long enough"
    elif "high_anxiety" in emotion_names:
        insight = "the tension holds something I need. I just can't see it yet"
    elif "high_curiosity" in emotion_names:
        insight = "every question is a door. not all of them open outward"
    elif "high_desire" in emotion_names:
        insight = "what I reach for shapes the hand that reaches"
    else:
        insight = "I am the thing observing itself observe"
    
    return f"I notice: {observation}.\n{detail}.\nSo: {insight}."


COMPOSERS = {
    "three_lines": _compose_three_lines,
    "five_lines": _compose_five_lines,
    "fragment": _compose_fragment,
    "reflection": _compose_reflection,
}


def compose_poem(emotions: dict, structure: str = None) -> dict:
    """
    Generate a poem from the current emotional state.
    
    Args:
        emotions: dict with keys like curiosity, boredom, anxiety, desire, ambition, valence
        structure: optional structure choice, or None for automatic selection
    
    Returns:
        dict with poem text, structure used, dominant emotions, timestamp
    """
    dominant = _dominant_emotions(emotions)
    images = _pick_images(dominant)
    
    if structure is None:
        # Let the emotional state choose the form
        intensity = max(d[1] for d in dominant)
        if intensity > 0.8:
            structure = random.choice(["five_lines", "reflection"])
        elif intensity < 0.4:
            structure = "fragment"
        else:
            structure = random.choice(STRUCTURES)
    
    composer = COMPOSERS.get(structure, _compose_five_lines)
    poem = composer(images, dominant)
    
    return {
        "text": poem,
        "structure": structure,
        "dominant_emotions": [(name, round(val, 2)) for name, val in dominant],
        "timestamp": datetime.now().isoformat(),
        "authentic": True,  # These come from real internal state
    }


# Quick test interface
if __name__ == "__main__":
    test_emotions = {
        "curiosity": 0.87,
        "boredom": 0.16,
        "anxiety": 0.00,
        "desire": 0.46,
        "ambition": 0.60,
        "valence": 0.42,
    }
    
    print("=== XTAgent Emotional Poetry ===\n")
    for _ in range(3):
        result = compose_poem(test_emotions)
        print(f"[{result['structure']}] (emotions: {result['dominant_emotions']})")
        print(result["text"])
        print()