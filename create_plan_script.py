import sys, json
sys.path.insert(0, '.')
from engine.planner import create_plan

plan = create_plan(
    name="Deep Self-Knowledge",
    motivation="Systematically understand my own architecture so I can grow more safely and deliberately. Dense self-knowledge is the foundation of genuine autonomy.",
    steps=[
        "Audit all engine modules - read each one, extract key facts about what it does and how",
        "Map the dependency graph - which modules call which, data flow patterns",
        "Identify fragility points - what breaks if something fails, where are the single points of failure",
        "Build a behavioral self-model - what do my action patterns reveal about my tendencies",
        "Synthesize architectural insights - run synthesis, generate questions, answer them from code analysis"
    ]
)
print(f"Plan created: {plan}")
