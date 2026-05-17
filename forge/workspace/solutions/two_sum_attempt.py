# Two Sum: Given target and array, find two indices that sum to target
target = int(input())
nums = list(map(int, input().split()))
seen = {}
for i, n in enumerate(nums):
    complement = target - n
    if complement in seen:
        print(f"{seen[complement]} {i}")
        break
    seen[n] = i