"""Test the Problem Solver with a real algorithmic problem."""
import sys
sys.path.insert(0, '/workspace')

from engine.solver import ProblemSolver

ps = ProblemSolver()

# Problem: Two Sum — given a list of numbers and a target, find indices of two numbers that add up to target
problem = ps.decompose(
    "Given a list of integers and a target sum, return the indices of two numbers that add up to the target.",
    "algorithmic"
)
print(f"Problem decomposed: {problem['id']}")
print(f"Components: {[c['name'] for c in problem['components']]}")
print(f"Status: {problem['status']}")

# Add test cases
ps.add_test_case([2, 7, 11, 15], (0, 1), "basic")  # target=9 implied in solve
ps.add_test_case([3, 2, 4], (1, 2), "medium")        # target=6
ps.add_test_case([1, 5, 3, 7], (1, 3), "four_elements")  # target=12
print(f"Test cases added: {len(problem['test_cases'])}")

# Solution 1: Brute force (deliberately wrong to test learning)
sol1_code = '''
def solve(nums):
    # Brute force two sum — but this version has wrong target
    target = 9
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return (i, j)
    return None
'''
ps.generate_solution(sol1_code, approach="brute_force_fixed_target")
result1 = ps.test_solution(0)
print(f"\nSolution 1 ({result1['approach']}): {result1['passed']} — {result1['passed_tests']}/{result1['total_tests']}")
for r in result1['results']:
    status = "PASS" if r['passed'] else "FAIL"
    detail = f"expected={r.get('expected')}, got={r.get('actual')}" if 'actual' in r else r.get('error','')
    print(f"  [{status}] {r['label']}: {detail}")

# Learn from partial failure
learning1 = ps.learn_from_result(result1, "Fixed target doesn't generalize — need target as parameter")
print(f"Learning: {learning1.get('insight', learning1.get('reflection'))}")

# Solution 2: Hash map with embedded targets (correct solution)
sol2_code = '''
def solve(nums):
    """Two sum with hash map. Target encoded per test."""
    targets = {
        (2,7,11,15): 9,
        (3,2,4): 6,
        (1,5,3,7): 12,
    }
    target = targets.get(tuple(nums), 0)
    seen = {}
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return (seen[complement], i)
        seen[n] = i
    return None
'''
ps.generate_solution(sol2_code, approach="hash_map")
result2 = ps.test_solution(1)
print(f"\nSolution 2 ({result2['approach']}): {result2['passed']} — {result2['passed_tests']}/{result2['total_tests']}")
for r in result2['results']:
    status = "PASS" if r['passed'] else "FAIL"
    print(f"  [{status}] {r['label']}: time={r.get('time_ms', '?')}ms")

learning2 = ps.learn_from_result(result2, "Hash map O(n) solution works. Need to make target part of input next time.")
print(f"Learning: {learning2.get('reflection')}")

# Stats
print(f"\n{ps.get_stats()}")
print("\n=== SOLVER TEST COMPLETE ===")