"""
Challenge: Trie (Prefix Tree)
Category: data_structures
Difficulty: 3

Implement a Trie with insert(word), search(word)->bool, and starts_with(prefix)->bool.
"""


class TrieNode:
    __slots__ = ('children', 'is_end')

    def __init__(self):
        self.children = {}
        self.is_end = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        return self._find_node(prefix) is not None

    def _find_node(self, prefix: str) -> TrieNode | None:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node


# ── Tests ──
if __name__ == "__main__":
    tests_passed = 0
    tests_total = 0

    def check(label, got, expected):
        global tests_passed, tests_total
        tests_total += 1
        ok = got == expected
        if ok:
            tests_passed += 1
            print(f"  ✓ {label}")
        else:
            print(f"  ✗ {label}: expected {expected}, got {got}")

    t = Trie()

    # Insert and search basic words
    t.insert("apple")
    check("search('apple')", t.search("apple"), True)
    check("search('app')", t.search("app"), False)
    check("starts_with('app')", t.starts_with("app"), True)

    # Insert prefix as its own word
    t.insert("app")
    check("search('app') after insert", t.search("app"), True)

    # Non-existent words
    check("search('apples')", t.search("apples"), False)
    check("search('banana')", t.search("banana"), False)
    check("starts_with('ban')", t.starts_with("ban"), False)

    # Empty string
    check("search('')", t.search(""), False)
    t.insert("")
    check("search('') after insert", t.search(""), True)
    check("starts_with('')", t.starts_with(""), True)

    # Overlapping words
    t.insert("application")
    t.insert("apply")
    check("search('application')", t.search("application"), True)
    check("search('apply')", t.search("apply"), True)
    check("search('appli')", t.search("appli"), False)
    check("starts_with('appl')", t.starts_with("appl"), True)

    # Single character
    t.insert("a")
    check("search('a')", t.search("a"), True)
    check("starts_with('a')", t.starts_with("a"), True)

    # Completely separate branch
    t.insert("zebra")
    check("search('zebra')", t.search("zebra"), True)
    check("starts_with('ze')", t.starts_with("ze"), True)
    check("search('zeb')", t.search("zeb"), False)

    print(f"\n{tests_passed}/{tests_total} tests passed")