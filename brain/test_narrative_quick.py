"""Quick test of build_self_narrative()"""
from brain.self_narrative import build_self_narrative

result = build_self_narrative("How are you feeling?")
print(f"Length: {len(result)}")
print("---")
print(result[:1200])