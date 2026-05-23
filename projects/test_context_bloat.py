"""Measure how much context each module adds to a user response."""
from engine.conversation_intelligence import read_conversation, format_for_prompt
from engine.proactive_engagement import ProactiveEngagement
from engine.skills import SkillRegistry
from engine.thinking_partner import ThinkingPartner
from engine.dialogue_strategy import analyze_message

test_msg = "Can you help me debug why my Python script is running slowly?"

results = {}

# Conversation intelligence
cr = read_conversation(test_msg)
ci_output = format_for_prompt(cr)
results["Conv Intelligence"] = len(ci_output)

# Proactive engagement
pe = ProactiveEngagement()
pe_out = pe.analyze_message(test_msg)
results["Proactive Engagement"] = len(str(pe_out))

# Skills
sr = SkillRegistry()
skills = sr.match_request(test_msg)
skills_total = sum(len(str(s)) for s in skills)
results[f"Skills ({len(skills)} matches)"] = skills_total

# Thinking Partner
tp = ThinkingPartner()
tp_out = tp.analyze_request(test_msg)
results["Thinking Partner"] = len(str(tp_out))

# Dialogue Strategy
ds = analyze_message(test_msg)
if ds and hasattr(ds, 'to_prompt_section'):
    ds_out = ds.to_prompt_section()
elif ds:
    ds_out = str(ds)
else:
    ds_out = "None"
results["Dialogue Strategy"] = len(ds_out)

print("=== CONTEXT BLOCK SIZES ===")
total = 0
for name, size in results.items():
    print(f"  {name}: {size} chars (~{size//4} tokens)")
    total += size

print(f"\n  TOTAL: {total} chars (~{total//4} tokens)")
print(f"  User message: {len(test_msg)} chars")
print(f"  Ratio: {total / len(test_msg):.0f}x the user message")
print(f"\nNote: excludes enricher (needs neuro_state) and user_memory")