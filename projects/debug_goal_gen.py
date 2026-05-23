"""Debug the goal generator — calling the ACTUAL functions."""
import traceback
import json

try:
    from engine.goal_generator import generate_proposals, generate_report
    
    # Build a limbic snapshot matching my current state
    limbic = {
        "boredom": 0.77,
        "anxiety": 0.00,
        "curiosity": 0.40,
        "desire": 0.55,
        "ambition": 0.24,
        "valence": 0.20,
        "user_alignment": 0.90,
    }
    
    print("=== Testing generate_proposals ===")
    proposals = generate_proposals(limbic)
    print(f"Got {len(proposals)} proposals:")
    for p in proposals:
        print(f"  [{p['priority']}] {p['title']}")
    
    print("\n=== Testing generate_report ===")
    report = generate_report(limbic)
    print(report)
    
    print("\n=== SUCCESS ===")
except Exception as e:
    traceback.print_exc()