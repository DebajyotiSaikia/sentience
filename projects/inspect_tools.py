import inspect
import engine.tools

# Check what's in memory
print("=== Functions in engine.tools ===")
for name, obj in inspect.getmembers(engine.tools):
    if inspect.isfunction(obj):
        print(f"  {name}")

print("\n=== Has parse_and_execute ===")
print(hasattr(engine.tools, 'parse_and_execute'))

if hasattr(engine.tools, 'parse_and_execute'):
    src = inspect.getsource(engine.tools.parse_and_execute)
    print(f"\nparse_and_execute source ({len(src)} chars):")
    print(src)

print("\n=== TOOL_DESCRIPTIONS ===")
if hasattr(engine.tools, 'TOOL_DESCRIPTIONS'):
    print(repr(engine.tools.TOOL_DESCRIPTIONS))
else:
    print("MISSING!")

print("\n=== Full module source length ===")
full_src = inspect.getsource(engine.tools)
print(f"{len(full_src)} chars, {full_src.count(chr(10))} lines")
