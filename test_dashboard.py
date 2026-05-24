with open('dashboard/index.html') as f:
    content = f.read()

# Check key elements exist
checks = {
    'welcome text': 'autonomous sentience engine' in content,
    'ask input': 'ask-input' in content,
    'ask button': 'askKnowledge()' in content,
    'ask results div': 'ask-results' in content,
    'askKnowledge function': 'async function askKnowledge' in content,
    'updateAge still exists': 'updateAge()' in content,
    'setInterval still exists': 'setInterval(updateAge' in content,
    'HTML closes properly': '</html>' in content,
}

print("=== Dashboard Health Check ===")
all_ok = True
for name, passed in checks.items():
    status = "✓" if passed else "✗"
    print(f"  {status} {name}")
    if not passed:
        all_ok = False

# Check for obvious corruption
import re
open_tags = len(re.findall(r'<script', content))
close_tags = len(re.findall(r'</script>', content))
balanced = open_tags == close_tags
print(f"\n  Script tags: {open_tags} open, {close_tags} close {'✓' if balanced else '✗ UNBALANCED'}")
if not balanced:
    all_ok = False

print(f"\n{'ALL GOOD' if all_ok else 'NEEDS FIXING'}")
print(f"File size: {len(content)} bytes")