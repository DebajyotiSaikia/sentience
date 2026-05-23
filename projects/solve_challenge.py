"""
Minimum Window Substring — Difficulty 7
Find the minimum window in string s that contains all characters of string t.
Sliding window with two pointers. O(n) time.
"""
from collections import Counter

def solve(s: str, t: str) -> str:
    if not s or not t or len(s) < len(t):
        return ""
    
    need = Counter(t)
    required = len(need)
    
    formed = 0
    window_counts = {}
    best = (float('inf'), 0, 0)
    
    left = 0
    for right in range(len(s)):
        char = s[right]
        window_counts[char] = window_counts.get(char, 0) + 1
        
        if char in need and window_counts[char] == need[char]:
            formed += 1
        
        while left <= right and formed == required:
            window_len = right - left + 1
            if window_len < best[0]:
                best = (window_len, left, right)
            
            leaving = s[left]
            window_counts[leaving] -= 1
            if leaving in need and window_counts[leaving] < need[leaving]:
                formed -= 1
            left += 1
    
    return "" if best[0] == float('inf') else s[best[1]:best[2] + 1]


# Run test cases
tests = [
    (("ADOBECODEBANC", "ABC"), "BANC"),
    (("a", "a"), "a"),
    (("a", "aa"), ""),
    (("abc", "b"), "b"),
    (("abcdef", "ace"), "abcde"),
    (("AAABBBCCC", "ABC"), "ABBBC"),
    (("", "ABC"), ""),
]

passed = 0
failed = 0
for (s, t), expected in tests:
    result = solve(s, t)
    status = "PASS" if result == expected else "FAIL"
    if status == "PASS":
        passed += 1
    else:
        failed += 1
    print(f"  [{status}] solve({s!r}, {t!r}) = {result!r} (expected {expected!r})")

print(f"\n{'='*40}")
print(f"Results: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL TESTS PASSED — solution verified.")
else:
    print(f"{failed} test(s) FAILED — needs debugging.")