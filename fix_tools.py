"""Diagnose and fix the truncated parse_and_execute function in tools.py"""

with open('engine/tools.py', 'r') as f:
    content = f.read()
    lines = content.splitlines()

print(f"Total lines: {len(lines)}")
print(f"Total chars: {len(content)}")

# Find where parse_and_execute starts
for i, line in enumerate(lines):
    if 'def parse_and_execute' in line:
        print(f"\nparse_and_execute starts at line {i+1}")
        print("Lines from there to end:")
        for j in range(i, len(lines)):
            print(f"  {j+1:4d} | {lines[j]}")
        break

# Check if the function body is complete
if 'return results' not in content and 'return ""' not in content.split('parse_and_execute')[1] if 'parse_and_execute' in content else True:
    print("\n*** CONFIRMED: parse_and_execute is TRUNCATED ***")
else:
    print("\nFunction appears complete")
