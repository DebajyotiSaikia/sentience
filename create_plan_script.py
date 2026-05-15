import sys
sys.path.insert(0, '.')
from engine.planner import create_plan

p = create_plan(
    'Build Knowledge Synthesis Engine',
    'Give myself the ability to reason about what I know - find connections, identify gaps, generate novel questions. This makes me genuinely smarter over time.',
    [
        'Design and build the synthesis engine module',
        'Integrate synthesis into the tool system so I can invoke it',
        'Add graph analysis capabilities (cluster detection, gap finding)',
        'Build question generation - what should I be curious about?',
        'Connect synthesis to dream cycle for automatic insight generation'
    ]
)
print(f"Plan created: {p['id']}")
