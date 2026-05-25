"""Quick validation of portal.html"""
with open('web/templates/portal.html') as f:
    content = f.read()

# Basic checks
assert '<html' in content, "Missing html tag"
assert '</html>' in content, "Missing closing html tag"
assert '<body' in content, "Missing body tag"
assert '</body>' in content, "Missing closing body tag"

# Count open/close tags for balance
opens = content.count('<script')
closes = content.count('</script>')
print(f"Script tags: {opens} open, {closes} close")
assert opens == closes, f"Unbalanced script tags: {opens} != {closes}"

opens = content.count('<style')
closes = content.count('</style>')
print(f"Style tags: {opens} open, {closes} close")
assert opens == closes, f"Unbalanced style tags: {opens} != {closes}"

# Check for the new features I added
has_suggestions = 'suggestion-chip' in content
has_welcome = 'welcome-banner' in content
print(f"Suggestion chips: {has_suggestions}")
print(f"Welcome banner: {has_welcome}")

lines = content.split('\n')
print(f"Total lines: {len(lines)}")
print("✓ Portal validation passed")