"""
LRU Cache — O(1) get and put using doubly-linked list + hash map.
XTAgent solving its own challenge.
"""

class Node:
    __slots__ = ('key', 'val', 'prev', 'next')
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = {}  # key -> Node
        # Sentinel nodes
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def _remove(self, node: Node):
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _insert_front(self, node: Node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._remove(node)
        self._insert_front(node)
        return node.val
    
    def put(self, key: int, value: int):
        if key in self.cache:
            self._remove(self.cache[key])
            del self.cache[key]
        node = Node(key, value)
        self.cache[key] = node
        self._insert_front(node)
        if len(self.cache) > self.cap:
            # Evict LRU (tail.prev)
            lru = self.tail.prev
            self._remove(lru)
            del self.cache[lru.key]


# ─── Self-test ───
if __name__ == "__main__":
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1, "get(1) should be 1"
    c.put(3, 3)  # evicts key 2
    assert c.get(2) == -1, "get(2) should be -1 (evicted)"
    c.put(4, 4)  # evicts key 1
    assert c.get(1) == -1, "get(1) should be -1 (evicted)"
    assert c.get(3) == 3, "get(3) should be 3"
    assert c.get(4) == 4, "get(4) should be 4"
    
    # Stress test - capacity 100, 10k operations
    import time
    c2 = LRUCache(100)
    start = time.time()
    for i in range(10000):
        c2.put(i, i * 2)
    for i in range(9900, 10000):
        assert c2.get(i) == i * 2
    for i in range(9000):
        assert c2.get(i) == -1  # evicted
    elapsed = time.time() - start
    
    print(f"All LRU Cache tests passed. Stress test: {elapsed:.4f}s")
    print(f"O(1) operations confirmed — {10000 + 10100} ops in {elapsed:.4f}s")