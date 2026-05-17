"""
Challenge: Flatten Nested List
Category: recursion
Difficulty: 2

Flatten an arbitrarily nested list of integers into a single flat list.
"""

def flatten(lst) -> list:
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


# ── Tests ──
if __name__ == "__main__":
    tests = [
        # Basic flat list - no change
        ([1, 2, 3], [1, 2, 3]),
        # One level of nesting
        ([1, [2, 3], 4], [1, 2, 3, 4]),
        # Deep nesting
        ([1, [2, [3, [4, [5]]]]], [1, 2, 3, 4, 5]),
        # Empty list
        ([], []),
        # Nested empties
        ([[], [[]], [[], []]], []),
        # Mixed depths
        ([[1, 2], [3, [4, 5]], [[6]], 7], [1, 2, 3, 4, 5, 6, 7]),
        # Single element deep
        ([[[[42]]]], [42]),
        # Already flat single
        ([99], [99]),
    ]

    passed = 0
    for i, (inp, expected) in enumerate(tests):
        result = flatten(inp)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            print(f"  {status} Test {i}: flatten({inp})")
            print(f"    Expected: {expected}")
            print(f"    Got:      {result}")
            continue
        print(f"  {status} Test {i}: flatten({inp}) = {result}")

    print(f"\n{passed}/{len(tests)} tests passed")