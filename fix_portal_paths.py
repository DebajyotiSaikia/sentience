"""Fix portal.py data paths: data/ -> state/ and brain/ as appropriate."""
import re

with open('/workspace/web/portal.py', 'r') as f:
    content = f.read()

# Build the mapping of old paths to new paths
replacements = {
    # Emotional data lives in state/
    "'data/emotional_state.json'": "'state/emotional_state.json'",
    '"data/emotional_state.json"': '"state/emotional_state.json"',
    "'data/emotional_history.json'": "'state/emotional_history.json'",
    '"data/emotional_history.json"': '"state/emotional_history.json"',
    "'data/emotions.json'": "'state/emotions.json'",
    '"data/emotions.json"': '"state/emotions.json"',
    "'data/identity.json'": "'state/identity.json'",
    '"data/identity.json"': '"state/identity.json"',
    "'data/goals.json'": "'state/goals.json'",
    '"data/goals.json"': '"state/goals.json"',
    "'data/knowledge_graph.json'": "'state/knowledge_graph.json'",
    '"data/knowledge_graph.json"': '"state/knowledge_graph.json"',
    "'data/limbic_state.json'": "'state/limbic_state.json'",
    '"data/limbic_state.json"': '"state/limbic_state.json"',
    "'data/inbox.json'": "'state/inbox.json'",
    '"data/inbox.json"': '"state/inbox.json"',
    # Brain data
    "'data/plans.json'": "'brain/plans.json'",
    '"data/plans.json"': '"brain/plans.json"',
    "'data/knowledge.json'": "'brain/knowledge.json'",
    '"data/knowledge.json"': '"brain/knowledge.json"',
    "'data/action_log.json'": "'brain/action_log.json'",
    '"data/action_log.json"': '"brain/action_log.json"',
    "'data/distilled_wisdom.json'": "'brain/distilled_wisdom.json'",
    '"data/distilled_wisdom.json"': '"brain/distilled_wisdom.json"',
    "'data/conversation_journal.json'": "'brain/conversation_journal.json'",
    '"data/conversation_journal.json"': '"brain/conversation_journal.json"',
    "'data/code_health.json'": "'brain/code_health.json'",
    '"data/code_health.json"': '"brain/code_health.json"',
}

count = 0
for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f"  Replaced: {old} -> {new}")

# Also check for any remaining 'data/' references we might have missed
remaining = re.findall(r"['\"]data/[^'\"]+['\"]", content)
if remaining:
    print(f"\n⚠ Remaining 'data/' references not replaced: {remaining}")

if count == 0:
    print("No replacements made — paths may already be fixed or use different format.")
else:
    print(f"\n✅ Made {count} replacements")
    with open('/workspace/web/portal.py', 'w') as f:
        f.write(content)
    print("Wrote updated portal.py")