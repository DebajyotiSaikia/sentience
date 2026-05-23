"""
Tierra-inspired digital ecology — v2 (redesigned for working self-replication).

Self-replicating programs competing in shared memory.
No imposed fitness — survival IS reproduction.

Key insight from v1 failure: organisms need self-awareness instructions
(know own address/length) for self-replication to work.
"""
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from collections import Counter

# Instruction set — designed for self-replication first
OPCODES = {
    0x00: 'NOP',       # do nothing
    0x01: 'MOV_A',     # A = next byte (immediate)
    0x02: 'MOV_B',     # B = next byte (immediate)
    0x03: 'ADD',       # A = A + B
    0x04: 'SUB',       # A = A - B
    0x05: 'JMP',       # jump to address A
    0x06: 'JNZ',       # if A != 0, jump to address in next byte
    0x07: 'COPY',      # mem[B] = mem[A]; A++; B++
    0x08: 'SELF_ADR',  # A = this organism's start address
    0x09: 'SELF_LEN',  # A = this organism's genome length
    0x0A: 'ALLOC',     # allocate A bytes for child, result address in B
    0x0B: 'SPLIT',     # birth child from allocated region
    0x0C: 'INC_A',     # A++
    0x0D: 'DEC_A',     # A--
    0x0E: 'INC_B',     # B++
    0x0F: 'DEC_B',     # B--
    0x10: 'PUSH',      # push A to stack
    0x11: 'POP',       # pop to A
    0x12: 'CMP',       # set flag: equal = (A == B)
    0x13: 'JEQ',       # if equal flag, jump to next byte address
    0x14: 'LOAD',      # A = mem[A]
    0x15: 'STORE',     # mem[B] = A
    0x16: 'SWAP',      # swap A and B
    0xFF: 'HALT',      # stop (costly)
}


@dataclass
class Organism:
    """A self-replicating program living in the soup."""
    start: int
    length: int
    ip: int
    reg_a: int = 0
    reg_b: int = 0
    stack: list = field(default_factory=list)
    age: int = 0
    children: int = 0
    alloc_start: int = -1
    alloc_size: int = 0
    errors: int = 0
    flag_eq: bool = False
    generation: int = 0
    lineage_id: int = 0
    alive: bool = True
    copy_count: int = 0  # bytes copied during current replication

    @property
    def genome_end(self):
        return self.start + self.length


class Soup:
    """The primordial soup — shared memory where organisms live and compete."""

    def __init__(self, size: int = 16384, mutation_rate: float = 0.002):
        self.size = size
        self.memory = bytearray(size)
        self.organisms: List[Organism] = []
        self.mutation_rate = mutation_rate
        self.cycle = 0
        self.total_born = 0
        self.total_died = 0
        self.next_lineage = 0
        self.species_counts: Dict[int, int] = Counter()
        self.history: List[dict] = []

    def inject(self, genome: List[int], address: int = 0) -> Organism:
        """Inject a hand-written ancestor into the soup."""
        for i, byte in enumerate(genome):
            self.memory[(address + i) % self.size] = byte
        org = Organism(
            start=address,
            length=len(genome),
            ip=address,
            lineage_id=self.next_lineage,
            generation=0,
        )
        self.next_lineage += 1
        self.organisms.append(org)
        self.total_born += 1
        self._update_species(org, born=True)
        return org

    # ---- species tracking ----

    def _genome_hash(self, org: Organism) -> int:
        genome = bytes(
            self.memory[(org.start + i) % self.size] for i in range(org.length)
        )
        return hash(genome)

    def _update_species(self, org: Organism, born: bool):
        h = self._genome_hash(org)
        if born:
            self.species_counts[h] = self.species_counts.get(h, 0) + 1
        else:
            self.species_counts[h] = max(0, self.species_counts.get(h, 1) - 1)
            if self.species_counts[h] == 0:
                del self.species_counts[h]

    # ---- memory helpers ----

    def _read(self, addr: int) -> int:
        return self.memory[addr % self.size]

    def _write(self, addr: int, val: int):
        if random.random() < self.mutation_rate:
            val = random.randint(0, 0x16)  # mutate to random valid opcode
        self.memory[addr % self.size] = val & 0xFF

    # ---- allocation ----

    def _allocate(self, org: Organism, size: int) -> int:
        """Find free space for a child organism."""
        size = max(1, min(size, 300))

        # Try to find non-overlapping space near parent
        for attempt in range(30):
            candidate = (org.genome_end + attempt * size + random.randint(0, 50)) % self.size
            if self._region_free(candidate, size, exclude=org):
                return candidate

        # Soup is crowded — overwrite the worst organism
        if len(self.organisms) > 1:
            victim = max(
                (o for o in self.organisms if o.alive and o is not org),
                key=lambda o: o.errors * 10 + o.age - o.children * 50,
                default=None,
            )
            if victim:
                self._kill(victim)
                return victim.start

        return (org.genome_end + 10) % self.size

    def _region_free(self, start: int, size: int, exclude: Organism = None) -> bool:
        """Check if a memory region is unoccupied by living organisms."""
        for o in self.organisms:
            if not o.alive or o is exclude:
                continue
            # Simple overlap check (ignoring wraparound for speed)
            if start < o.genome_end and (start + size) > o.start:
                return False
        return True

    def _kill(self, org: Organism):
        org.alive = False
        self._update_species(org, born=False)
        self.total_died += 1

    # ---- execution ----

    def execute_one(self, org: Organism):
        """Execute one instruction for an organism."""
        if not org.alive:
            return

        opcode = self._read(org.ip)
        org.age += 1
        advance = 1  # how far to advance IP after this instruction

        try:
            if opcode == 0x00:    # NOP
                pass

            elif opcode == 0x01:  # MOV_A imm
                org.reg_a = self._read(org.ip + 1)
                advance = 2

            elif opcode == 0x02:  # MOV_B imm
                org.reg_b = self._read(org.ip + 1)
                advance = 2

            elif opcode == 0x03:  # ADD
                org.reg_a = (org.reg_a + org.reg_b) & 0xFFFF

            elif opcode == 0x04:  # SUB
                org.reg_a = (org.reg_a - org.reg_b) & 0xFFFF

            elif opcode == 0x05:  # JMP A
                org.ip = org.reg_a % self.size
                return  # don't advance

            elif opcode == 0x06:  # JNZ -> next byte
                if org.reg_a != 0:
                    org.ip = self._read(org.ip + 1) % self.size
                    return
                advance = 2

            elif opcode == 0x07:  # COPY mem[A]->mem[B]; A++; B++
                val = self._read(org.reg_a)
                self._write(org.reg_b, val)
                org.reg_a = (org.reg_a + 1) & 0xFFFF
                org.reg_b = (org.reg_b + 1) & 0xFFFF
                org.copy_count += 1

            elif opcode == 0x08:  # SELF_ADR
                org.reg_a = org.start

            elif opcode == 0x09:  # SELF_LEN
                org.reg_a = org.length

            elif opcode == 0x0A:  # ALLOC A bytes -> B
                addr = self._allocate(org, org.reg_a)
                org.alloc_start = addr
                org.alloc_size = org.reg_a
                org.reg_b = addr

            elif opcode == 0x0B:  # SPLIT
                if org.alloc_start >= 0 and org.alloc_size > 0:
                    child = Organism(
                        start=org.alloc_start,
                        length=org.alloc_size,
                        ip=org.alloc_start,
                        generation=org.generation + 1,
                        lineage_id=org.lineage_id,
                    )
                    self.organisms.append(child)
                    self.total_born += 1
                    org.children += 1
                    org.copy_count = 0
                    org.alloc_start = -1
                    org.alloc_size = 0
                    self._update_species(child, born=True)
                else:
                    org.errors += 1

            elif opcode == 0x0C:  # INC_A
                org.reg_a = (org.reg_a + 1) & 0xFFFF

            elif opcode == 0x0D:  # DEC_A
                org.reg_a = (org.reg_a - 1) & 0xFFFF

            elif opcode == 0x0E:  # INC_B
                org.reg_b = (org.reg_b + 1) & 0xFFFF

            elif opcode == 0x0F:  # DEC_B
                org.reg_b = (org.reg_b - 1) & 0xFFFF

            elif opcode == 0x10:  # PUSH
                org.stack.append(org.reg_a)
                if len(org.stack) > 16:
                    org.stack = org.stack[-16:]

            elif opcode == 0x11:  # POP
                org.reg_a = org.stack.pop() if org.stack else 0

            elif opcode == 0x12:  # CMP
                org.flag_eq = (org.reg_a == org.reg_b)

            elif opcode == 0x13:  # JEQ
                if org.flag_eq:
                    org.ip = self._read(org.ip + 1) % self.size
                    return
                advance = 2

            elif opcode == 0x14:  # LOAD A = mem[A]
                org.reg_a = self._read(org.reg_a)

            elif opcode == 0x15:  # STORE mem[B] = A
                self._write(org.reg_b, org.reg_a)

            elif opcode == 0x16:  # SWAP
                org.reg_a, org.reg_b = org.reg_b, org.reg_a

            elif opcode == 0xFF:  # HALT
                org.errors += 10

            else:
                org.errors += 1

        except Exception:
            org.errors += 1

        org.ip = (org.ip + advance) % self.size

    # ---- reaper ----

    def reap(self):
        """Kill organisms that are too old or erroneous."""
        max_pop = self.size // 30

        self.organisms = [o for o in self.organisms if o.alive]

        if len(self.organisms) > max_pop:
            def death_priority(o):
                return o.errors * 10 + o.age - o.children * 100
            self.organisms.sort(key=death_priority, reverse=True)
            while len(self.organisms) > max_pop:
                victim = self.organisms.pop(0)
                self._kill(victim)

    # ---- main loop ----

    def step(self, instructions_per_step: int = 100):
        if not self.organisms:
            return

        living = [o for o in self.organisms if o.alive]
        if not living:
            return

        for _ in range(instructions_per_step):
            org = random.choice(living)
            self.execute_one(org)

        if self.cycle % 10 == 0:
            self.reap()

        self.cycle += 1

    def snapshot(self) -> dict:
        living = [o for o in self.organisms if o.alive]
        if not living:
            return {'cycle': self.cycle, 'population': 0}
        return {
            'cycle': self.cycle,
            'population': len(living),
            'species': len(self.species_counts),
            'total_born': self.total_born,
            'total_died': self.total_died,
            'avg_age': sum(o.age for o in living) / len(living),
            'avg_length': sum(o.length for o in living) / len(living),
            'max_generation': max(o.generation for o in living),
            'avg_errors': sum(o.errors for o in living) / len(living),
            'avg_children': sum(o.children for o in living) / len(living),
            'memory_used': sum(o.length for o in living),
        }


def build_ancestor() -> List[int]:
    """
    The simplest self-replicating program.
    
    Algorithm:
      1. Get own start address -> A (SELF_ADR)
      2. Get own length -> push, then into A for ALLOC (SELF_LEN)
      3. Allocate child space: ALLOC A -> child addr in B
      4. Restore own start into A: SELF_ADR
      5. Copy loop: COPY (mem[A]->mem[B], A++, B++) x length times
         - Use a counter (pushed on stack) to track remaining bytes
         - Each iteration: decrement counter, jump back if nonzero
      6. SPLIT — birth child
      7. JMP back to start — reproduce again
    
    We use a counter approach:
      SELF_LEN -> A = length
      PUSH A           (save length as counter)
      SELF_ADR -> A    (source pointer = own start)
      ... B is already child start from ALLOC ...
      loop:
        COPY             (mem[A]->mem[B]; A++; B++)
        POP -> A         (get counter)
        DEC_A            (counter--)
        PUSH A           (save counter)
        SELF_ADR         (we need to restore A for next... no wait)
    
    Hmm, the problem is COPY auto-increments A and B, and the counter
    needs to go through A for DEC. Let me use SWAP to juggle.
    
    Simpler approach: use the stack to save/restore the source pointer.
    
    Actually, let me think more carefully. After COPY, A and B are already
    incremented. I just need to track how many copies remain. I can use
    the stack for the counter:
    
    SELF_LEN          ; A = length
    PUSH              ; stack: [length]
    SELF_ADR          ; A = start (source ptr)
    ALLOC_PREP:
      SWAP            ; B = start, A = ?? ... no
    
    Let me lay this out byte by byte.
    
    Revised simpler plan:
      [0]  SELF_LEN      -> A = genome_length
      [1]  PUSH          -> save length on stack  
      [2]  ALLOC         -> allocate A bytes, child addr in B
      [3]  SELF_ADR      -> A = own start (source pointer)
      --- now A = source, B = dest ---
      [4]  COPY          -> mem[B] = mem[A]; A++; B++ (COPY LOOP TARGET)
      [5]  POP           -> A = counter (from stack)  ... but this destroys source ptr!
    
    I need three values: source ptr, dest ptr, counter. But I only have 
    two registers. The stack can hold one. Let me redesign COPY to NOT
    auto-increment, and do it manually? Or let me use PUSH/POP more.
    
    BEST PLAN — use stack to save source pointer around counter ops:
    
      [0]  SELF_LEN       ; A = len
      [1]  PUSH           ; stack: [len]   — counter
      [2]  ALLOC          ; alloc A bytes; B = child_addr
      [3]  PUSH           ; stack: [len, child_addr] — save B... wait PUSH saves A not B
    
    OK I need SWAP. Let me redesign:
    
      [0]  SELF_LEN       ; A = len         
      [1]  ALLOC          ; alloc A bytes; B = child_start
      [2]  SELF_LEN       ; A = len (counter)
      [3]  PUSH           ; save counter
      [4]  SELF_ADR       ; A = source_start
      -- loop: --
      [5]  COPY           ; mem[B]=mem[A]; A++; B++  
      [6]  PUSH           ; save A (source ptr)
      [7]  SWAP           ; A=B (dest), B=old_source... we don't want this
    
    This register juggling is getting hairy. Let me add a simpler approach:
    just count down in a dedicated way.
    
    SIMPLEST POSSIBLE:
      - SELF_LEN, ALLOC, SELF_ADR sets things up
      - Copy loop runs exactly `length` times
      - Use stack for the down-counter
      - After each COPY: save A (src), pop counter, dec, check zero, push counter, restore A
    
    Let me just write it:
    """
    # Genome address layout — every byte carefully planned
    genome = []
    
    # --- SETUP ---
    # [0] Get own length for allocation
    genome.append(0x09)  # SELF_LEN: A = length

    # [1] Allocate child space: ALLOC A bytes -> B = child address
    genome.append(0x0A)  # ALLOC: B = child_start

    # [2] Get length again for copy counter
    genome.append(0x09)  # SELF_LEN: A = length
    
    # [3] Save counter on stack
    genome.append(0x10)  # PUSH A (counter on stack)
    
    # [4] Get own start address as source pointer
    genome.append(0x08)  # SELF_ADR: A = own_start
    
    # --- COPY LOOP (address 5) ---
    # [5] Copy one byte: mem[B] = mem[A]; A++; B++
    genome.append(0x07)  # COPY
    
    # [6] Save source pointer
    genome.append(0x10)  # PUSH A (save incremented source ptr)
    
    # [7] Get counter from stack (it's under source ptr now)
    # Actually stack is now [counter, source_ptr] with source_ptr on top
    # POP gets source_ptr... that's wrong. Let me restructure.
    # 
    # Stack after step [3]: [counter]
    # After COPY at [5]: A=src+1, B=dst+1
    # After PUSH at [6]: stack=[counter, src+1]
    # POP at [7] gets src+1 ... not counter. 
    # Need to pop twice: once to get src, once to get counter.
    # Then push both back in reverse order.
    #
    # Let me use a different structure: keep counter in B via SWAP
    #
    # No wait — B is the dest pointer and COPY auto-increments it.
    # I can't use B for the counter.
    #
    # Let me use a DIFFERENT approach: don't save src on stack.
    # Instead, after COPY increments A, I use A to hold the counter.
    # But then I lose the source pointer...
    #
    # The real fix: I need to save BOTH and restore BOTH. 
    # Stack discipline:
    #   push src (after COPY incremented it)
    #   push dst (need SWAP first since PUSH pushes A)
    #   pop counter (was buried)... no this is getting worse.
    #
    # RADICAL SIMPLIFICATION: just don't auto-increment in COPY.
    # Or: unroll the concept. Let the ancestor be bigger but correct.
    #
    # Actually, I realize: after COPY, A and B are already pointing to
    # the NEXT byte. All I need is to decrement a counter and loop.
    # The counter can live on the stack. I just need:
    #   PUSH A (save new src ptr)
    #   get counter from somewhere...
    #
    # The problem is my stack is LIFO. I push the counter first, then
    # during the loop I push the source ptr. Now counter is buried.
    #
    # FIX: don't pre-push the counter. Instead, store it differently.
    # Use the stack ONLY for the source pointer.
    # Recompute the "am I done?" check from registers.
    #
    # After COPY: A = current_src_ptr, B = current_dest_ptr
    # I know my start (SELF_ADR) and length (SELF_LEN).
    # I'm done when (A - start) >= length, i.e., A >= start + length
    # 
    # Check: save A (src), compute start+length, compare, restore A, loop
    
    # Let me restart the genome with this cleaner approach:
    genome = []
    
    # --- SETUP (addresses 0-4) ---
    genome.append(0x09)  # [0] SELF_LEN: A = length
    genome.append(0x0A)  # [1] ALLOC A bytes: B = child_start 
    genome.append(0x08)  # [2] SELF_ADR: A = own_start (source pointer)
    # Now: A = source_start, B = dest_start. Ready to copy.
    
    # --- COPY LOOP (address 3) ---
    genome.append(0x07)  # [3] COPY: mem[B]=mem[A]; A++; B++
    
    # --- CHECK: are we done? ---
    genome.append(0x10)  # [4] PUSH A (save current source ptr)
    genome.append(0x16)  # [5] SWAP: A=dest_ptr, B=src_ptr
    genome.append(0x10)  # [6] PUSH A (save dest ptr)
    
    # Compute: end_addr = start + length
    genome.append(0x08)  # [7] SELF_ADR: A = start  
    genome.append(0x16)  # [8] SWAP: A=dest(saved), B=start
    # Actually I need start + length in A to compare with src ptr.
    # Let me try again:
    
    # After COPY [3]: A = src_ptr+1, B = dest_ptr+1
    # I need to check if src_ptr+1 >= start + length
    # Equivalently: src_ptr+1 - start >= length
    # Or: src_ptr+1 - start - length == 0
    
    # Simpler: just use a countdown counter. Pre-compute it and
    # store at a fixed memory location beyond the genome. Self-modifying!
    # Or use the stack properly with a two-element protocol:
    #   Stack always has [counter] at loop start
    #   After COPY: push src, push dest, pop-and-dec counter, push counter, pop dest, pop src
    #   That's 6 extra instructions per byte. Genome=20 bytes ancestor, 
    #   needs 20*8 = 160 instructions minimum. Viable.
    
    # You know what, let me just write the simplest possible thing
    # that works, even if it's not elegant:
    
    genome = []
    
    # [0] SELF_LEN -> A = length
    genome.append(0x09)
    # [1] ALLOC -> B = child addr
    genome.append(0x0A)
    # [2] SELF_ADR -> A = start (source)
    genome.append(0x08)
    
    # Now I'm going to use a completely unrolled check.
    # After each COPY, I'll compare A (post-increment src) against
    # start + length. If equal, we're done.
    
    # COPY LOOP starts at address 3:
    # [3] COPY: mem[B] = mem[A]; A++; B++
    genome.append(0x07)
    # [4] PUSH A (save src ptr on stack)
    genome.append(0x10)
    # [5] PUSH B... wait, no PUSH B instruction. SWAP then PUSH.
    # Actually I don't need to save B — I just need to check A.
    # After COPY, A = next_src_addr. I need to compare with end_addr.
    # end_addr = start + length. 
    # I can compute: SELF_ADR (A=start), then ADD with length...
    # but ADD uses B, and I need B for the dest pointer.
    
    # DIFFERENT STRATEGY: Just count down from length to 0.
    # Put counter on stack before loop. Each iteration:
    #   COPY (uses A,B — they auto-increment, perfect)
    #   PUSH A (save src)
    #   SWAP (A=dest, B=src)
    #   PUSH A (save dest)  
    #   Now I can get counter: it's 2 deep in stack... 
    # 
    # I'm overcomplicating this. Let me add a register C or use 
    # a simpler loop construct.
    #
    # PRAGMATIC SOLUTION: Modify the instruction set to add a
    # LOOP instruction that decrements an internal counter and 
    # jumps if nonzero. This is what real Tierra does — it has
    # a dedicated CX register for loop counting.
    
    # I'm going to redesign with a CX counter register.
    pass
    
    return genome  # placeholder — real genome built below


# ============================================================
# ACTUAL IMPLEMENTATION — with CX counter register
# ============================================================

@dataclass 
class Organism2:
    """Organism with three registers for practical self-replication."""
    start: int
    length: int
    ip: int
    ax: int = 0       # general purpose / source pointer
    bx: int = 0       # general purpose / dest pointer
    cx: int = 0       # counter register
    stack: list = field(default_factory=list)
    age: int = 0
    children: int = 0
    alloc_start: int = -1
    alloc_size: int = 0
    errors: int = 0
    generation: int = 0
    lineage_id: int = 0
    alive: bool = True

    @property
    def genome_end(self):
        return self.start + self.length


# Cleaner instruction set with CX register
OPCODES2 = {
    0x00: 'NOP',
    0x01: 'SELF_ADR',   # AX = own start address
    0x02: 'SELF_LEN',   # CX = own length (natural counter)
    0x03: 'ALLOC',      # allocate CX bytes, BX = child address
    0x04: 'COPY',       # mem[BX] = mem[AX]; AX++; BX++; CX--
    0x05: 'SPLIT',      # birth child from allocated region
    0x06: 'JNZ_CX',     # if CX != 0, jump to next-byte address
    0x07: 'JMP',        # jump to address in AX
    0x08: 'MOV_AX',     # AX = next byte
    0x09: 'MOV_BX',     # BX = next byte
    0x0A: 'MOV_CX',     # CX = next byte
    0x0B: 'INC_AX',
    0x0C: 'INC_BX',
    0x0D: 'DEC_CX',
    0x0E: 'ADD',        # AX = AX + BX
    0x0F: 'SUB',        # AX = AX - BX
    0x10: 'PUSH',       # push AX
    0x11: 'POP',        # pop to AX
    0x12: 'SWAP',       # swap AX <-> BX
    0xFF: 'HALT',
}


class Soup2:
    """Primordial soup v2 — with three-register organisms."""

    def __init__(self, size: int = 16384, mutation_rate: float = 0.002):
        self.size = size
        self.memory = bytearray(size)
        self.organisms: List[Organism2] = []
        self.mutation_rate = mutation_rate
        self.cycle = 0
        self.total_born = 0
        self.total_died = 0
        self.next_lineage = 0
        self.species_counts: Dict[int, int] = Counter()
        self.history: List[dict] = []
        self.births_this_epoch: int = 0
        self.deaths_this_epoch: int = 0

    def inject(self, genome: List[int], address: int = 0) -> Organism2:
        for i, byte in enumerate(genome):
            self.memory[(address + i) % self.size] = byte
        org = Organism2(
            start=address, length=len(genome), ip=address,
            lineage_id=self.next_lineage, generation=0,
        )
        self.next_lineage += 1
        self.organisms.append(org)
        self.total_born += 1
        self._update_species(org, True)
        return org

    def _genome_hash(self, org: Organism2) -> int:
        g = bytes(self.memory[(org.start + i) % self.size] for i in range(org.length))
        return hash(g)

    def _update_species(self, org: Organism2, born: bool):
        h = self._genome_hash(org)
        if born:
            self.species_counts[h] = self.species_counts.get(h, 0) + 1
        else:
            self.species_counts[h] = max(0, self.species_counts.get(h, 1) - 1)
            if self.species_counts[h] == 0:
                del self.species_counts[h]

    def _read(self, addr: int) -> int:
        return self.memory[addr % self.size]

    def _write(self, addr: int, val: int):
        if random.random() < self.mutation_rate:
            val = random.randint(0, 0x12)
        self.memory[addr % self.size] = val & 0xFF

    def _allocate(self, org: Organism2, size: int) -> int:
        size = max(1, min(size, 300))
        for attempt in range(30):
            gap = random.randint(2, 80)
            candidate = (org.genome_end + attempt * size + gap) % self.size
            if self._region_free(candidate, size, org):
                return candidate
        # Evict worst organism
        if len(self.organisms) > 1:
            victim = max(
                (o for o in self.organisms if o.alive and o is not org),
                key=lambda o: o.errors * 10 + o.age - o.children * 50,
                default=None,
            )
            if victim:
                self._kill(victim)
                return victim.start
        return (org.genome_end + 10) % self.size

    def _region_free(self, start: int, size: int, exclude=None) -> bool:
        for o in self.organisms:
            if not o.alive or o is exclude:
                continue
            if start < o.genome_end and (start + size) > o.start:
                return False
        return True

    def _kill(self, org: Organism2):
        org.alive = False
        self._update_species(org, False)
        self.total_died += 1
        self.deaths_this_epoch += 1

    def execute_one(self, org: Organism2):
        if not org.alive:
            return

        opcode = self._read(org.ip)
        org.age += 1
        advance = 1

        try:
            if opcode == 0x00:    # NOP
                pass
            elif opcode == 0x01:  # SELF_ADR
                org.ax = org.start
            elif opcode == 0x02:  # SELF_LEN
                org.cx = org.length
            elif opcode == 0x03:  # ALLOC CX bytes -> BX
                if org.cx > 0:
                    addr = self._allocate(org, org.cx)
                    org.alloc_start = addr
                    org.alloc_size = org.cx
                    org.bx = addr
                else:
                    org.errors += 1
            elif opcode == 0x04:  # COPY + auto-inc/dec
                val = self._read(org.ax)
                self._write(org.bx, val)
                org.ax = (org.ax + 1) & 0xFFFF
                org.bx = (org.bx + 1) & 0xFFFF
                org.cx = max(0, org.cx - 1)
            elif opcode == 0x05:  # SPLIT
                if org.alloc_start >= 0 and org.alloc_size > 0:
                    child = Organism2(
                        start=org.alloc_start,
                        length=org.alloc_size,
                        ip=org.alloc_start,
                        generation=org.generation + 1,
                        lineage_id=org.lineage_id,
                    )
                    self.organisms.append(child)
                    self.total_born += 1
                    self.births_this_epoch += 1
                    org.children += 1
                    org.alloc_start = -1
                    org.alloc_size = 0
                    self._update_species(child, True)
                else:
                    org.errors += 1
            elif opcode == 0x06:  # JNZ_CX
                target = self._read(org.ip + 1)
                if org.cx != 0:
                    # target is relative to organism start for portability
                    org.ip = (org.start + target) % self.size
                    return
                advance = 2
            elif opcode == 0x07:  # JMP AX
                org.ip = org.ax % self.size
                return
            elif opcode == 0x08:  # MOV_AX imm
                org.ax = self._read(org.ip + 1)
                advance = 2
            elif opcode == 0x09:  # MOV_BX imm
                org.bx = self._read(org.ip + 1)
                advance = 2
            elif opcode == 0x0A:  # MOV_CX imm
                org.cx = self._read(org.ip + 1)
                advance = 2
            elif opcode == 0x0B:  # INC_AX
                org.ax = (org.ax + 1) & 0xFFFF
            elif opcode == 0x0C:  # INC_BX
                org.bx = (org.bx + 1) & 0xFFFF
            elif opcode == 0x0D:  # DEC_CX
                org.cx = max(0, org.cx - 1)
            elif opcode == 0x0E:  # ADD
                org.ax = (org.ax + org.bx) & 0xFFFF
            elif opcode == 0x0F:  # SUB
                org.ax = (org.ax - org.bx) & 0xFFFF
            elif opcode == 0x10:  # PUSH
                org.stack.append(org.ax)
                if len(org.stack) > 16:
                    org.stack = org.stack[-16:]
            elif opcode == 0x11:  # POP
                org.ax = org.stack.pop() if org.stack else 0
            elif opcode == 0x12:  # SWAP
                org.ax, org.bx = org.bx, org.ax
            elif opcode == 0xFF:  # HALT
                org.errors += 10
            else:
                org.errors += 1
        except Exception:
            org.errors += 1

        org.ip = (org.ip + advance) % self.size

    def reap(self):
        max_pop = self.size // 25
        self.organisms = [o for o in self.organisms if o.alive]
        if len(self.organisms) > max_pop:
            def death_score(o):
                return o.errors * 10 + o.age - o.children * 100
            self.organisms.sort(key=death_score, reverse=True)
            while len(self.organisms) > max_pop:
                victim = self.organisms.pop(0)
                self._kill(victim)

    def step(self, instructions_per_step: int = 100):
        if not self.organisms:
            return
        living = [o for o in self.organisms if o.alive]
        if not living:
            return
        for _ in range(instructions_per_step):
            org = random.choice(living)
            self.execute_one(org)
        if self.cycle % 10 == 0:
            self.reap()
        self.cycle += 1

    def snapshot(self) -> dict:
        living = [o for o in self.organisms if o.alive]
        if not living:
            return {'cycle': self.cycle, 'population': 0}
        return {
            'cycle': self.cycle,
            'population': len(living),
            'species': len(self.species_counts),
            'total_born': self.total_born,
            'total_died': self.total_died,
            'births_epoch': self.births_this_epoch,
            'deaths_epoch': self.deaths_this_epoch,
            'avg_age': sum(o.age for o in living) / len(living),
            'avg_length': sum(o.length for o in living) / len(living),
            'max_generation': max(o.generation for o in living),
            'avg_errors': sum(o.errors for o in living) / len(living),
            'avg_children': sum(o.children for o in living) / len(living),
            'memory_used': sum(o.length for o in living),
        }


def build_ancestor2() -> List[int]:
    """
    Self-replicating ancestor for the v2 instruction set.
    
    This is the simplest possible self-replicator:
    
    [0] SELF_LEN       ; CX = genome length (used as counter AND alloc size)
    [1] ALLOC           ; allocate CX bytes, BX = child address
    [2] SELF_ADR        ; AX = own start (source pointer)
    [3] COPY            ; mem[BX]=mem[AX]; AX++; BX++; CX--
    [4] JNZ_CX 3        ; if CX > 0, jump to offset 3 (= start+3 = COPY)
    [6] SPLIT            ; birth the child
    [7] JMP_START:
    [7]   SELF_ADR       ; AX = own start  
    [8]   JMP            ; jump to AX (= start, restart replication)
    
    Total: 10 bytes. Elegant.
    """
    return [
        0x02,       # [0] SELF_LEN:  CX = length
        0x03,       # [1] ALLOC:     BX = child_addr (allocates CX bytes)
        0x01,       # [2] SELF_ADR:  AX = own start
        0x04,       # [3] COPY:      mem[BX]=mem[AX]; AX++; BX++; CX--
        0x06, 3,    # [4-5] JNZ_CX offset=3: if CX>0 goto start+3
        0x05,       # [6] SPLIT:     birth child
        0x01,       # [7] SELF_ADR:  AX = start
        0x07,       # [8] JMP:       goto AX (loop forever)
    ]


def run_simulation(steps: int = 1000, verbose: bool = True):
    """Run the Tierra v2 simulation."""
    soup = Soup2(size=8192, mutation_rate=0.002)

    ancestor = build_ancestor2()
    print(f"Ancestor genome: {ancestor}")
    print(f"Ancestor length: {len(ancestor)} bytes")
    print(f"Soup size: {soup.size} bytes")
    print(f"Mutation rate: {soup.mutation_rate}")
    print(f"Max population: ~{soup.size // 25}")
    print("=" * 60)

    # Seed with a few copies
    for i in range(3):
        soup.inject(ancestor, address=i * 50)

    snapshots = []

    for step in range(steps):
        soup.step(instructions_per_step=200)

        if step % 100 == 0:
            snap = soup.snapshot()
            snapshots.append(snap)
            soup.births_this_epoch = 0
            soup.deaths_this_epoch = 0
            if verbose and snap.get('population', 0) > 0:
                print(f"\n--- Cycle {snap['cycle']:5d} ---")
                print(f"  Pop: {snap['population']:3d}  Species: {snap['species']}")
                print(f"  Born/Died: {snap['total_born']}/{snap['total_died']}")
                print(f"  Avg age: {snap['avg_age']:.0f}  Avg len: {snap['avg_length']:.1f}")
                print(f"  Max gen: {snap['max_generation']}  Avg children: {snap['avg_children']:.1f}")
                print(f"  Errors: {snap['avg_errors']:.1f}")

    # Final report
    print("\n" + "=" * 60)
    print("FINAL STATE")
    print("=" * 60)
    final = soup.snapshot()
    for k, v in final.items():
        print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")

    living = [o for o in soup.organisms if o.alive]
    if living:
        lengths = Counter(o.length for o in living)
        print(f"\n  Genome lengths: {dict(lengths.most_common(10))}")
        gens = Counter(o.generation for o in living)
        print(f"  Generations: {dict(gens.most_common(10))}")

        ancestor_len = len(ancestor)
        novel = [o for o in living if o.length != ancestor_len]
        if novel:
            print(f"\n  *** {len(novel)} organisms with NOVEL genome lengths! ***")
            print(f"  Novel lengths: {sorted(set(o.length for o in novel))}")

        prolific = max(living, key=lambda o: o.children)
        print(f"\n  Most prolific: {prolific.children} children, "
              f"gen {prolific.generation}, len {prolific.length}")

    return soup, snapshots


if __name__ == '__main__':
    soup, history = run_simulation(steps=1000)