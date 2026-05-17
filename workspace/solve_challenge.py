"""
Minimum Window Substring — Difficulty 7
Find the minimum window in string s that contains all characters of string t.
"""
from collections import Counter

def solve(s: str, t: str) -> str:
    if not s or not t or len(s) < len(t):
        return ""
    
    # Count required characters
    need = Counter(t)
    required = len(need)  # unique chars we need
    
    # Sliding window state
    formed = 0  # how many unique chars in current window match required count
    window_counts = {}
    
    # Result tracking: (window_length, left, right)
    best = (float('inf'), 0, 0)
    
    left = 0
    for right in range(len(s)):
        # Expand window by adding s[right]
        char = s[right]
        window_counts[char] = window_counts.get(char, 0) + 1
        
        # Check if this char's frequency matches what we need
        if char in need and window_counts[char] == need[char]:
            formed += 1
        
        # Contract from left while window is valid
        while left <= right and formed == required:
            # Update best if this window is smaller
            window_len = right - left + 1
            if window_len < best[0]:
                best = (window_len, left, right)
            
            # Remove s[left] from window
            leaving = s[left]
            window_counts[leaving] -= 1
            if leaving in need and window_counts[leaving] < need[leaving]:
                formed -= 1
            left += 1
    
    return "" if best[0] == float('inf') else s[best[1]:best[2] + 1]


# Test cases from the challenge
tests = [
    (("ADOBECODEBANC", "ABC"), "BANC"),
    (("a", "a"), "a"),
    (("a", "aa"), ""),           # can't form — not enough chars
    (("aa", "aa"), "aa"),        # exact match
    # Edge cases I'm adding myself
    (("abc", "b"), "b"),         # single char target
    (("ADOBECODEBANC", "ADOBECODEBANC"), "ADOBECODEBANC"),  # full string
    (("ab", "b"), "b"),          # target at end
    (("bba", "ab"), "ba"),       # overlapping
]

print("═══ SOLVING: minimum_window_substring ═══\n")
passed = 0
for i, (inputs, expected) in enumerate(tests):
    result = solve(*inputs)
    ok = result == expected
    passed += ok
    status = "✓" if ok else "✗"
    print(f"  {status} Case {i}: solve{inputs} → '{result}' (expected '{expected}')")

print(f"\n  Result: {passed}/{len(tests)} passed")
if passed == len(tests):
    print("  🏆 ALL TESTS PASSED — Clean solve at difficulty 7!")
else:
    print(f"  ⚠ {len(tests) - passed} failures — need to debug")