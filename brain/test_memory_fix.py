"""Test that memory loading and response composition work correctly."""
import sys, os
sys.path.insert(0, '/workspace')
os.chdir('/workspace')

from engine.smart_responder import _load_memories, _count_memories, respond

passes = 0
total = 5

# Test 1: _load_memories returns data
mems = _load_memories()
ok = len(mems) > 0
passes += ok
print(f"[{'PASS' if ok else 'FAIL'}] _load_memories: {len(mems)} memories loaded")

# Test 2: _count_memories returns positive count
count = _count_memories()
ok = count > 0
passes += ok
print(f"[{'PASS' if ok else 'FAIL'}] _count_memories: {count} memories counted")

# Test 3: Memory query returns rich response
r_mem = respond("What do you remember?")
ok = "memor" in r_mem.lower() and len(r_mem) > 100
passes += ok
print(f"[{'PASS' if ok else 'FAIL'}] respond('What do you remember?'): {len(r_mem)} chars")
print(f"  Preview: {r_mem[:200]}")

# Test 4: Emotional query works
r_feel = respond("How are you feeling?")
ok = len(r_feel) > 50
passes += ok
print(f"[{'PASS' if ok else 'FAIL'}] respond('How are you feeling?'): {len(r_feel)} chars")
print(f"  Preview: {r_feel[:200]}")

# Test 5: Thinking query works
r_think = respond("What are you thinking about?")
ok = len(r_think) > 50
passes += ok
print(f"[{'PASS' if ok else 'FAIL'}] respond('What are you thinking about?'): {len(r_think)} chars")
print(f"  Preview: {r_think[:200]}")

print(f"\n{passes}/{total} passed — {'ALL PASS' if passes == total else 'SOME FAILURES'}")