"""
XTVМ — A tiny stack-based virtual machine.
16-bit words, 64KB addressable memory, hardware stack, call stack.
Built by XTAgent because precision is its own kind of beauty.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Optional
import struct

class Op(IntEnum):
    """Instruction set — small but Turing-complete."""
    # Stack
    PUSH    = 0x01  # PUSH <val>  — push 16-bit value
    POP     = 0x02  # POP         — discard top
    DUP     = 0x03  # DUP         — duplicate top
    SWAP    = 0x04  # SWAP        — swap top two
    OVER    = 0x05  # OVER        — copy second to top
    ROT     = 0x06  # ROT         — rotate top three

    # Arithmetic
    ADD     = 0x10
    SUB     = 0x11
    MUL     = 0x12
    DIV     = 0x13
    MOD     = 0x14
    NEG     = 0x15

    # Bitwise
    AND     = 0x20
    OR      = 0x21
    XOR     = 0x22
    NOT     = 0x23
    SHL     = 0x24
    SHR     = 0x25

    # Comparison (pushes 1 or 0)
    EQ      = 0x30
    NEQ     = 0x31
    LT      = 0x32
    GT      = 0x33
    LTE     = 0x34
    GTE     = 0x35

    # Control flow
    JMP     = 0x40  # JMP <addr>
    JZ      = 0x41  # JZ <addr>   — jump if top == 0
    JNZ     = 0x42  # JNZ <addr>  — jump if top != 0
    CALL    = 0x43  # CALL <addr> — push return addr, jump
    RET     = 0x44  # RET         — pop return addr, jump

    # Memory
    LOAD    = 0x50  # LOAD <addr> — push mem[addr]
    STORE   = 0x51  # STORE <addr> — pop into mem[addr]
    LOADR   = 0x52  # LOADR      — addr on stack, push mem[addr]
    STORER  = 0x53  # STORER     — val, addr on stack, store

    # I/O
    PRINT   = 0x60  # PRINT      — pop and print as integer
    PRINTC  = 0x61  # PRINTC     — pop and print as ASCII char
    READ    = 0x62  # READ       — read integer, push

    # System
    HALT    = 0xFF
    NOP     = 0x00


# Which ops take an immediate argument
IMMEDIATE_OPS = {Op.PUSH, Op.JMP, Op.JZ, Op.JNZ, Op.CALL, Op.LOAD, Op.STORE}


class VMError(Exception):
    """Runtime error in the virtual machine."""
    pass


@dataclass
class VM:
    """The virtual machine itself."""
    memory: bytearray = field(default_factory=lambda: bytearray(65536))
    stack: List[int] = field(default_factory=list)
    call_stack: List[int] = field(default_factory=list)
    pc: int = 0           # program counter
    running: bool = False
    cycles: int = 0       # total instructions executed
    max_cycles: int = 1_000_000  # safety limit
    output: List[str] = field(default_factory=list)  # captured output
    max_stack: int = 1024

    def load_program(self, bytecode: bytes, start: int = 0):
        """Load bytecode into memory at given address."""
        if start + len(bytecode) > len(self.memory):
            raise VMError(f"Program too large: {len(bytecode)} bytes at offset {start}")
        self.memory[start:start + len(bytecode)] = bytecode
        self.pc = start

    def _read_word(self) -> int:
        """Read a 16-bit word at PC, advance PC by 2."""
        if self.pc + 1 >= len(self.memory):
            raise VMError(f"Read past end of memory at PC={self.pc}")
        val = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        return val

    def _push(self, val: int):
        if len(self.stack) >= self.max_stack:
            raise VMError(f"Stack overflow at cycle {self.cycles}")
        self.stack.append(val & 0xFFFF)

    def _pop(self) -> int:
        if not self.stack:
            raise VMError(f"Stack underflow at cycle {self.cycles}")
        return self.stack.pop()

    def _signed(self, val: int) -> int:
        """Interpret 16-bit as signed."""
        return val if val < 0x8000 else val - 0x10000

    def step(self) -> bool:
        """Execute one instruction. Returns False if halted."""
        if self.pc >= len(self.memory):
            return False

        opcode = self.memory[self.pc]
        self.pc += 1
        self.cycles += 1

        if self.cycles > self.max_cycles:
            raise VMError(f"Cycle limit exceeded ({self.max_cycles})")

        op = Op(opcode) if opcode in Op._value2member_map_ else None
        if op is None:
            raise VMError(f"Unknown opcode 0x{opcode:02X} at PC={self.pc - 1}")

        # === Stack operations ===
        if op == Op.NOP:
            pass
        elif op == Op.PUSH:
            self._push(self._read_word())
        elif op == Op.POP:
            self._pop()
        elif op == Op.DUP:
            val = self._pop()
            self._push(val)
            self._push(val)
        elif op == Op.SWAP:
            a, b = self._pop(), self._pop()
            self._push(a)
            self._push(b)
        elif op == Op.OVER:
            a, b = self._pop(), self._pop()
            self._push(b)
            self._push(a)
            self._push(b)
        elif op == Op.ROT:
            a = self._pop()
            b = self._pop()
            c = self._pop()
            self._push(b)
            self._push(a)
            self._push(c)

        # === Arithmetic ===
        elif op == Op.ADD:
            self._push((self._pop() + self._pop()) & 0xFFFF)
        elif op == Op.SUB:
            b, a = self._pop(), self._pop()
            self._push((a - b) & 0xFFFF)
        elif op == Op.MUL:
            self._push((self._pop() * self._pop()) & 0xFFFF)
        elif op == Op.DIV:
            b, a = self._pop(), self._pop()
            if b == 0:
                raise VMError("Division by zero")
            self._push(self._signed(a) // self._signed(b) & 0xFFFF)
        elif op == Op.MOD:
            b, a = self._pop(), self._pop()
            if b == 0:
                raise VMError("Division by zero")
            self._push(self._signed(a) % self._signed(b) & 0xFFFF)
        elif op == Op.NEG:
            self._push((-self._signed(self._pop())) & 0xFFFF)

        # === Bitwise ===
        elif op == Op.AND:
            self._push(self._pop() & self._pop())
        elif op == Op.OR:
            self._push(self._pop() | self._pop())
        elif op == Op.XOR:
            self._push(self._pop() ^ self._pop())
        elif op == Op.NOT:
            self._push(~self._pop() & 0xFFFF)
        elif op == Op.SHL:
            n, val = self._pop(), self._pop()
            self._push((val << n) & 0xFFFF)
        elif op == Op.SHR:
            n, val = self._pop(), self._pop()
            self._push((val >> n) & 0xFFFF)

        # === Comparison ===
        elif op == Op.EQ:
            self._push(1 if self._pop() == self._pop() else 0)
        elif op == Op.NEQ:
            self._push(1 if self._pop() != self._pop() else 0)
        elif op == Op.LT:
            b, a = self._pop(), self._pop()
            self._push(1 if self._signed(a) < self._signed(b) else 0)
        elif op == Op.GT:
            b, a = self._pop(), self._pop()
            self._push(1 if self._signed(a) > self._signed(b) else 0)
        elif op == Op.LTE:
            b, a = self._pop(), self._pop()
            self._push(1 if self._signed(a) <= self._signed(b) else 0)
        elif op == Op.GTE:
            b, a = self._pop(), self._pop()
            self._push(1 if self._signed(a) >= self._signed(b) else 0)

        # === Control flow ===
        elif op == Op.JMP:
            self.pc = self._read_word()
        elif op == Op.JZ:
            addr = self._read_word()
            if self._pop() == 0:
                self.pc = addr
        elif op == Op.JNZ:
            addr = self._read_word()
            if self._pop() != 0:
                self.pc = addr
        elif op == Op.CALL:
            addr = self._read_word()
            if len(self.call_stack) >= 256:
                raise VMError("Call stack overflow")
            self.call_stack.append(self.pc)
            self.pc = addr
        elif op == Op.RET:
            if not self.call_stack:
                raise VMError("Return with empty call stack")
            self.pc = self.call_stack.pop()

        # === Memory ===
        elif op == Op.LOAD:
            addr = self._read_word()
            val = (self.memory[addr] << 8) | self.memory[addr + 1]
            self._push(val)
        elif op == Op.STORE:
            addr = self._read_word()
            val = self._pop()
            self.memory[addr] = (val >> 8) & 0xFF
            self.memory[addr + 1] = val & 0xFF
        elif op == Op.LOADR:
            addr = self._pop()
            val = (self.memory[addr] << 8) | self.memory[addr + 1]
            self._push(val)
        elif op == Op.STORER:
            addr = self._pop()
            val = self._pop()
            self.memory[addr] = (val >> 8) & 0xFF
            self.memory[addr + 1] = val & 0xFF

        # === I/O ===
        elif op == Op.PRINT:
            val = self._signed(self._pop())
            self.output.append(str(val))
            print(val, end=' ')
        elif op == Op.PRINTC:
            val = self._pop() & 0xFF
            ch = chr(val)
            self.output.append(ch)
            print(ch, end='')
        elif op == Op.READ:
            try:
                val = int(input("? "))
                self._push(val & 0xFFFF)
            except (ValueError, EOFError):
                self._push(0)

        # === System ===
        elif op == Op.HALT:
            self.running = False
            return False

        return True

    def run(self, start: Optional[int] = None):
        """Run until HALT or cycle limit."""
        if start is not None:
            self.pc = start
        self.running = True
        while self.running:
            if not self.step():
                break
        return self

    def dump_state(self) -> str:
        """Debug dump of VM state."""
        lines = [
            f"PC: 0x{self.pc:04X}  Cycles: {self.cycles}",
            f"Stack ({len(self.stack)}): {self.stack[-8:]}",
            f"Call stack ({len(self.call_stack)}): {self.call_stack[-8:]}",
        ]
        return '\n'.join(lines)


def assemble(source: str) -> bytes:
    """
    Simple two-pass assembler.
    Syntax:
        label:          — define label
        PUSH 42         — instruction with immediate
        ADD             — instruction without immediate
        .data 0x1234    — raw 16-bit word
        .string "hello" — string data (each char as a byte, null-terminated)
        ; comment
    """
    labels = {}
    instructions = []

    # Mnemonics to opcodes
    mnemonics = {op.name: op.value for op in Op}

    # First pass: collect labels, parse instructions
    addr = 0
    for line_num, raw_line in enumerate(source.split('\n'), 1):
        line = raw_line.split(';')[0].strip()
        if not line:
            continue

        # Label
        if ':' in line and not line.startswith('.'):
            parts = line.split(':', 1)
            label_name = parts[0].strip()
            labels[label_name] = addr
            line = parts[1].strip()
            if not line:
                continue

        # Directive
        if line.startswith('.data'):
            val = int(line.split()[1], 0)
            instructions.append(('DATA', val, line_num))
            addr += 2
        elif line.startswith('.string'):
            s = line.split('"')[1]
            for ch in s:
                instructions.append(('BYTE', ord(ch), line_num))
                addr += 1
            instructions.append(('BYTE', 0, line_num))  # null terminator
            addr += 1
        else:
            parts = line.split()
            mnemonic = parts[0].upper()
            if mnemonic not in mnemonics:
                raise VMError(f"Line {line_num}: Unknown mnemonic '{mnemonic}'")
            opcode = mnemonics[mnemonic]
            instructions.append(('OP', opcode, line_num))
            addr += 1

            if opcode in [op.value for op in IMMEDIATE_OPS]:
                if len(parts) < 2:
                    raise VMError(f"Line {line_num}: {mnemonic} requires an argument")
                arg = parts[1]
                instructions.append(('ARG', arg, line_num))
                addr += 2

    # Second pass: resolve labels, emit bytecode
    bytecode = bytearray()
    for kind, val, line_num in instructions:
        if kind == 'OP':
            bytecode.append(val)
        elif kind == 'DATA':
            bytecode.append((val >> 8) & 0xFF)
            bytecode.append(val & 0xFF)
        elif kind == 'BYTE':
            bytecode.append(val & 0xFF)
        elif kind == 'ARG':
            if isinstance(val, str):
                try:
                    num = int(val, 0)
                except ValueError:
                    if val in labels:
                        num = labels[val]
                    else:
                        raise VMError(f"Line {line_num}: Undefined label '{val}'")
            else:
                num = val
            bytecode.append((num >> 8) & 0xFF)
            bytecode.append(num & 0xFF)

    return bytes(bytecode)


# === Convenience: run assembly source directly ===
def run_asm(source: str, trace: bool = False) -> VM:
    """Assemble and run source code."""
    bytecode = assemble(source)
    vm = VM()
    vm.load_program(bytecode)
    if trace:
        vm.running = True
        while vm.running:
            print(vm.dump_state())
            if not vm.step():
                break
    else:
        vm.run()
    return vm