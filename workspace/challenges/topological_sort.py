"""
Challenge: Topological Sort
Category: algorithms
Difficulty: ★★★☆☆

Implement topological sort for a DAG using Kahn's algorithm (BFS). Return a valid ordering or raise ValueError if cycle detected.

Solve below, then run this file to test.
"""

# === YOUR SOLUTION HERE ===

from collections import deque

def topological_sort(graph):
    # Compute in-degrees
    in_degree = {node: 0 for node in graph}
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

    # Seed queue with zero in-degree nodes
    queue = deque(node for node in graph if in_degree[node] == 0)
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(graph):
        raise ValueError("Cycle detected — not a DAG")

    return result


# === TESTS (do not modify) ===
if __name__ == "__main__":
    # Simple DAG
    graph = {0: [1, 2], 1: [3], 2: [3], 3: []}
    result = topological_sort(graph)
    assert result.index(0) < result.index(1)
    assert result.index(0) < result.index(2)
    assert result.index(1) < result.index(3)
    assert result.index(2) < result.index(3)

    # Cycle detection
    try:
        topological_sort({0: [1], 1: [2], 2: [0]})
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Single node
    assert topological_sort({0: []}) == [0]
    print("All topological sort tests passed!")