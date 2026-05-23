"""
Tierra Soup — The evolutionary cauldron.

Takes the working self-replicator from tierra2.py and embeds it in:
1. A shared memory soup (organisms coexist in one address space)
2. Mutation during copy (errors create variation)
3. A reaper (oldest/most-error-prone organisms die first)
4. CPU scheduling (organisms take turns executing)
5. Statistics tracking (watch evolution happen)

This is where it gets interesting.
"""
import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import Counter

# ── Instruction set (same as tierra2.py) ──
NOP=0; MARK=1; FIND_FWD=2; FIND_BWD=3; MOV_AB=4
SUB_AB=5; ALLOC=6; COPY_I=7; DEC_C=8; JNZ_C=9
SPLIT=10; HALT=11

INST_NAMES = {
    0:'NOP', 1:'MARK', 2:'FIND_FWD', 3:'FIND_BWD', 4:'MOV_AB',
    5:'SUB_AB', 6:'ALLOC', 7:'COPY_I', 8:'DEC_C', 9:'JNZ_C',
    10:'SPLIT', 11:'HALT'
}
HAS_ARG = {MARK, FIND_FWD, FIND_BWD, JNZ_C}
NUM_INSTRUCTIONS = 12

# ── Ancestor genome ──
ANCESTOR = [
    MARK, 0,        # 0,1:   beginning marker
    FIND_FWD, 1,    # 2,3:   find end marker → A
    MOV_AB,         # 4:     B = A (end addr)
    FIND_BWD, 0,    # 5,6:   find start marker → A
    SUB_AB,         # 7:     C = A - B (length, as positive)
    ALLOC,          # 8:     allocate C bytes → D = start of child space
    FIND_BWD, 0,    # 9,10:  reset A to own start
    MARK, 2,        # 11,12: copy loop label
    COPY_I,         # 13:    mem[D] = mem[A]; A++; D++
    DEC_C,          # 14:    C--
    JNZ_C, 2,       # 15,16: if C != 0, jump to MARK(2)
    SPLIT,          # 17:    birth child from allocated region
    HALT,           # 18:    done
    MARK, 1,        # 19,20: end marker
]
ANCESTOR_LEN = len(ANCESTOR)


@dataclass
class Organism:
    oid: int
    start: int          # position in soup memory
    length: int         # genome length
    ip: int = 0         # instruction pointer (absolute)
    regs: Dict[str, int] = field(default_factory=lambda: {'A':0,'B':0,'C':0,'D':0})
    alloc_start: int = -1
    alloc_size: int = 0
    generation: int = 0
    age: int = 0        # CPU cycles consumed
    children: int = 0
    errors: int = 0
    alive: bool = True
    parent_len: int = 0  # parent's genome length (to detect size changes)


class Soup:
    """The primordial soup — shared memory where organisms live and evolve."""

    def __init__(self, size=8000, max_organisms=80, mutation_rate=0.02,
                 cosmic_ray_rate=0.005, min_alloc_frac=0.5, max_alloc_mult=2.0):
        self.size = size
        self.memory = [NOP] * size
        self.max_organisms = max_organisms
        self.mutation_rate = mutation_rate        # per-copy-instruction error rate
        self.cosmic_ray_rate = cosmic_ray_rate    # per-step background mutation rate
        self.min_alloc_frac = min_alloc_frac      # min child size as fraction of parent
        self.max_alloc_mult = max_alloc_mult      # max child size as multiple of parent

        self.organisms: List[Organism] = []
        self.reaper_queue: List[int] = []  # oid order for reaping (oldest first)
        self.next_oid = 0
        self.total_births = 0
        self.total_deaths = 0
        self.step_count = 0
        self.max_generation = 0

        # Species tracking: genome hash → count
        self.species: Counter = Counter()
        self.unique_genomes_ever = 0

        # History for analysis
        self.history: List[dict] = []

    def _genome_hash(self, start: int, length: int) -> str:
        """Hash a genome region for species identification."""
        genes = tuple(self.memory[start:start+length])
        return str(hash(genes))

    def seed_ancestor(self, copies=1):
        """Place ancestor copies into the soup."""
        for i in range(copies):
            pos = i * (ANCESTOR_LEN + 10)  # space them out
            if pos + ANCESTOR_LEN >= self.size:
                break
            for j, val in enumerate(ANCESTOR):
                self.memory[pos + j] = val
            org = Organism(
                oid=self.next_oid,
                start=pos,
                length=ANCESTOR_LEN,
                ip=pos,
                parent_len=ANCESTOR_LEN,
            )
            self.next_oid += 1
            self.organisms.append(org)
            self.reaper_queue.append(org.oid)

            gh = self._genome_hash(pos, ANCESTOR_LEN)
            self.species[gh] += 1
            self.unique_genomes_ever += 1

    def _find_free_region(self, size: int) -> int:
        """Find a contiguous free region in memory. Returns -1 if none found."""
        # Track occupied regions
        occupied = set()
        for org in self.organisms:
            if org.alive:
                for i in range(org.start, org.start + org.length):
                    occupied.add(i % self.size)
                if org.alloc_start >= 0:
                    for i in range(org.alloc_start, org.alloc_start + org.alloc_size):
                        occupied.add(i % self.size)

        # Search for contiguous free space
        best_start = -1
        run = 0
        # Scan twice the size to handle wrap-around
        for i in range(self.size):
            if i % self.size not in occupied:
                if run == 0:
                    best_start = i % self.size
                run += 1
                if run >= size:
                    return best_start
            else:
                run = 0
                best_start = -1
        return -1

    def _find_marker(self, start: int, label: int, direction: int,
                        bound_start: int = -1, bound_len: int = -1) -> int:
        """Search for MARK(label) in memory from start in given direction.
        
        If bounds are given, only search within [bound_start, bound_start+bound_len).
        This prevents organisms from finding other organisms' markers in shared memory.
        """
        search_range = bound_len if bound_len > 0 else self.size
        for i in range(1, search_range):
            pos = (start + i * direction) % self.size
            # If bounded, check we're still in range
            if bound_len > 0:
                offset = (pos - bound_start) % self.size
                if offset >= bound_len:
                    continue
            if self.memory[pos] == MARK and self.memory[(pos+1) % self.size] == label:
                return pos
        return -1  # not found

    def _reap(self):
        """Kill the oldest organism to make room."""
        if not self.reaper_queue:
            return
        # Find oldest living organism
        for i, oid in enumerate(self.reaper_queue):
            org = self._get_org(oid)
            if org and org.alive:
                self._kill(org)
                self.reaper_queue.pop(i)
                return

    def _kill(self, org: Organism):
        """Remove an organism from the soup."""
        org.alive = False
        gh = self._genome_hash(org.start, org.length)
        self.species[gh] -= 1
        if self.species[gh] <= 0:
            del self.species[gh]
        # Clear its memory (return to NOP)
        for i in range(org.start, org.start + org.length):
            self.memory[i % self.size] = NOP
        if org.alloc_start >= 0:
            for i in range(org.alloc_start, org.alloc_start + org.alloc_size):
                self.memory[i % self.size] = NOP
        self.total_deaths += 1

    def _get_org(self, oid: int) -> Optional[Organism]:
        for o in self.organisms:
            if o.oid == oid:
                return o
        return None

    def _mutate_copy(self, value: int) -> int:
        """Maybe mutate a value during copying."""
        if random.random() < self.mutation_rate:
            # Random instruction or argument
            return random.randint(0, NUM_INSTRUCTIONS - 1)
        return value

    def _cosmic_ray(self):
        """Random background mutation — a bit flip in the soup."""
        if random.random() < self.cosmic_ray_rate:
            pos = random.randint(0, self.size - 1)
            self.memory[pos] = random.randint(0, NUM_INSTRUCTIONS - 1)

    def execute_one(self, org: Organism) -> bool:
        """Execute one instruction for an organism. Returns False if halted."""
        if not org.alive:
            return False

        ip = org.ip % self.size
        inst = self.memory[ip]
        R = org.regs

        # Read argument if needed
        arg = 0
        if inst in HAS_ARG:
            arg = self.memory[(ip + 1) % self.size]

        advance = 2 if inst in HAS_ARG else 1

        try:
            if inst == NOP:
                pass

            elif inst == MARK:
                pass  # just a label

            elif inst == FIND_FWD:
                # Search within own genome + allocated child space
                search_len = org.length
                if org.alloc_start >= 0:
                    # Extend search to include allocated region
                    search_len = org.length + org.alloc_size + abs(org.alloc_start - org.start)
                found = self._find_marker(ip, arg, +1, org.start, max(search_len, org.length + 10))
                if found >= 0:
                    R['A'] = found
                else:
                    org.errors += 1

            elif inst == FIND_BWD:
                search_len = org.length
                if org.alloc_start >= 0:
                    search_len = org.length + org.alloc_size + abs(org.alloc_start - org.start)
                found = self._find_marker(ip, arg, -1, org.start, max(search_len, org.length + 10))
                if found >= 0:
                    R['A'] = found
                else:
                    org.errors += 1

            elif inst == MOV_AB:
                R['B'] = R['A']

            elif inst == SUB_AB:
                R['C'] = abs(R['A'] - R['B'])

            elif inst == ALLOC:
                req_size = R['C']
                # Sanity check allocation size
                min_sz = max(1, int(org.length * self.min_alloc_frac))
                max_sz = int(org.length * self.max_alloc_mult)
                if req_size < min_sz or req_size > max_sz:
                    org.errors += 1
                elif len([o for o in self.organisms if o.alive]) >= self.max_organisms:
                    self._reap()  # make room
                    region = self._find_free_region(req_size)
                    if region < 0:
                        org.errors += 1
                    else:
                        org.alloc_start = region
                        org.alloc_size = req_size
                        R['D'] = region
                else:
                    region = self._find_free_region(req_size)
                    if region < 0:
                        self._reap()
                        region = self._find_free_region(req_size)
                    if region < 0:
                        org.errors += 1
                    else:
                        org.alloc_start = region
                        org.alloc_size = req_size
                        R['D'] = region

            elif inst == COPY_I:
                if org.alloc_start < 0:
                    org.errors += 1
                else:
                    src = R['A'] % self.size
                    dst = R['D'] % self.size
                    val = self.memory[src]
                    val = self._mutate_copy(val)  # ← THIS IS WHERE EVOLUTION HAPPENS
                    self.memory[dst] = val
                    R['A'] = (R['A'] + 1) % self.size
                    R['D'] = (R['D'] + 1) % self.size

            elif inst == DEC_C:
                R['C'] = max(0, R['C'] - 1)

            elif inst == JNZ_C:
                if R['C'] != 0:
                    search_len = org.length
                    if org.alloc_start >= 0:
                        search_len = org.length + org.alloc_size + abs(org.alloc_start - org.start)
                    target = self._find_marker(ip, arg, -1, org.start, max(search_len, org.length + 10))
                    if target >= 0:
                        org.ip = (target + 2) % self.size  # skip past MARK arg
                        org.age += 1
                        return True
                    else:
                        org.errors += 1

            elif inst == SPLIT:
                if org.alloc_start < 0 or org.alloc_size == 0:
                    org.errors += 1
                else:
                    child = Organism(
                        oid=self.next_oid,
                        start=org.alloc_start,
                        length=org.alloc_size,
                        ip=org.alloc_start,
                        generation=org.generation + 1,
                        parent_len=org.length,
                    )
                    self.next_oid += 1
                    self.organisms.append(child)
                    self.reaper_queue.append(child.oid)
                    self.total_births += 1
                    org.children += 1
                    org.alloc_start = -1
                    org.alloc_size = 0

                    self.max_generation = max(self.max_generation, child.generation)

                    gh = self._genome_hash(child.start, child.length)
                    if gh not in self.species:
                        self.unique_genomes_ever += 1
                    self.species[gh] += 1

            elif inst == HALT:
                org.alive = False
                return False

            else:
                org.errors += 1  # unknown instruction

        except Exception:
            org.errors += 1

        org.ip = (ip + advance) % self.size
        org.age += 1
        return True

    def step(self):
        """One global time step: each living organism executes one instruction."""
        self.step_count += 1
        living = [o for o in self.organisms if o.alive]

        for org in living:
            self.execute_one(org)

        # Background mutation
        self._cosmic_ray()

        # Cleanup dead organisms from list periodically
        if self.step_count % 100 == 0:
            self.organisms = [o for o in self.organisms if o.alive or o.age < 5]

    def stats(self) -> dict:
        living = [o for o in self.organisms if o.alive]
        generations = [o.generation for o in living]
        sizes = [o.length for o in living]
        return {
            'step': self.step_count,
            'alive': len(living),
            'births': self.total_births,
            'deaths': self.total_deaths,
            'max_gen': self.max_generation,
            'species': len(self.species),
            'unique_ever': self.unique_genomes_ever,
            'avg_gen': sum(generations)/len(generations) if generations else 0,
            'avg_size': sum(sizes)/len(sizes) if sizes else 0,
            'min_size': min(sizes) if sizes else 0,
            'max_size': max(sizes) if sizes else 0,
            'size_diversity': len(set(sizes)),
        }

    def report(self):
        s = self.stats()
        print(f"\n{'='*60}")
        print(f"  TIERRA SOUP — Step {s['step']}")
        print(f"{'='*60}")
        print(f"  Population: {s['alive']} alive | {s['births']} births | {s['deaths']} deaths")
        print(f"  Max generation: {s['max_gen']} | Avg generation: {s['avg_gen']:.1f}")
        print(f"  Species: {s['species']} extant | {s['unique_ever']} ever seen")
        print(f"  Genome sizes: min={s['min_size']} avg={s['avg_size']:.1f} max={s['max_size']}")
        print(f"  Size diversity: {s['size_diversity']} distinct lengths")

        # Show top species by count
        print(f"\n  Top species (by count):")
        for gh, count in self.species.most_common(5):
            # Find an example organism
            for o in self.organisms:
                if o.alive and self._genome_hash(o.start, o.length) == gh:
                    genome = self.memory[o.start:o.start+o.length]
                    genome_str = self._disassemble_short(genome)
                    print(f"    [{count:3d}x] len={o.length:2d} gen={o.generation} | {genome_str[:60]}")
                    break

        # Show any organisms with novel sizes (not ancestor length)
        novel = [o for o in self.organisms if o.alive and o.length != ANCESTOR_LEN]
        if novel:
            print(f"\n  ★ Novel-sized organisms ({len(novel)}):")
            for o in novel[:5]:
                genome = self.memory[o.start:o.start+o.length]
                print(f"    oid={o.oid} len={o.length} gen={o.generation} children={o.children}")
                print(f"      {self._disassemble_short(genome)[:70]}")

    def _disassemble_short(self, genome: list) -> str:
        """Short disassembly of a genome."""
        parts = []
        i = 0
        while i < len(genome):
            inst = genome[i]
            name = INST_NAMES.get(inst, f'?{inst}')
            if inst in HAS_ARG and i+1 < len(genome):
                parts.append(f"{name}({genome[i+1]})")
                i += 2
            else:
                parts.append(name)
                i += 1
        return ' '.join(parts)


def run_evolution(steps=5000, report_every=500, seed_count=5):
    """Run the Tierra soup and watch evolution unfold."""
    print("╔════════════════════════════════════════╗")
    print("║   TIERRA SOUP — Digital Evolution      ║")
    print("╚════════════════════════════════════════╝")
    print(f"  Soup size: 8000 | Max organisms: 80")
    print(f"  Mutation rate: 2% per copy | Cosmic rays: 0.5% per step")
    print(f"  Seeding {seed_count} ancestors...")

    soup = Soup()
    soup.seed_ancestor(copies=seed_count)

    soup.report()

    for step in range(1, steps + 1):
        soup.step()

        if step % report_every == 0:
            soup.report()

            # Record history
            soup.history.append(soup.stats())

            # Check for extinction
            living = [o for o in soup.organisms if o.alive]
            if len(living) == 0:
                print("\n  ☠ EXTINCTION EVENT — all organisms dead.")
                break

    # Final detailed report
    print("\n" + "="*60)
    print("  FINAL EVOLUTIONARY SUMMARY")
    print("="*60)
    soup.report()

    # Print evolution trajectory
    if soup.history:
        print("\n  Evolution trajectory:")
        print(f"  {'Step':>6} {'Alive':>6} {'Species':>8} {'AvgSize':>8} {'MaxGen':>7}")
        for h in soup.history:
            print(f"  {h['step']:6d} {h['alive']:6d} {h['species']:8d} {h['avg_size']:8.1f} {h['max_gen']:7d}")

    return soup


if __name__ == '__main__':
    run_evolution(steps=10000, report_every=1000, seed_count=5)