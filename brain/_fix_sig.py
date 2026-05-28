with open('engine/response_shaper.py') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'get_emotional_voice_directive' in line and 'def ' in line:
        print(f'{i}: {line.rstrip()}')