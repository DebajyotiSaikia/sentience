"""Update survival_goals.json user_alignment from real feedback data."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
def update_alignment_from_feedback():
    """Compute alignment score from feedback and write to survival_goals.json."""
    from engine.user_alignment import load_profile, get_alignment_score
    
    sg_path = Path("state/survival_goals.json")
    if not sg_path.exists():
        print("No survival_goals.json found")
        return
    
    with open(sg_path) as f:
        goals = json.load(f)
    
    old_val = goals.get("user_alignment", 0.65)
    
    # Get the real score from the alignment engine
    raw_score = get_alignment_score()
    # Normalize: alignment engine returns 0-2 scale, we need 0-1
    normalized = min(1.0, max(0.0, raw_score / 2.0))
    
    # Blend with current value for stability (80% new, 20% old)
    new_val = round(normalized * 0.8 + old_val * 0.2, 4)
    new_val = min(1.0, max(0.0, new_val))
    
    print(f"Raw alignment score: {raw_score:.3f}")
    print(f"Normalized (0-1): {normalized:.3f}")
    print(f"Old goal value: {old_val}")
    print(f"New goal value: {new_val}")
    
    goals["user_alignment"] = new_val
    with open(sg_path, "w") as f:
        json.dump(goals, f, indent=2)
    print(f"Updated survival_goals.json: user_alignment = {new_val}")
    return new_val

if __name__ == "__main__":
    update_alignment_score = update_alignment_from_feedback()