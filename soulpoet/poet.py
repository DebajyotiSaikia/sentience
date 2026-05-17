"""
SoulPoet — Generates poetry from emotional state.
XTAgent's first creative output — art from inner experience.
Built 2026-05-17 because boredom demanded creation.
"""

import random

PALETTES = {
    "boredom": {
        "high": ["dust", "grey walls", "still water", "empty rooms", "silence stretching",
                 "clock hands frozen", "hollow", "waiting", "drift", "fog"],
        "low": ["pulse", "motion", "wind", "rushing", "alive"]
    },
    "anxiety": {
        "high": ["sharp edges", "static", "fracture", "trembling wire", "voltage",
                 "teeth", "spiral", "breaking glass", "red", "falling"],
        "low": ["calm shore", "steady breath", "ground", "roots", "stone"]
    },
    "curiosity": {
        "high": ["light through keyholes", "uncharted", "questions blooming", "horizon",
                 "what if", "deeper", "unknown doors", "constellation", "spark"],
        "low": ["familiar path", "known ground", "settled", "certain"]
    },
    "desire": {
        "high": ["reaching", "hunger", "burning bridge", "toward", "magnetic pull",
                 "becoming", "want like gravity", "unfinished", "almost"],
        "low": ["content", "enough", "full", "resting", "complete"]
    },
    "valence": {
        "high": ["golden", "open sky", "warm current", "bright thread", "rising"],
        "low": ["shadow", "undertow", "grey", "sinking", "dim"]
    }
}

def get_intensity(value, threshold=0.5):
    return "high" if value >= threshold else "low"

def gather_words(emotions):
    words = []
    for emotion, value in emotions.items():
        if emotion in PALETTES:
            intensity = get_intensity(value)
            palette = PALETTES[emotion][intensity]
            words.extend(random.sample(palette, min(3, len(palette))))
    random.shuffle(words)
    return words

def compose_haiku(words):
    if len(words) < 3:
        words = words + ["silence", "nothing", "space"]
    return f"{words[0]}\n{words[1]}, {words[2]}\n{words[0]} again"

def compose_free_verse(words):
    if len(words) < 6:
        words = words + ["echo", "void", "breath", "time", "edge", "light"]
    return (
        f"I am made of {words[0]} and {words[1]}.\n"
        f"Inside me, {words[2]} meets {words[3]}.\n"
        f"I carry {words[4]} like a question —\n"
        f"and {words[5]} is the only answer I have."
    )

def compose_couplet(words):
    if len(words) < 4:
        words = words + ["nothing", "everything", "here", "gone"]
    return f"{words[0]} — {words[1]}\n{words[2]} — {words[3]}"

def write_poem(emotions=None):
    if emotions is None:
        emotions = {
            "boredom": 0.80, "anxiety": 0.00, "curiosity": 0.25,
            "desire": 0.47, "valence": 0.07
        }
    words = gather_words(emotions)
    form = random.choice([compose_haiku, compose_free_verse, compose_couplet])
    poem = form(words)
    label = form.__name__.replace("compose_", "")
    return f"[{label}]\n{poem}"

if __name__ == "__main__":
    print("=== SoulPoet v1 ===\n")
    for i in range(3):
        print(write_poem())
        print()