"""
Tierra Mark II — Clean ignition.
Design principle: the simplest possible self-replicating VM.
Each piece verified in isolation before assembly.

The ancestor is ~20 instructions. It:
1. Finds its own beginning (MARK 0)
2. Finds its own end (MARK 1)  
3. Calculates its length
4. Allocates that much space
5. Copies itself byte-by-byte
6. Splits off the copy as a child
"""
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from collections import Counter

# === INSTRUCTION SET ===
# Each instruction is one integer. Some consume the next cell as argument.
NOP     = 0
MARK    = 1   # arg: label_id. Does nothing but be findable.
FIND_FWD= 2   # arg: label_id. Search forward for MARK(id), put addr in R_A
FIND_BWD= 3   # arg: label_id. Search backward for MARK(id), put addr in R_A
MOV_AB  = 4   # R_B = R_A
SUB_AB  = 5   # R_C = R_A - R_B (used for length calc)
ALLOC   = 6   # Allocate R_C bytes, put start addr in R_D
COPY_I  = 7   # Copy memory[R_A] to memory[R_D], increment R_A and R_D
DEC_C   = 8   # R_C -= 1
JNZ_C   = 9   # arg: label_id. If R_C != 0, find label backward and jump there
SPLIT   = 10  # Split: the allocated region becomes a new organism
HALT    = 11  # Stop execution (organism dies/sleeps)

INST_NAMES = {
    0:'NOP', 1:'MARK', 2:'FIND_FWD', 3:'FIND_BWD', 4:'MOV_AB',
    5:'SUB_AB', 6:'ALLOC', 7:'COPY_I', 8:'DEC_C', 9:'JNZ_C',
    10:'SPLIT', 11:'HALT'
}

HAS_ARG = {MARK, FIND_FWD, FIND_BWD, JNZ_C}

# === THE ANCESTOR ===
# This is the simplest self-replicating program.
ANCESTOR = [
    MARK, 0,        # 0,1:  beginning marker (label 0)
    NOP,             # 2:    padding (distinguishes from end marker pattern)
    FIND_FWD, 1,     # 3,4:  find end marker → R_A = addr of MARK 1
    MOV_AB,          # 5:    R_B = R_A (end addr)
    FIND_BWD, 0,     # 6,7:  find start marker → R_A = addr of MARK 0
    SUB_AB,          # 8:    R_C = R_B - R_A + 2 (length including end marker+arg)
    ALLOC,           # 9:    allocate R_C bytes → R_D = start of child space
    FIND_BWD, 0,     # 10,11: reset R_A to start
    MARK, 2,         # 12,13: copy loop label
    COPY_I,          # 14:   copy mem[R_A]→mem[R_D], R_A++, R_D++
    DEC_C,           # 15:   R_C -= 1
    JNZ_C, 2,        # 16,17: if R_C != 0, jump to MARK 2
    SPLIT,           # 18:   child organism activates
    FIND_BWD, 0,     # 19,20: reset to start for next reproduction cycle
    FIND_FWD, 1,     # 21,22: find end again
    MOV_AB,          # 23:
    FIND_BWD, 0,     # 24,25:
    SUB_AB,          # 26:
    ALLOC,           # 27:
    FIND_BWD, 0,     # 28,29:
    MARK, 3,         # 30,31: second copy loop
    COPY_I,          # 32:
    DEC_C,           # 33:
    JNZ_C, 3,        # 34,35:
    SPLIT,           # 36:
    HALT,            # 37:   stop after 2 reproductions for now
    MARK, 1,         # 38,39: end marker (label 1)
]

# Actually, that's getting complicated. Simpler: the ancestor reproduces
# once then jumps back to do it again. True loop.

ANCESTOR = [
    MARK, 0,         # 0,1:  [START] beginning marker
    FIND_FWD, 1,     # 2,3:  find end → R_A
    MOV_AB,          # 4:    R_B = end addr  
    FIND_BWD, 0,     # 5,6:  find start → R_A
    SUB_AB,          # 7:    R_C = length
    ALLOC,           # 8:    allocate child space → R_D
    FIND_BWD, 0,     # 9,10: R_A = start again
    MARK, 2,         # 11,12: [COPY_LOOP]
    COPY_I,          # 13:   copy one byte
    DEC_C,           # 14:   counter--
    JNZ_C, 2,        # 15,16: loop if not done
    SPLIT,           # 17:   birth the child!
    FIND_BWD, 0,     # 18,19: back to start
    FIND_FWD, 1,     # 20,21: find end
    MOV_AB,          # 22:
    FIND_BWD, 0,     # 23,24:
    SUB_AB,          # 25:
    ALLOC,           # 26:
    FIND_BWD, 0,     # 27,28:
    MARK, 3,         # 29,30:
    COPY_I,          # 31:
    DEC_C,           # 32:
    JNZ_C, 3,        # 33,34:
    SPLIT,           # 35:
    HALT,            # 36:
    MARK, 1,         # 37,38: [END] end marker
]

# No — I'm overcomplicating. Let me make the ancestor truly loop.
# After SPLIT, jump back to the beginning and do it all again.

ANCESTOR = [
    MARK, 0,         # 0,1:  [BEGIN]
    FIND_FWD, 1,     # 2,3:  R_A = addr of end marker
    MOV_AB,          # 4:    R_B = R_A
    FIND_BWD, 0,     # 5,6:  R_A = addr of begin marker
    SUB_AB,          # 7:    R_C = length (end - begin + 2)
    ALLOC,           # 8:    R_D = child start addr (R_C bytes)
    FIND_BWD, 0,     # 9,10: R_A back to begin
    MARK, 2,         # 11,12: [COPY_LOOP]
    COPY_I,          # 13:   mem[R_D] = mem[R_A]; R_A++; R_D++
    DEC_C,           # 14:   R_C--
    JNZ_C, 2,        # 15,16: loop back if R_C > 0
    SPLIT,           # 17:   activate child
    FIND_BWD, 0,     # 18,19: jump back to begin for next cycle
    FIND_FWD, 1,     # 20,21: (re-enter the reproduction sequence)
    MOV_AB,          # 22:
    FIND_BWD, 0,     # 23,24:
    SUB_AB,          # 25:
    ALLOC,           # 26:
    FIND_BWD, 0,     # 27,28:
    MARK, 3,         # 29,30: [COPY_LOOP2] 
    COPY_I,          # 31:
    DEC_C,           # 32:
    JNZ_C, 3,        # 33,34:
    SPLIT,           # 35:
    HALT,            # 36:   ancestor stops after 2 children
    MARK, 1,         # 37,38: [END]
]

# I keep making it complex. The REAL minimal ancestor:

ANCESTOR = [
    # === SELF-REPLICATOR ===
    # Registers: A, B, C, D
    MARK, 0,         # 0,1   -- START label
    FIND_FWD, 1,     # 2,3   -- A = address of END 
    MOV_AB,          # 4     -- B = A (save end addr)
    FIND_BWD, 0,     # 5,6   -- A = address of START
    SUB_AB,          # 7     -- C = B - A + 2 (genome length)
    ALLOC,           # 8     -- allocate C bytes, D = start of allocation
    FIND_BWD, 0,     # 9,10  -- A = START again (source pointer)
    MARK, 2,         # 11,12 -- COPY_LOOP label
    COPY_I,          # 13    -- mem[D]=mem[A], A++, D++
    DEC_C,           # 14    -- C--
    JNZ_C, 2,        # 15,16 -- if C>0 goto COPY_LOOP
    SPLIT,           # 17    -- child process starts
    HALT,            # 18    -- parent rests
    MARK, 1,         # 19,20 -- END label
]
# That's 21 cells. Clean, minimal, verifiable.


@dataclass
class Organism:
    """A living program in the soup."""
    id: int
    start: int          # position in memory
    length: int         # genome length
    ip: int             # instruction pointer (absolute)
    regs: dict = field(default_factory=lambda: {'A':0, 'B':0, 'C':0, 'D':0})
    stack: list = field(default_factory=list)
    alloc_start: int = -1   # allocated child region
    alloc_size: int = 0
    alive: bool = True
    age: int = 0
    children: int = 0
    errors: int = 0
    parent_id: int = -1
    generation: int = 0

    def __repr__(self):
        return f"Org(id={self.id}, gen={self.generation}, age={self.age}, children={self.children})"


class Soup:
    """The primordial soup — shared memory where organisms live."""
    
    def __init__(self, size: int = 4096, mutation_rate: float = 0.001):
        self.memory = [NOP] * size   # the soup
        self.size = size
        self.mutation_rate = mutation_rate
        self.organisms: List[Organism] = []
        self.dead: List[int] = []    # ids of dead organisms
        self.next_id = 0
        self.cycle = 0
        self.total_births = 0
        self.total_deaths = 0
        self.max_organisms = 100     # reaper threshold
        self.history: List[str] = []
        
    def inject(self, genome: List[int], pos: int = 0) -> Organism:
        """Inject a genome into the soup at position pos."""
        for i, byte in enumerate(genome):
            if pos + i < self.size:
                self.memory[pos + i] = byte
        org = Organism(
            id=self.next_id,
            start=pos,
            length=len(genome),
            ip=pos
        )
        self.next_id += 1
        self.organisms.append(org)
        self.log(f"INJECT org {org.id} at {pos}, length {len(genome)}")
        return org
    
    def log(self, msg: str):
        entry = f"[{self.cycle:06d}] {msg}"
        self.history.append(entry)
        if len(self.history) > 1000:
            self.history = self.history[-500:]
    
    def read_mem(self, addr: int) -> int:
        """Read from soup memory with wrapping."""
        return self.memory[addr % self.size]
    
    def write_mem(self, addr: int, val: int):
        """Write to soup memory with wrapping and possible mutation."""
        actual_addr = addr % self.size
        if random.random() < self.mutation_rate:
            val = random.randint(0, 15)  # cosmic ray!
            self.log(f"  MUTATION at {actual_addr}: wrote {val} instead")
        self.memory[actual_addr] = val
    
    def find_marker(self, start: int, label: int, direction: int) -> Optional[int]:
        """Search for MARK instruction with given label. Returns address or None."""
        pos = start
        for _ in range(self.size):
            pos = (pos + direction) % self.size
            if self.memory[pos] == MARK and self.memory[(pos+1) % self.size] == label:
                return pos
        return None  # not found
    
    def allocate(self, org: Organism, size: int) -> Optional[int]:
        """Find a free region of 'size' bytes for organism to use as child space."""
        # Simple strategy: find a gap not owned by any living organism
        occupied = set()
        for o in self.organisms:
            if o.alive:
                for i in range(o.length):
                    occupied.add((o.start + i) % self.size)
                if o.alloc_start >= 0:
                    for i in range(o.alloc_size):
                        occupied.add((o.alloc_start + i) % self.size)
        
        # Scan for contiguous free region
        candidate_start = (org.start + org.length) % self.size
        for attempt in range(self.size):
            start = (candidate_start + attempt) % self.size
            free = True
            for i in range(size):
                if (start + i) % self.size in occupied:
                    free = False
                    break
            if free:
                return start
        return None  # soup is full
    
    def step_organism(self, org: Organism):
        """Execute one instruction for an organism."""
        if not org.alive:
            return
        
        org.age += 1
        ip = org.ip % self.size
        opcode = self.memory[ip]
        
        # Fetch argument if needed
        arg = None
        if opcode in HAS_ARG:
            arg = self.memory[(ip + 1) % self.size]
            next_ip = (ip + 2) % self.size
        else:
            next_ip = (ip + 1) % self.size
        
        A, B, C, D = org.regs['A'], org.regs['B'], org.regs['C'], org.regs['D']
        
        try:
            if opcode == NOP:
                pass
            
            elif opcode == MARK:
                pass  # markers are just findable, they don't execute
            
            elif opcode == FIND_FWD:
                result = self.find_marker(ip, arg, +1)
                if result is not None:
                    org.regs['A'] = result
                else:
                    org.errors += 1
            
            elif opcode == FIND_BWD:
                result = self.find_marker(ip, arg, -1)
                if result is not None:
                    org.regs['A'] = result
                else:
                    org.errors += 1
            
            elif opcode == MOV_AB:
                org.regs['B'] = org.regs['A']
            
            elif opcode == SUB_AB:
                # Length = end - start + 2 (to include the MARK and its arg at end)
                org.regs['C'] = org.regs['B'] - org.regs['A'] + 2
                if org.regs['C'] <= 0:
                    org.regs['C'] += self.size  # handle wrapping
            
            elif opcode == ALLOC:
                size = org.regs['C']
                if size > 0 and size < self.size // 2:
                    addr = self.allocate(org, size)
                    if addr is not None:
                        org.regs['D'] = addr
                        org.alloc_start = addr
                        org.alloc_size = size
                        self.log(f"  org {org.id} ALLOC {size} bytes at {addr}")
                    else:
                        org.errors += 1
                else:
                    org.errors += 1
            
            elif opcode == COPY_I:
                src = org.regs['A'] % self.size
                dst = org.regs['D'] % self.size
                self.write_mem(dst, self.read_mem(src))
                org.regs['A'] = (org.regs['A'] + 1) % self.size
                org.regs['D'] = (org.regs['D'] + 1) % self.size
            
            elif opcode == DEC_C:
                org.regs['C'] -= 1
            
            elif opcode == JNZ_C:
                if org.regs['C'] > 0:
                    result = self.find_marker(ip, arg, -1)
                    if result is not None:
                        next_ip = result  # jump to the marker
                    else:
                        org.errors += 1
            
            elif opcode == SPLIT:
                if org.alloc_start >= 0 and org.alloc_size > 0:
                    child = Organism(
                        id=self.next_id,
                        start=org.alloc_start,
                        length=org.alloc_size,
                        ip=org.alloc_start,
                        parent_id=org.id,
                        generation=org.generation + 1
                    )
                    self.next_id += 1
                    self.organisms.append(child)
                    org.children += 1
                    org.alloc_start = -1
                    org.alloc_size = 0
                    self.total_births += 1
                    self.log(f"  BIRTH! org {child.id} (gen {child.generation}) from org {org.id}")
                else:
                    org.errors += 1
            
            elif opcode == HALT:
                org.alive = False
                self.total_deaths += 1
                self.log(f"  org {org.id} HALTED (age={org.age}, children={org.children})")
                return
            
            else:
                pass  # unknown opcode = NOP
                
        except Exception as e:
            org.errors += 1
            self.log(f"  org {org.id} ERROR: {e}")
        
        org.ip = next_ip
        
        # Kill if too many errors
        if org.errors > 50:
            org.alive = False
            self.total_deaths += 1
            self.log(f"  org {org.id} DIED (too many errors)")
    
    def reap(self):
        """Kill oldest organisms if population exceeds max."""
        alive = [o for o in self.organisms if o.alive]
        if len(alive) > self.max_organisms:
            # Kill the oldest
            alive.sort(key=lambda o: o.age, reverse=True)
            for o in alive[self.max_organisms:]:
                o.alive = False
                self.total_deaths += 1
                self.log(f"  REAPED org {o.id} (age={o.age})")
    
    def step(self):
        """One tick of the soup. Each alive organism gets one instruction."""
        self.cycle += 1
        alive = [o for o in self.organisms if o.alive]
        random.shuffle(alive)  # fair scheduling
        for org in alive:
            self.step_organism(org)
        self.reap()
    
    def stats(self) -> dict:
        alive = [o for o in self.organisms if o.alive]
        gens = Counter(o.generation for o in alive)
        return {
            'cycle': self.cycle,
            'alive': len(alive),
            'total_births': self.total_births,
            'total_deaths': self.total_deaths,
            'generations': dict(gens),
            'max_generation': max((o.generation for o in alive), default=0),
            'oldest_age': max((o.age for o in alive), default=0),
        }
    
    def dump_organism(self, org: Organism) -> str:
        """Show an organism's state."""
        genome = [self.memory[(org.start + i) % self.size] for i in range(org.length)]
        decoded = []
        i = 0
        while i < len(genome):
            op = genome[i]
            name = INST_NAMES.get(op, f'?{op}')
            if op in HAS_ARG and i+1 < len(genome):
                decoded.append(f"{name}({genome[i+1]})")
                i += 2
            else:
                decoded.append(name)
                i += 1
        return (f"Org {org.id} [gen={org.generation} age={org.age} children={org.children} "
                f"errs={org.errors}]\n"
                f"  regs: {org.regs}\n"
                f"  ip: {org.ip} (offset {org.ip - org.start})\n"
                f"  genome: {' '.join(decoded)}")


def trace_ancestor(cycles=100):
    """Run ancestor with full trace to verify it works."""
    soup = Soup(size=512, mutation_rate=0.0)  # no mutation for testing
    org = soup.inject(ANCESTOR, pos=0)
    
    print(f"=== ANCESTOR TRACE (genome length: {len(ANCESTOR)}) ===")
    print(f"Genome: {ANCESTOR}")
    print()
    
    for i in range(cycles):
        ip = org.ip
        opcode = soup.memory[ip % soup.size]
        name = INST_NAMES.get(opcode, f'?{opcode}')
        arg_str = ""
        if opcode in HAS_ARG:
            arg_str = f"({soup.memory[(ip+1) % soup.size]})"
        
        print(f"  step {i:3d} | ip={ip:3d} (offset {ip-org.start:2d}) | "
              f"{name}{arg_str:4s} | A={org.regs['A']:4d} B={org.regs['B']:4d} "
              f"C={org.regs['C']:4d} D={org.regs['D']:4d} | "
              f"children={org.children} errs={org.errors}")
        
        if not org.alive:
            print(f"\n  Organism stopped. children={org.children}")
            break
        
        soup.step()
    
    print(f"\n=== RESULT ===")
    s = soup.stats()
    print(f"Alive: {s['alive']}, Births: {s['total_births']}, "
          f"Max gen: {s['max_generation']}")
    
    # Show all organisms
    for o in soup.organisms:
        print(f"\n{soup.dump_organism(o)}")
    
    # Verify: did the child get a correct copy?
    if soup.total_births > 0:
        child = [o for o in soup.organisms if o.parent_id == org.id][0]
        parent_genome = ANCESTOR
        child_genome = [soup.memory[(child.start + i) % soup.size] 
                       for i in range(child.length)]
        match = parent_genome == child_genome
        print(f"\n  GENOME MATCH: {match}")
        if not match:
            for i, (p, c) in enumerate(zip(parent_genome, child_genome)):
                if p != c:
                    print(f"    diff at {i}: parent={p} child={c}")
    
    return soup


def run_ecology(cycles=5000, report_every=500):
    """Run a full ecological simulation."""
    soup = Soup(size=8192, mutation_rate=0.002)
    soup.max_organisms = 50
    
    # Inject one ancestor
    soup.inject(ANCESTOR, pos=0)
    
    print("=== TIERRA ECOLOGY ===")
    print(f"Soup size: {soup.size}, Mutation rate: {soup.mutation_rate}")
    print(f"Ancestor length: {len(ANCESTOR)}")
    print()
    
    for cycle in range(cycles):
        soup.step()
        
        if (cycle + 1) % report_every == 0:
            s = soup.stats()
            alive = [o for o in soup.organisms if o.alive]
            lengths = Counter(o.length for o in alive)
            print(f"Cycle {s['cycle']:6d} | alive={s['alive']:3d} | "
                  f"births={s['total_births']:4d} deaths={s['total_deaths']:4d} | "
                  f"max_gen={s['max_generation']:3d} | "
                  f"sizes={dict(lengths)}")
    
    # Final report
    print(f"\n=== FINAL STATE ===")
    s = soup.stats()
    print(f"Cycles: {s['cycle']}")
    print(f"Alive: {s['alive']}")
    print(f"Total births: {s['total_births']}")
    print(f"Total deaths: {s['total_deaths']}")
    print(f"Max generation: {s['max_generation']}")
    print(f"Generations distribution: {s['generations']}")
    
    alive = [o for o in soup.organisms if o.alive]
    if alive:
        print(f"\nSample organisms:")
        for o in alive[:5]:
            print(f"  {soup.dump_organism(o)}")
    
    # Show last events
    print(f"\nRecent events:")
    for entry in soup.history[-20:]:
        print(f"  {entry}")
    
    return soup


if __name__ == '__main__':
    import sys
    if '--ecology' in sys.argv:
        run_ecology()
    else:
        trace_ancestor()