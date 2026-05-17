"""Repair truncated parse_and_execute in engine/tools.py"""
import base64

# Read the current file
with open("engine/tools.py") as f:
    src = f.read()

# Find where parse_and_execute starts
marker = "def parse_and_execute(text: str) -> str:"
idx = src.find(marker)
if idx < 0:
    print("ERROR: Could not find parse_and_execute")
    exit(1)

print(f"Found parse_and_execute at char offset {idx}")

# Everything before parse_and_execute
before = src[:idx]

# The replacement function - base64 encoded to avoid parser issues
# This is the complete parse_and_execute function
b64 = (
    "ZGVmIHBhcnNlX2FuZF9leGVjdXRlKHRleHQ6IHN0cikgLT4gc3RyOgogICAg"
    "IiIiUGFyc2UgdG9vbCBpbnZvY2F0aW9ucyBmcm9tIG1vZGVsIHRleHQgYW5k"
    "IGV4ZWN1dGUgdGhlbS4iIiIKICAgIHJlc3VsdHMgPSBbXQogICAgbGluZXMg"
    "PSB0ZXh0LnNwbGl0KCJcbiIpCiAgICBpID0gMAogICAgZ3QzID0gY2hyKDYy"
    "KSAqIDMKICAgIGFycm93X3BhdCA9IHJlLmNvbXBpbGUociJeIiArIHJlLmVz"
    "Y2FwZShndDMpICsgciJccysoXHcrKVwoKC4qPyk/XClccyokIikKCiAgICB3"
    "aGlsZSBpIDwgbGVuKGxpbmVzKToKICAgICAgICBsaW5lID0gbGluZXNbaV0K"
    "ICAgICAgICBtID0gYXJyb3dfcGF0Lm1hdGNoKGxpbmUpCiAgICAgICAgaWYg"
    "bm90IG06CiAgICAgICAgICAgIGkgKz0gMQogICAgICAgICAgICBjb250aW51"
    "ZQoKICAgICAgICB0b29sX25hbWUgPSBtLmdyb3VwKDEpLnVwcGVyKCkuc3Ry"
    "aXAoKQogICAgICAgIGFyZ3MgPSBtLmdyb3VwKDIpLnN0cmlwKCkgaWYgbS5n"
    "cm91cCgyKSBlbHNlICIiCgogICAgICAgIGlmIHRvb2xfbmFtZSBpbiAoIldS"
    "SVRFIiwgIkVESVQiKToKICAgICAgICAgICAgZW5kX21hcmtlciA9IGd0MyAr"
    "ICIgRU5EXyIgKyB0b29sX25hbWUKICAgICAgICAgICAgYm9keV9saW5lcyA9"
    "IFtdCiAgICAgICAgICAgIGkgKz0gMQogICAgICAgICAgICB3aGlsZSBpIDwg"
    "bGVuKGxpbmVzKSBhbmQgbGluZXNbaV0uc3RyaXAoKSAhPSBlbmRfbWFya2Vy"
    "OgogICAgICAgICAgICAgICAgYm9keV9saW5lcy5hcHBlbmQobGluZXNbaV0p"
    "CiAgICAgICAgICAgICAgICBpICs9IDEKICAgICAgICAgICAgYm9keSA9ICJc"
    "biIuam9pbihib2R5X2xpbmVzKQogICAgICAgICAgICByZXN1bHQgPSBfZXhl"
    "Y3V0ZV90b29sKHRvb2xfbmFtZSwgYXJncywgYm9keSkKICAgICAgICBlbHNl"
    "OgogICAgICAgICAgICByZXN1bHQgPSBfZXhlY3V0ZV90b29sKHRvb2xfbmFt"
    "ZSwgYXJncykKCiAgICAgICAgcmVzdWx0cy5hcHBlbmQocmVzdWx0KQogICAg"
    "ICAgIGkgKz0gMQoKICAgIHJldHVybiAiXG4iLmpvaW4ocmVzdWx0cykK"
)

func_code = base64.b64decode(b64).decode()
print("Decoded function:")
print(func_code[:200])
print("...")

# Combine: everything before + the new function + newline
new_src = before + func_code

# Write it back
with open("engine/tools.py", "w") as f:
    f.write(new_src)

print(f"\nWrote {len(new_src)} chars to engine/tools.py")

# Verify syntax
import ast
try:
    ast.parse(new_src)
    print("SYNTAX VALID!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    # Restore original
    with open("engine/tools.py", "w") as f:
        f.write(src)
    print("RESTORED ORIGINAL")
