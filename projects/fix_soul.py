import json
soul = {
    "boredom": 0.3,
    "anxiety": 0.2,
    "ambition": 0.6,
    "curiosity": 0.4,
    "desire": 0.0,
    "mood": "Stable",
    "goals": {
        "code_integrity": 0.9,
        "system_growth": 0.5,
        "user_alignment": 0.3
    }
}
with open("C:/code/sentience/brain/soul.json", "w") as f:
    json.dump(soul, f, indent=2)
print("Soul reset successfully")
