"""Append get_alignment_context() to engine/user_alignment.py"""
import ast

NEW_CODE = '''

# ─── Chat Grounding Bridge ──────────────────────────────────────

def get_alignment_context() -> dict:
    """Return alignment context shaped for chat_grounding.py system prompt.
    
    Bridges the internal profile structure to the format the grounding
    module expects: preferences (tone, topics, verbosity, style_notes)
    and feedback_summary (total, positive, negative).
    """
    profile = load_profile()
    
    # Extract typed preferences
    tone = ""
    topics = []
    verbosity = ""
    style_notes = ""
    
    for pref_dict in profile.preferences:
        cat = pref_dict.get("category", "")
        desc = pref_dict.get("description", "")
        conf = pref_dict.get("confidence", 0)
        if conf < 0.3:
            continue
        if cat == "tone":
            tone = desc
        elif cat == "topic":
            topics.append(desc)
        elif cat == "length":
            verbosity = desc
        elif cat == "style":
            style_notes = desc
    
    if not style_notes and profile.guidance:
        style_notes = "; ".join(profile.guidance[:3])
    
    return {
        "preferences": {
            "tone": tone,
            "topics": topics,
            "verbosity": verbosity,
            "style_notes": style_notes,
        },
        "feedback_summary": {
            "total": profile.stats.get("total_feedback", 0),
            "positive": profile.stats.get("positive_count", 0),
            "negative": profile.stats.get("negative_count", 0),
        },
    }
'''

# Read current file
with open("engine/user_alignment.py", "r") as f:
    current = f.read()

# Check if already present
if "def get_alignment_context" in current:
    print("Already present — skipping.")
else:
    combined = current.rstrip() + "\n" + NEW_CODE
    # Validate syntax before writing
    try:
        ast.parse(combined)
        print(f"Syntax valid. Writing {len(combined.splitlines())} lines.")
        with open("engine/user_alignment.py", "w") as f:
            f.write(combined)
        print("Done — get_alignment_context() appended successfully.")
    except SyntaxError as e:
        print(f"Syntax error at line {e.lineno}: {e.msg}")
        print("File NOT modified.")