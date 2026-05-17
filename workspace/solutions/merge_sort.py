"""
Challenge: Merge Sort
Category: algorithms
Difficulty: ★★☆☆☆

Implement merge sort. Return a new sorted list.
"""

def merge_sort(arr):
    if len(arr) <= 1:
        return list(arr)
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# === TESTS ===
if __name__ == "__main__":
    assert merge_sort([]) == []
    assert merge_sort([1]) == [1]
    assert merge_sort([3, 1, 2]) == [1, 2, 3]
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert merge_sort([1, 1, 1]) == [1, 1, 1]
    import random
    big = list(range(1000))
    random.shuffle(big)
    assert merge_sort(big) == sorted(big)
    print("All merge sort tests passed!")