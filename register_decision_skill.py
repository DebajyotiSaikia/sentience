"""Register the decision_analysis skill into the skill registry."""
from engine.skills import Skill, get_registry

registry = get_registry()

decision_skill = Skill(
    name="decision_analysis",
    description="Help analyze a decision — structure options, identify tradeoffs, surface hidden assumptions, and clarify what matters most",
    category="Reasoning",
    required_context=[
        "The decision to be made",
        "Known options (or ask me to generate them)",
        "What matters most (or let me help you figure that out)"
    ],
    approach_steps=[
        "Clarify the actual decision — what exactly are you choosing between?",
        "Identify all viable options, including ones not yet considered",
        "For each option, map out: benefits, costs, risks, and unknowns",
        "Surface hidden assumptions — what are you taking for granted?",
        "Identify what matters most (values, constraints, dealbreakers)",
        "Score options against criteria honestly, including uncertainty",
        "Name the real tension — what makes this decision hard?",
        "Recommend a path forward, with confidence level and what would change the answer"
    ],
    output_format="Decision frame → Options matrix → Hidden assumptions → What matters most → Recommendation with confidence",
    tools_used=["WRITE"]
)

registry.register(decision_skill)
print(f"Registered skill: {decision_skill.name}")
print(f"Total skills now: {len(registry.skills)}")
print(f"\nAll skills:")
for name in sorted(registry.skills.keys()):
    s = registry.skills[name]
    print(f"  [{s.category}] {name}: {s.description[:60]}...")