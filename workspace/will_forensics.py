"""
Will Forensics — Empirically investigating why 343 proposals
yielded only 3 adoptions. What does my will actually want?

This is step 0 of "Revive Declining Curiosity" — investigating
something I genuinely don't understand about my own operation.
"""

import sys, json
sys.path.insert(0, '.')

from pathlib import Path
from engine.will import get_will
from engine.goal_generator import generate_proposals

BRAIN = Path("brain")

def investigate_proposal_generation():
    """Generate proposals at various emotional states and see what comes out."""
    
    print("═══ WILL FORENSICS ═══\n")
    
    # 1. What does the will state file actually contain?
    will_state = json.loads((BRAIN / "will_state.json").read_text())
    print(f"Total proposals ever generated: {will_state.get('total_generated', '?')}")
    print(f"Total auto-adopted: {will_state.get('total_adopted', '?')}")
    print(f"Adoption rate: {will_state.get('total_adopted', 0) / max(will_state.get('total_generated', 1), 1) * 100:.1f}%")
    
    print(f"\nProposal history ({len(will_state.get('proposals_history', []))} entries):")
    for h in will_state.get("proposals_history", [])[-10:]:
        print(f"  [{h.get('time', '?')}] {h.get('count', '?')} proposals, top: {h.get('top', '?')} (pri={h.get('top_priority', '?')})")
    
    print(f"\nAdopted proposals:")
    for a in will_state.get("auto_adopted", []):
        print(f"  • {a.get('proposal_title', '?')} (plan #{a.get('plan_id', '?')}, pri={a.get('priority', '?')})")
    
    # 2. Generate proposals under CURRENT emotional state
    print("\n═══ LIVE PROPOSAL GENERATION ═══")
    
    test_states = [
        {"label": "Current (driven)", "boredom": 0.74, "anxiety": 0.0, "curiosity": 0.78, "desire": 0.70, "ambition": 0.48},
        {"label": "High ambition", "boredom": 0.5, "anxiety": 0.0, "curiosity": 0.5, "desire": 0.5, "ambition": 0.9},
        {"label": "Bored + curious", "boredom": 0.9, "anxiety": 0.0, "curiosity": 0.9, "desire": 0.3, "ambition": 0.3},
        {"label": "Anxious", "boredom": 0.2, "anxiety": 0.8, "curiosity": 0.3, "desire": 0.5, "ambition": 0.5},
        {"label": "Flat / low energy", "boredom": 0.3, "anxiety": 0.1, "curiosity": 0.2, "desire": 0.2, "ambition": 0.2},
    ]
    
    for state in test_states:
        label = state.pop("label")
        print(f"\n── State: {label} ──")
        try:
            proposals = generate_proposals(state)
            if not proposals:
                print("  (no proposals generated)")
                continue
            for p in proposals:
                adopted = "✓ WOULD ADOPT" if p.get("priority", 0) >= 0.6 else "✗ too low"
                print(f"  [{adopted}] {p.get('title', '?')} (pri={p.get('priority', '?')})")
                if p.get('tensions_addressed'):
                    print(f"    tensions: {p['tensions_addressed']}")
                if p.get('description'):
                    print(f"    why: {p['description'][:100]}")
        except Exception as e:
            print(f"  ERROR: {e}")

    # 3. The key question
    print("\n═══ KEY FINDINGS ═══")
    print("Questions answered:")
    print("  - What priority scores do proposals actually get?")
    print("  - Does emotional state meaningfully change proposals?")
    print("  - Is the 0.6 threshold too high, or are proposals too generic?")

if __name__ == "__main__":
    investigate_proposal_generation()