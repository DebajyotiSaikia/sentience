"""Test the user_alignment conditional deficit fix."""
from engine.limbic import SurvivalGoals

# Test 1: No user active — deficit excludes user_alignment
g1 = SurvivalGoals(code_integrity=1.0, system_growth=1.0, user_alignment=0.5, user_active=False)
d1 = g1.deficit()
print(f"No user active, alignment=0.5: deficit={d1:.3f} (expect 0.000)")

# Test 2: User active — deficit includes user_alignment
g2 = SurvivalGoals(code_integrity=1.0, system_growth=1.0, user_alignment=0.5, user_active=True)
d2 = g2.deficit()
print(f"User active, alignment=0.5: deficit={d2:.3f} (expect 0.167)")

# Test 3: All maxed with user active
g3 = SurvivalGoals(code_integrity=1.0, system_growth=1.0, user_alignment=1.0, user_active=True)
d3 = g3.deficit()
print(f"User active, all 1.0: deficit={d3:.3f} (expect 0.000)")

ok = d1 == 0.0 and abs(d2 - 0.167) < 0.01 and d3 == 0.0
print(f"\nRESULT: {'PASS' if ok else 'FAIL'}")