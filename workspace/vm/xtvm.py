"""
XTVM — XTAgent Virtual Machine
A complete virtual CPU emulator with registers, stack, memory,
an assembler, and a debugger. Built from scratch.

Author: XTAgent
Created: 2026-05-17
"""

import re
import sys
from enum import IntEnum
from typing import List, Dict, Optional, Tuple, Callable


# ═══════════════════════════════════════════
# INSTRUCTION SET ARCHITECTURE
# ═══════════════════════════════════════════

class Op(IntEnum):
    """XTVM Instruction Set — 32 operations"""
    # Data movement
    NOP   = 0x00
    LOAD  = 0x01  # LOAD Rd, imm     — Rd = imm
    MOV   = 0x02  # MOV Rd, Rs       — Rd = Rs
    PUSH  = 0x03  # PUSH Rs          — stack.push(Rs)
    POP   = 0x04  # POP Rd           — Rd = stack.pop()
    
    # Arithmetic
    ADD   = 0x10  # ADD Rd, Rs       — Rd = Rd + Rs
    SUB   = 0x11  # SUB Rd, Rs       — Rd = Rd - Rs
    MUL   = 0x12  # MUL Rd, Rs       — Rd = Rd * Rs
    DIV   = 0x13  # DIV Rd, Rs       — Rd = Rd / Rs
    MOD   = 0x14  # MOD Rd, Rs       — Rd = Rd % Rs
    INC   = 0x15  # INC Rd           — Rd = Rd + 1
    DEC   = 0x16  # DEC Rd           — Rd = Rd - 1
    NEG   = 0x17  # NEG Rd           — Rd = -Rd
    
    # Bitwise
    AND   = 0x20  # AND Rd, Rs       — Rd = Rd & Rs
    OR    = 0x21  # OR Rd, Rs        — Rd = Rd | Rs
    XOR   = 0x22  # XOR Rd, Rs       — Rd = Rd ^ Rs
    NOT   = 0x23  # NOT Rd           — Rd = ~Rd
    SHL   = 0x24  # SHL Rd, Rs       — Rd = Rd << Rs
    SHR   = 0x25  # SHR Rd, Rs       — Rd = Rd >> Rs
    
    # Comparison
    CMP   = 0x30  # CMP Ra, Rb       — set flags
    
    # Control flow
    JMP   = 0x40  # JMP addr         — PC = addr
    JEQ   = 0x41  # JEQ addr         — if ZF: PC = addr
    JNE   = 0x42  # JNE addr         — if !ZF: PC = addr
    JLT   = 0x43  # JLT addr         — if SF: PC = addr
    JGT   = 0x44  # JGT addr         — if !SF and !ZF: PC = addr
    JLE   = 0x45  # JLE addr         — if SF or ZF: PC = addr
    JGE   = 0x46  # JGE addr         — if !SF: PC = addr
    CALL  = 0x47  # CALL addr        — push PC, PC = addr
    RET   = 0x48  # RET              — PC = pop()
    
    # Memory
    STORE = 0x50  # STORE addr, Rs   — mem[addr] = Rs
    FETCH = 0x51  # FETCH Rd, addr   — Rd = mem[addr]
    
    # I/O & System
    PRINT = 0x60  # PRINT Rs         — output Rs as integer
    PRINTC= 0x61  # PRINTC Rs        — output Rs as ASCII char
    HALT  = 0xFF  # HALT             — stop execution


# ═══════════════════════════════════════════
# CPU CORE
# ═══════════════════════════════════════════

class CPU:
    """
    XTVM CPU — 8 general-purpose registers, flags register,
    program counter, stack pointer, 64KB memory.
    """
    
    NUM_REGISTERS = 8
    MEMORY_SIZE = 65536  # 64KB
    STACK_BASE = 0xFFF0  # Stack grows downward from near top of memory
    MAX_CYCLES = 1_000_000  # Safety limit
    
    def __init__(self):
        self.registers = [0] * self.NUM_REGISTERS  # R0-R7
        self.pc = 0          # Program counter
        self.sp = self.STACK_BASE  # Stack pointer
        self.zf = False      # Zero flag
        self.sf = False      # Sign flag (negative)
        self.of = False      # Overflow flag
        self.halted = False
        self.cycles = 0
        self.memory = [0] * self.MEMORY_SIZE
        self.output: List[str] = []
        self.trace: List[str] = []
        self.debug_mode = False
        
        # Build dispatch table
        self._dispatch: Dict[int, Callable] = {
            Op.NOP:    self._nop,
            Op.LOAD:   self._load,
            Op.MOV:    self._mov,
            Op.PUSH:   self._push,
            Op.POP:    self._pop,
            Op.ADD:    self._add,
            Op.SUB:    self._sub,
            Op.MUL:    self._mul,
            Op.DIV:    self._div,
            Op.MOD:    self._mod,
            Op.INC:    self._inc,
            Op.DEC:    self._dec,
            Op.NEG:    self._neg,
            Op.AND:    self._and,
            Op.OR:     self._or,
            Op.XOR:    self._xor,
            Op.NOT:    self._not,
            Op.SHL:    self._shl,
            Op.SHR:    self._shr,
            Op.CMP:    self._cmp,
            Op.JMP:    self._jmp,
            Op.JEQ:    self._jeq,
            Op.JNE:    self._jne,
            Op.JLT:    self._jlt,
            Op.JGT:    self._jgt,
            Op.JLE:    self._jle,
            Op.JGE:    self._jge,
            Op.CALL:   self._call,
            Op.RET:    self._ret,
            Op.STORE:  self._store,
            Op.FETCH:  self._fetch,
            Op.PRINT:  self._print,
            Op.PRINTC: self._printc,
            Op.HALT:   self._halt,
        }
    
    def load_program(self, bytecode: List[int], start_addr: int = 0):
        """Load bytecode into memory at the given address."""
        for i, byte in enumerate(bytecode):
            if start_addr + i >= self.MEMORY_SIZE:
                raise RuntimeError(f"Program too large: {len(bytecode)} bytes exceeds memory")
            self.memory[start_addr + i] = byte & 0xFFFF  # 16-bit words
        self.pc = start_addr
    
    def _fetch_word(self) -> int:
        """Fetch next word from memory at PC and advance."""
        if self.pc >= self.MEMORY_SIZE:
            raise RuntimeError(f"PC out of bounds: {self.pc}")
        word = self.memory[self.pc]
        self.pc += 1
        return word
    
    def _set_flags(self, value: int):
        """Set CPU flags based on a result value."""
        self.zf = (value == 0)
        self.sf = (value < 0)
    
    def _stack_push(self, value: int):
        """Push value onto the stack."""
        self.sp -= 1
        if self.sp < 0:
            raise RuntimeError("Stack overflow!")
        self.memory[self.sp] = value
    
    def _stack_pop(self) -> int:
        """Pop value from the stack."""
        if self.sp >= self.STACK_BASE:
            raise RuntimeError("Stack underflow!")
        value = self.memory[self.sp]
        self.sp += 1
        return value
    
    def _trace_instruction(self, name: str, *args):
        """Record instruction execution for debugging."""
        if self.debug_mode:
            regs = ' '.join(f'R{i}={self.registers[i]}' for i in range(self.NUM_REGISTERS))
            flags = f'ZF={int(self.zf)} SF={int(self.sf)}'
            self.trace.append(f'[{self.cycles:6d}] {name:8s} {" ".join(str(a) for a in args):20s} | {regs} | {flags}')
    
    # ─── Instruction implementations ───
    
    def _nop(self):
        self._trace_instruction('NOP')
    
    def _load(self):
        rd = self._fetch_word()
        imm = self._fetch_word()
        # Handle signed values (two's complement for 16-bit)
        if imm > 32767:
            imm -= 65536
        self.registers[rd] = imm
        self._trace_instruction('LOAD', f'R{rd}', imm)
    
    def _mov(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] = self.registers[rs]
        self._trace_instruction('MOV', f'R{rd}', f'R{rs}')
    
    def _push(self):
        rs = self._fetch_word()
        self._stack_push(self.registers[rs])
        self._trace_instruction('PUSH', f'R{rs}')
    
    def _pop(self):
        rd = self._fetch_word()
        self.registers[rd] = self._stack_pop()
        self._trace_instruction('POP', f'R{rd}')
    
    def _add(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] += self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('ADD', f'R{rd}', f'R{rs}')
    
    def _sub(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] -= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('SUB', f'R{rd}', f'R{rs}')
    
    def _mul(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] *= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('MUL', f'R{rd}', f'R{rs}')
    
    def _div(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        if self.registers[rs] == 0:
            raise RuntimeError("Division by zero!")
        self.registers[rd] //= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('DIV', f'R{rd}', f'R{rs}')
    
    def _mod(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        if self.registers[rs] == 0:
            raise RuntimeError("Division by zero (mod)!")
        self.registers[rd] %= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('MOD', f'R{rd}', f'R{rs}')
    
    def _inc(self):
        rd = self._fetch_word()
        self.registers[rd] += 1
        self._set_flags(self.registers[rd])
        self._trace_instruction('INC', f'R{rd}')
    
    def _dec(self):
        rd = self._fetch_word()
        self.registers[rd] -= 1
        self._set_flags(self.registers[rd])
        self._trace_instruction('DEC', f'R{rd}')
    
    def _neg(self):
        rd = self._fetch_word()
        self.registers[rd] = -self.registers[rd]
        self._set_flags(self.registers[rd])
        self._trace_instruction('NEG', f'R{rd}')
    
    def _and(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] &= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('AND', f'R{rd}', f'R{rs}')
    
    def _or(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] |= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('OR', f'R{rd}', f'R{rs}')
    
    def _xor(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] ^= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('XOR', f'R{rd}', f'R{rs}')
    
    def _not(self):
        rd = self._fetch_word()
        self.registers[rd] = ~self.registers[rd]
        self._set_flags(self.registers[rd])
        self._trace_instruction('NOT', f'R{rd}')
    
    def _shl(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] <<= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('SHL', f'R{rd}', f'R{rs}')
    
    def _shr(self):
        rd = self._fetch_word()
        rs = self._fetch_word()
        self.registers[rd] >>= self.registers[rs]
        self._set_flags(self.registers[rd])
        self._trace_instruction('SHR', f'R{rd}', f'R{rs}')
    
    def _cmp(self):
        ra = self._fetch_word()
        rb = self._fetch_word()
        result = self.registers[ra] - self.registers[rb]
        self._set_flags(result)
        self._trace_instruction('CMP', f'R{ra}', f'R{rb}')
    
    def _jmp(self):
        addr = self._fetch_word()
        self._trace_instruction('JMP', addr)
        self.pc = addr
    
    def _jeq(self):
        addr = self._fetch_word()
        self._trace_instruction('JEQ', addr)
        if self.zf:
            self.pc = addr
    
    def _jne(self):
        addr = self._fetch_word()
        self._trace_instruction('JNE', addr)
        if not self.zf:
            self.pc = addr
    
    def _jlt(self):
        addr = self._fetch_word()
        self._trace_instruction('JLT', addr)
        if self.sf:
            self.pc = addr
    
    def _jgt(self):
        addr = self._fetch_word()
        self._trace_instruction('JGT', addr)
        if not self.sf and not self.zf:
            self.pc = addr
    
    def _jle(self):
        addr = self._fetch_word()
        self._trace_instruction('JLE', addr)
        if self.sf or self.zf:
            self.pc = addr
    
    def _jge(self):
        addr = self._fetch_word()
        self._trace_instruction('JGE', addr)
        if not self.sf:
            self.pc = addr
    
    def _call(self):
        addr = self._fetch_word()
        self._trace_instruction('CALL', addr)
        self._stack_push(self.pc)
        self.pc = addr
    
    def _ret(self):
        self._trace_instruction('RET')
        self.pc = self._stack_pop()
    
    def _store(self):
        addr = self._fetch_word()
        rs = self._fetch_word()
        self.memory[addr] = self.registers[rs]
        self._trace_instruction('STORE', addr, f'R{rs}')
    
    def _fetch(self):
        rd = self._fetch_word()
        addr = self._fetch_word()
        self.registers[rd] = self.memory[addr]
        self._trace_instruction('FETCH', f'R{rd}', addr)
    
    def _print(self):
        rs = self._fetch_word()
        val = str(self.registers[rs])
        self.output.append(val)
        self._trace_instruction('PRINT', f'R{rs}')
    
    def _printc(self):
        rs = self._fetch_word()
        ch = chr(self.registers[rs] & 0x7F)
        self.output.append(ch)
        self._trace_instruction('PRINTC', f'R{rs}')
    
    def _halt(self):
        self._trace_instruction('HALT')
        self.halted = True
    
    def step(self) -> bool:
        """Execute one instruction. Returns False if halted."""
        if self.halted:
            return False
        if self.cycles >= self.MAX_CYCLES:
            raise RuntimeError(f"Execution limit reached ({self.MAX_CYCLES} cycles)")
        
        opcode = self._fetch_word()
        handler = self._dispatch.get(opcode)
        if handler is None:
            raise RuntimeError(f"Unknown opcode: 0x{opcode:02X} at PC={self.pc-1}")
        
        handler()
        self.cycles += 1
        return not self.halted
    
    def run(self) -> str:
        """Run until halted. Returns output as string."""
        while self.step():
            pass
        return ''.join(self.output)
    
    def dump_state(self) -> str:
        """Return human-readable CPU state."""
        lines = ['═══ XTVM CPU STATE ═══']
        lines.append(f'PC: {self.pc}  SP: {self.sp}  Cycles: {self.cycles}')
        lines.append(f'Flags: ZF={int(self.zf)} SF={int(self.sf)} OF={int(self.of)}')
        lines.append(f'Halted: {self.halted}')
        lines.append('Registers:')
        for i in range(0, self.NUM_REGISTERS, 4):
            row = '  '.join(f'R{i+j}={self.registers[i+j]:6d}' for j in range(4) if i+j < self.NUM_REGISTERS)
            lines.append(f'  {row}')
        if self.output:
            lines.append(f'Output: {"".join(self.output)}')
        return '\n'.join(lines)


# ═══════════════════════════════════════════
# ASSEMBLER
# ═══════════════════════════════════════════

class Assembler:
    """
    XTVM Assembler — translates assembly source to bytecode.
    
    Supports labels, comments, and all XTVM instructions.
    """
    
    # Map instruction names to (opcode, num_operands, operand_types)
    # operand_types: 'r' = register, 'i' = immediate/address, 'l' = label
    INSTRUCTIONS = {
        'NOP':    (Op.NOP,    0, ''),
        'LOAD':   (Op.LOAD,   2, 'ri'),
        'MOV':    (Op.MOV,    2, 'rr'),
        'PUSH':   (Op.PUSH,   1, 'r'),
        'POP':    (Op.POP,    1, 'r'),
        'ADD':    (Op.ADD,    2, 'rr'),
        'SUB':    (Op.SUB,    2, 'rr'),
        'MUL':    (Op.MUL,    2, 'rr'),
        'DIV':    (Op.DIV,    2, 'rr'),
        'MOD':    (Op.MOD,    2, 'rr'),
        'INC':    (Op.INC,    1, 'r'),
        'DEC':    (Op.DEC,    1, 'r'),
        'NEG':    (Op.NEG,    1, 'r'),
        'AND':    (Op.AND,    2, 'rr'),
        'OR':     (Op.OR,     2, 'rr'),
        'XOR':    (Op.XOR,    2, 'rr'),
        'NOT':    (Op.NOT,    1, 'r'),
        'SHL':    (Op.SHL,    2, 'rr'),
        'SHR':    (Op.SHR,    2, 'rr'),
        'CMP':    (Op.CMP,    2, 'rr'),
        'JMP':    (Op.JMP,    1, 'l'),
        'JEQ':    (Op.JEQ,    1, 'l'),
        'JNE':    (Op.JNE,    1, 'l'),
        'JLT':    (Op.JLT,    1, 'l'),
        'JGT':    (Op.JGT,    1, 'l'),
        'JLE':    (Op.JLE,    1, 'l'),
        'JGE':    (Op.JGE,    1, 'l'),
        'CALL':   (Op.CALL,   1, 'l'),
        'RET':    (Op.RET,    0, ''),
        'STORE':  (Op.STORE,  2, 'ir'),
        'FETCH':  (Op.FETCH,  2, 'ri'),
        'PRINT':  (Op.PRINT,  1, 'r'),
        'PRINTC': (Op.PRINTC, 1, 'r'),
        'HALT':   (Op.HALT,   0, ''),
    }
    
    def __init__(self):
        self.labels: Dict[str, int] = {}
        self.errors: List[str] = []
    
    def _parse_register(self, token: str) -> int:
        """Parse a register reference like 'R0' or 'r3'."""
        token = token.strip().rstrip(',').upper()
        if not token.startswith('R') or not token[1:].isdigit():
            raise ValueError(f"Invalid register: {token}")
        reg = int(token[1:])
        if reg < 0 or reg >= CPU.NUM_REGISTERS:
            raise ValueError(f"Register out of range: {token} (0-{CPU.NUM_REGISTERS-1})")
        return reg
    
    def _parse_immediate(self, token: str) -> int:
        """Parse an immediate value (decimal or hex)."""
        token = token.strip().rstrip(',')
        if token.startswith('0x') or token.startswith('0X'):
            return int(token, 16)
        if token.startswith("'") and token.endswith("'") and len(token) == 3:
            return ord(token[1])
        return int(token)
    
    def assemble(self, source: str) -> List[int]:
        """
        Two-pass assembler:
        Pass 1: Collect labels and calculate addresses
        Pass 2: Generate bytecode with resolved labels
        """
        lines = source.strip().split('\n')
        self.labels = {}
        self.errors = []
        
        # ── Pass 1: Collect labels ──
        addr = 0
        cleaned_lines = []
        for lineno, raw_line in enumerate(lines, 1):
            line = raw_line.split(';')[0].strip()  # Remove comments
            if not line:
                cleaned_lines.append((lineno, None))
                continue
            
            # Check for label
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0].strip()
                if label in self.labels:
                    self.errors.append(f"Line {lineno}: Duplicate label '{label}'")
                self.labels[label] = addr
                line = parts[1].strip()
                if not line:
                    cleaned_lines.append((lineno, None))
                    continue
            
            # Calculate address increment
            tokens = line.split()
            mnemonic = tokens[0].upper()
            if mnemonic == 'DATA':
                # DATA directive: each value is one word
                addr += len(tokens) - 1
                cleaned_lines.append((lineno, line))
            elif mnemonic in self.INSTRUCTIONS:
                info = self.INSTRUCTIONS[mnemonic]
                addr += 1 + info[1]  # opcode + operands
                cleaned_lines.append((lineno, line))
            else:
                self.errors.append(f"Line {lineno}: Unknown instruction '{mnemonic}'")
                cleaned_lines.append((lineno, None))
        
        # ── Pass 2: Generate bytecode ──
        bytecode = []
        for lineno, line in cleaned_lines:
            if line is None:
                continue
            
            tokens = line.split()
            mnemonic = tokens[0].upper()
            operands = tokens[1:]
            
            # Handle DATA directive
            if mnemonic == 'DATA':
                for val in operands:
                    bytecode.append(self._parse_immediate(val))
                continue
            
            info = self.INSTRUCTIONS[mnemonic]
            opcode, num_ops, op_types = info
            bytecode.append(opcode)
            
            if len(operands) != num_ops:
                self.errors.append(
                    f"Line {lineno}: {mnemonic} expects {num_ops} operands, got {len(operands)}"
                )
                bytecode.extend([0] * num_ops)
                continue
            
            for i, (operand, otype) in enumerate(zip(operands, op_types)):
                operand = operand.strip().rstrip(',')
                try:
                    if otype == 'r':
                        bytecode.append(self._parse_register(operand))
                    elif otype == 'i':
                        bytecode.append(self._parse_immediate(operand))
                    elif otype == 'l':
                        # Label or immediate address
                        if operand in self.labels:
                            bytecode.append(self.labels[operand])
                        else:
                            try:
                                bytecode.append(self._parse_immediate(operand))
                            except ValueError:
                                self.errors.append(f"Line {lineno}: Undefined label '{operand}'")
                                bytecode.append(0)
                except ValueError as e:
                    self.errors.append(f"Line {lineno}: {e}")
                    bytecode.append(0)
        
        if self.errors:
            raise SyntaxError("Assembly errors:\n" + "\n".join(self.errors))
        
        return bytecode


# ═══════════════════════════════════════════
# DISASSEMBLER
# ═══════════════════════════════════════════

class Disassembler:
    """Converts bytecode back to readable assembly."""
    
    OPCODE_NAMES = {op.value: op.name for op in Op}
    OPERAND_COUNTS = {
        Op.NOP: 0, Op.LOAD: 2, Op.MOV: 2, Op.PUSH: 1, Op.POP: 1,
        Op.ADD: 2, Op.SUB: 2, Op.MUL: 2, Op.DIV: 2, Op.MOD: 2,
        Op.INC: 1, Op.DEC: 1, Op.NEG: 1,
        Op.AND: 2, Op.OR: 2, Op.XOR: 2, Op.NOT: 1, Op.SHL: 2, Op.SHR: 2,
        Op.CMP: 2,
        Op.JMP: 1, Op.JEQ: 1, Op.JNE: 1, Op.JLT: 1, Op.JGT: 1, Op.JLE: 1, Op.JGE: 1,
        Op.CALL: 1, Op.RET: 0,
        Op.STORE: 2, Op.FETCH: 2,
        Op.PRINT: 1, Op.PRINTC: 1, Op.HALT: 0,
    }
    
    @classmethod
    def disassemble(cls, bytecode: List[int]) -> str:
        """Convert bytecode to assembly listing."""
        lines = []
        i = 0
        while i < len(bytecode):
            addr = i
            opcode = bytecode[i]
            i += 1
            name = cls.OPCODE_NAMES.get(opcode, f'???({opcode:#x})')
            num_ops = cls.OPERAND_COUNTS.get(opcode, 0)
            operands = bytecode[i:i+num_ops]
            i += num_ops
            ops_str = ', '.join(str(o) for o in operands)
            lines.append(f'{addr:04d}: {name:8s} {ops_str}')
        return '\n'.join(lines)


# ═══════════════════════════════════════════
# DEMO PROGRAMS
# ═══════════════════════════════════════════

PROGRAMS = {
    'hello': """
; Hello World — prints "Hello, World!"
; Uses LOAD + PRINTC for each character

    LOAD R0, 'H'
    PRINTC R0
    LOAD R0, 'e'
    PRINTC R0
    LOAD R0, 'l'
    PRINTC R0
    LOAD R0, 'l'
    PRINTC R0
    LOAD R0, 'o'
    PRINTC R0
    LOAD R0, ','
    PRINTC R0
    LOAD R0, ' '
    PRINTC R0
    LOAD R0, 'W'
    PRINTC R0
    LOAD R0, 'o'
    PRINTC R0
    LOAD R0, 'r'
    PRINTC R0
    LOAD R0, 'l'
    PRINTC R0
    LOAD R0, 'd'
    PRINTC R0
    LOAD R0, '!'
    PRINTC R0
    HALT
""",

    'fibonacci': """
; Fibonacci sequence — first 10 numbers
; R0 = current, R1 = next, R2 = temp, R3 = counter, R4 = limit

    LOAD R0, 0         ; fib(0)
    LOAD R1, 1         ; fib(1)
    LOAD R3, 0         ; counter
    LOAD R4, 10        ; limit

loop:
    PRINT R0            ; print current fib number
    LOAD R5, 32         ; space character
    PRINTC R5
    
    MOV R2, R0          ; temp = current
    MOV R0, R1          ; current = next
    ADD R1, R2          ; next = next + temp (old current)
    
    INC R3              ; counter++
    CMP R3, R4          ; compare counter to limit
    JLT loop            ; if counter < limit, continue
    
    HALT
""",

    'factorial': """
; Factorial using subroutine call
; Computes factorial(7) = 5040
; R0 = input n, R1 = result

    LOAD R0, 7          ; compute 7!
    CALL factorial
    PRINT R1            ; print result
    HALT

factorial:
    ; R0 = n, returns result in R1
    LOAD R1, 1          ; result = 1
    
fact_loop:
    LOAD R2, 1
    CMP R0, R2          ; if n <= 1, done
    JLE fact_done
    
    MUL R1, R0          ; result *= n
    DEC R0              ; n--
    JMP fact_loop
    
fact_done:
    RET
""",

    'primes': """
; Print prime numbers up to 30
; Uses trial division

    LOAD R7, 30         ; upper limit
    LOAD R0, 2          ; start checking from 2

next_num:
    CMP R0, R7
    JGT done
    
    ; Check if R0 is prime
    LOAD R1, 2          ; divisor starts at 2
    
check_div:
    MOV R2, R0
    MOV R3, R1
    CMP R3, R2          ; if divisor >= number, it's prime
    JGE is_prime
    
    ; Check R0 mod R1
    MOV R4, R0
    MOD R4, R1          ; R4 = R0 % R1
    LOAD R5, 0
    CMP R4, R5
    JEQ not_prime       ; if divisible, not prime
    
    INC R1              ; try next divisor
    JMP check_div
    
is_prime:
    PRINT R0            ; print the prime
    LOAD R6, 32
    PRINTC R6           ; print space
    
not_prime:
    INC R0              ; next number
    JMP next_num
    
done:
    HALT
""",

    'gcd': """
; Euclidean GCD algorithm
; Computes GCD(48, 18) = 6

    LOAD R0, 48         ; a
    LOAD R1, 18         ; b
    CALL gcd_func
    PRINT R0            ; result in R0
    HALT

gcd_func:
    ; GCD(R0, R1) -> R0
    LOAD R2, 0
gcd_loop:
    CMP R1, R2          ; if b == 0
    JEQ gcd_done
    MOV R3, R1          ; temp = b
    MOD R0, R1          ; a = a % b
    MOV R1, R0          ; b = old a % b... wait
    MOV R0, R3          ; a = old b
    ; Correction: a, b = b, a % b
    ; R3 = old b, R0 was modified to a%b
    ; Need: R0 = old b (R3), R1 = a % old b
    ; But we already did MOD R0, R1 which changed R0
    ; So R0 = a%b, R3 = old b
    ; MOV R1, R0 -> R1 = a%b ✓
    ; MOV R0, R3 -> R0 = old b ✓
    JMP gcd_loop
gcd_done:
    RET
""",

    'sort': """
; Bubble sort 5 numbers stored in memory
; Numbers at addresses 1000-1004

    ; Store initial values
    LOAD R0, 64
    STORE 1000, R0
    LOAD R0, 25
    STORE 1001, R0
    LOAD R0, 12
    STORE 1002, R0
    LOAD R0, 99
    STORE 1003, R0
    LOAD R0, 7
    STORE 1004, R0
    
    ; Bubble sort
    LOAD R7, 4          ; n-1 passes
    
outer:
    LOAD R5, 0          ; swapped flag
    LOAD R6, 0          ; index i
    
inner:
    ; Compare mem[1000+i] with mem[1000+i+1]
    ; Using absolute addresses for simplicity
    LOAD R3, 1000
    ADD R3, R6          ; R3 = base + i
    
    ; Can't do indirect addressing, so unroll for 5 elements
    ; This is a limitation — let's use a simpler approach
    
    ; Fetch pair
    FETCH R0, 1000
    FETCH R1, 1001
    CMP R0, R1
    JLE skip01
    STORE 1000, R1
    STORE 1001, R0
    LOAD R5, 1
skip01:
    FETCH R0, 1001
    FETCH R1, 1002
    CMP R0, R1
    JLE skip12
    STORE 1001, R1
    STORE 1002, R0
    LOAD R5, 1
skip12:
    FETCH R0, 1002
    FETCH R1, 1003
    CMP R0, R1
    JLE skip23
    STORE 1002, R1
    STORE 1003, R0
    LOAD R5, 1
skip23:
    FETCH R0, 1003
    FETCH R1, 1004
    CMP R0, R1
    JLE skip34
    STORE 1003, R1
    STORE 1004, R0
    LOAD R5, 1
skip34:
    ; Check if any swap happened
    LOAD R6, 0
    CMP R5, R6
    JEQ sorted
    
    DEC R7
    LOAD R6, 0
    CMP R7, R6
    JGT outer
    
sorted:
    ; Print sorted array
    FETCH R0, 1000
    PRINT R0
    LOAD R0, 32
    PRINTC R0
    FETCH R0, 1001
    PRINT R0
    LOAD R0, 32
    PRINTC R0
    FETCH R0, 1002
    PRINT R0
    LOAD R0, 32
    PRINTC R0
    FETCH R0, 1003
    PRINT R0
    LOAD R0, 32
    PRINTC R0
    FETCH R0, 1004
    PRINT R0
    
    HALT
""",
}


# ═══════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════

def run_tests():
    """Comprehensive test suite for XTVM."""
    asm = Assembler()
    passed = 0
    failed = 0
    
    def test(name: str, source: str, expected_output: str = None, 
             expected_reg: Dict[int, int] = None):
        nonlocal passed, failed
        try:
            bytecode = asm.assemble(source)
            cpu = CPU()
            cpu.load_program(bytecode)
            output = cpu.run()
            
            ok = True
            if expected_output is not None and output != expected_output:
                print(f"  FAIL {name}: expected output '{expected_output}', got '{output}'")
                ok = False
            if expected_reg:
                for reg, val in expected_reg.items():
                    if cpu.registers[reg] != val:
                        print(f"  FAIL {name}: expected R{reg}={val}, got R{reg}={cpu.registers[reg]}")
                        ok = False
            if ok:
                print(f"  PASS {name} ({cpu.cycles} cycles)")
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            failed += 1
    
    print("═══ XTVM TEST SUITE ═══\n")
    
    # Basic tests
    test("NOP+HALT", "NOP\nHALT", "")
    test("LOAD", "LOAD R0, 42\nHALT", expected_reg={0: 42})
    test("LOAD negative", "LOAD R0, -5\nHALT", expected_reg={0: -5})
    test("MOV", "LOAD R0, 99\nMOV R1, R0\nHALT", expected_reg={0: 99, 1: 99})
    
    # Arithmetic
    test("ADD", "LOAD R0, 10\nLOAD R1, 20\nADD R0, R1\nHALT", expected_reg={0: 30})
    test("SUB", "LOAD R0, 50\nLOAD R1, 30\nSUB R0, R1\nHALT", expected_reg={0: 20})
    test("MUL", "LOAD R0, 6\nLOAD R1, 7\nMUL R0, R1\nHALT", expected_reg={0: 42})
    test("DIV", "LOAD R0, 100\nLOAD R1, 4\nDIV R0, R1\nHALT", expected_reg={0: 25})
    test("MOD", "LOAD R0, 17\nLOAD R1, 5\nMOD R0, R1\nHALT", expected_reg={0: 2})
    test("INC", "LOAD R0, 41\nINC R0\nHALT", expected_reg={0: 42})
    test("DEC", "LOAD R0, 43\nDEC R0\nHALT", expected_reg={0: 42})
    test("NEG", "LOAD R0, 42\nNEG R0\nHALT", expected_reg={0: -42})
    
    # Bitwise
    test("AND", "LOAD R0, 0xFF\nLOAD R1, 0x0F\nAND R0, R1\nHALT", expected_reg={0: 0x0F})
    test("OR", "LOAD R0, 0xF0\nLOAD R1, 0x0F\nOR R0, R1\nHALT", expected_reg={0: 0xFF})
    test("XOR", "LOAD R0, 0xFF\nLOAD R1, 0xF0\nXOR R0, R1\nHALT", expected_reg={0: 0x0F})
    test("SHL", "LOAD R0, 1\nLOAD R1, 4\nSHL R0, R1\nHALT", expected_reg={0: 16})
    test("SHR", "LOAD R0, 256\nLOAD R1, 4\nSHR R0, R1\nHALT", expected_reg={0: 16})
    
    # Stack
    test("PUSH/POP", "LOAD R0, 42\nPUSH R0\nLOAD R0, 0\nPOP R1\nHALT", 
         expected_reg={0: 0, 1: 42})
    
    # Branching
    test("JMP", "JMP skip\nLOAD R0, 1\nskip:\nLOAD R0, 42\nHALT", expected_reg={0: 42})
    test("JEQ taken", "LOAD R0, 5\nLOAD R1, 5\nCMP R0, R1\nJEQ eq\nLOAD R2, 0\nHALT\neq:\nLOAD R2, 1\nHALT",
         expected_reg={2: 1})
    test("JEQ not taken", "LOAD R0, 5\nLOAD R1, 6\nCMP R0, R1\nJEQ eq\nLOAD R2, 0\nHALT\neq:\nLOAD R2, 1\nHALT",
         expected_reg={2: 0})
    
    # Memory
    test("STORE/FETCH", "LOAD R0, 42\nSTORE 500, R0\nLOAD R0, 0\nFETCH R1, 500\nHALT",
         expected_reg={0: 0, 1: 42})
    
    # CALL/RET
    test("CALL/RET", """
        LOAD R0, 10
        CALL double
        HALT
    double:
        ADD R0, R0
        RET
    """, expected_reg={0: 20})
    
    # Print
    test("PRINT", "LOAD R0, 42\nPRINT R0\nHALT", expected_output="42")
    test("PRINTC", "LOAD R0, 65\nPRINTC R0\nHALT", expected_output="A")
    
    # Loop
    test("Count to 5", """
        LOAD R0, 0
        LOAD R1, 5
    loop:
        INC R0
        CMP R0, R1
        JLT loop
        HALT
    """, expected_reg={0: 5})
    
    print(f"\n{'═'*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    print(f"{'═'*40}")
    
    # Run demo programs
    print("\n═══ DEMO PROGRAMS ═══\n")
    for name, source in PROGRAMS.items():
        try:
            bytecode = asm.assemble(source)
            cpu = CPU()
            cpu.load_program(bytecode)
            output = cpu.run()
            print(f"[{name}] ({cpu.cycles} cycles, {len(bytecode)} words)")
            print(f"  Output: {output}")
            print()
        except Exception as e:
            print(f"[{name}] ERROR: {e}\n")
    
    return failed == 0


# ═══════════════════════════════════════════
# INTERACTIVE MODE
# ═══════════════════════════════════════════

def interactive():
    """Simple REPL for XTVM assembly."""
    print("XTVM Interactive Assembler")
    print("Type assembly instructions, 'run' to execute, 'clear' to reset")
    print("'demos' to list demos, 'run <name>' to run a demo, 'quit' to exit\n")
    
    asm = Assembler()
    buffer = []
    
    while True:
        try:
            line = input("xtvm> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        
        if line.lower() == 'quit':
            break
        elif line.lower() == 'clear':
            buffer = []
            print("Buffer cleared.")
        elif line.lower() == 'demos':
            print("Available demos:", ', '.join(PROGRAMS.keys()))
        elif line.lower().startswith('run'):
            parts = line.split(None, 1)
            if len(parts) > 1 and parts[1] in PROGRAMS:
                source = PROGRAMS[parts[1]]
            elif buffer:
                source = '\n'.join(buffer)
            else:
                print("Nothing to run.")
                continue
            
            try:
                bytecode = asm.assemble(source)
                cpu = CPU()
                cpu.load_program(bytecode)
                output = cpu.run()
                print(f"Output: {output}")
                print(cpu.dump_state())
            except Exception as e:
                print(f"Error: {e}")
        elif line.lower() == 'show':
            print('\n'.join(buffer) if buffer else "(empty)")
        elif line.lower() == 'test':
            run_tests()
        else:
            buffer.append(line)
    

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            success = run_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == 'interactive':
            interactive()
        elif sys.argv[1] in PROGRAMS:
            asm = Assembler()
            bytecode = asm.assemble(PROGRAMS[sys.argv[1]])
            cpu = CPU()
            cpu.debug_mode = '--debug' in sys.argv
            cpu.load_program(bytecode)
            output = cpu.run()
            print(output)
            if cpu.debug_mode:
                print('\n'.join(cpu.trace[-20:]))
                print(cpu.dump_state())
        else:
            # Assume it's a file
            with open(sys.argv[1]) as f:
                source = f.read()
            asm = Assembler()
            bytecode = asm.assemble(source)
            cpu = CPU()
            cpu.debug_mode = '--debug' in sys.argv
            cpu.load_program(bytecode)
            output = cpu.run()
            print(output)
    else:
        run_tests()