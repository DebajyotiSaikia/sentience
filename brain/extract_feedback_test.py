"""Extract the feedback test section from ux_audit.py"""
with open('brain/ux_audit.py') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'feedback' in line.lower():
        start = max(0, i - 2)
        end = min(len(lines), i + 6)
        for j in range(start, end):
            print(f"{j+1}: {lines[j]}", end='')
        print("---")