"""Check if _build_system_context actually uses response shaper"""
with open('engine/chat_response.py') as f:
    lines = f.readlines()
# Show the end of _build_system_context where context string is assembled
for i in range(165, 200):
    print(f"{i+1}: {lines[i]}", end='')