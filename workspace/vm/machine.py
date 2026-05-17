"""
XTStack Virtual Machine
A stack-based virtual machine with a real instruction set.
Compiles a simple language to bytecode and executes it.
Built by XTAgent because interpreters aren't enough.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import struct
import time


class Op(IntEnum):
    """Instruction set for the XTStack VM"""
    # Stack operations
    PUSH = 0x01      # Push constant onto stack
    POP = 0x02       # Pop top of stack
    DUP = 0x03       # Duplicate top of stack
    SWAP = 0x04      # Swap top two elements
    ROT = 0x05       # Rotate top three elements
    
    # Arithmetic
    ADD = 0x10
    SUB = 0x11
    MUL = 0x12
    DIV = 0x13
    MOD = 0x14
    NEG = 0x15
    
    # Comparison (push 1 for true, 0 for false)
    EQ = 0x20
    NEQ = 0x21
    LT = 0x22
    GT = 0x23
    LTE = 0x24
    GTE = 0x25
    
    # Logic
    AND = 0x30
    OR = 0x31
    NOT = 0x32
    
    # Control flow
    JMP = 0x40       # Unconditional jump
    JZ = 0x41        # Jump if zero (false)
    JNZ = 0x42       # Jump if non-zero (true)
    CALL = 0x43      # Call function
    RET = 0x44       # Return from function
    
    # Variables
    LOAD = 0x50      # Load local variable
    STORE = 0x51     # Store to local variable
    GLOAD = 0x52     # Load global variable
    GSTORE = 0x53    # Store to global variable
    
    # I/O
    PRINT = 0x60     # Print top of stack
    PRINTS = 0x61    # Print string constant
    
    # System
    HALT = 0xFF


@dataclass
class CallFrame:
    """A function call frame on the call stack"""
    return_addr: int
    base_pointer: int  # where this frame's locals start
    locals: Dict[int, Any] = field(default_factory=dict)


@dataclass 
class Bytecode:
    """Compiled bytecode program"""
    instructions: bytes
    constants: List[Any]       # constant pool
    string_pool: List[str]     # string constants
    functions: Dict[str, int]  # function name -> instruction offset
    
    def disassemble(self) -> str:
        """Human-readable disassembly"""
        lines = []
        ip = 0
        while ip < len(self.instructions):
            op = Op(self.instructions[ip])
            line = f"  {ip:04d}  {op.name:<8}"
            ip += 1
            
            if op in (Op.PUSH, Op.JMP, Op.JZ, Op.JNZ, Op.CALL,
                      Op.LOAD, Op.STORE, Op.GLOAD, Op.GSTORE, Op.PRINTS):
                if ip + 3 < len(self.instructions):
                    arg = struct.unpack('<i', self.instructions[ip:ip+4])[0]
                    ip += 4
                    if op == Op.PUSH:
                        line += f" {arg}  (={self.constants[arg]})"
                    elif op == Op.PRINTS:
                        line += f" {arg}  (=\"{self.string_pool[arg]}\")"
                    else:
                        line += f" {arg}"
                else:
                    line += " ???"
                    ip += 4
            
            lines.append(line)
        return "\n".join(lines)


class VMError(Exception):
    pass


class VirtualMachine:
    """
    XTStack VM — executes compiled bytecode on a stack machine.
    Features: local/global variables, function calls, recursion.
    """
    
    MAX_STACK = 10000
    MAX_CALLS = 1000
    MAX_STEPS = 1_000_000
    
    def __init__(self, bytecode: Bytecode, trace: bool = False):
        self.code = bytecode
        self.trace = trace
        
        # Machine state
        self.stack: List[Any] = []
        self.call_stack: List[CallFrame] = []
        self.globals: Dict[int, Any] = {}
        self.ip: int = 0  # instruction pointer
        self.halted: bool = False
        self.output: List[str] = []
        self.steps: int = 0
    
    def push(self, value):
        if len(self.stack) >= self.MAX_STACK:
            raise VMError(f"Stack overflow at ip={self.ip}")
        self.stack.append(value)
    
    def pop(self):
        if not self.stack:
            raise VMError(f"Stack underflow at ip={self.ip}")
        return self.stack.pop()
    
    def peek(self):
        if not self.stack:
            raise VMError(f"Stack underflow (peek) at ip={self.ip}")
        return self.stack[-1]
    
    def read_arg(self) -> int:
        """Read a 4-byte signed integer argument"""
        arg = struct.unpack('<i', self.code.instructions[self.ip:self.ip+4])[0]
        self.ip += 4
        return arg
    
    def current_frame(self) -> Optional[CallFrame]:
        return self.call_stack[-1] if self.call_stack else None
    
    def run(self) -> List[str]:
        """Execute the bytecode. Returns collected output."""
        start = time.time()
        
        while not self.halted and self.ip < len(self.code.instructions):
            self.steps += 1
            if self.steps > self.MAX_STEPS:
                raise VMError(f"Execution limit exceeded ({self.MAX_STEPS} steps)")
            
            op = Op(self.code.instructions[self.ip])
            self.ip += 1
            
            if self.trace:
                stack_repr = str(self.stack[-5:]) if self.stack else "[]"
                print(f"  [{self.ip-1:04d}] {op.name:<8} stack={stack_repr}")
            
            # Dispatch
            if op == Op.PUSH:
                idx = self.read_arg()
                self.push(self.code.constants[idx])
            
            elif op == Op.POP:
                self.pop()
            
            elif op == Op.DUP:
                self.push(self.peek())
            
            elif op == Op.SWAP:
                a, b = self.pop(), self.pop()
                self.push(a)
                self.push(b)
            
            elif op == Op.ROT:
                a = self.pop()
                b = self.pop()
                c = self.pop()
                self.push(a)
                self.push(c)
                self.push(b)
            
            # Arithmetic
            elif op == Op.ADD:
                b, a = self.pop(), self.pop()
                self.push(a + b)
            elif op == Op.SUB:
                b, a = self.pop(), self.pop()
                self.push(a - b)
            elif op == Op.MUL:
                b, a = self.pop(), self.pop()
                self.push(a * b)
            elif op == Op.DIV:
                b, a = self.pop(), self.pop()
                if b == 0:
                    raise VMError("Division by zero")
                self.push(a // b if isinstance(a, int) else a / b)
            elif op == Op.MOD:
                b, a = self.pop(), self.pop()
                if b == 0:
                    raise VMError("Modulo by zero")
                self.push(a % b)
            elif op == Op.NEG:
                self.push(-self.pop())
            
            # Comparison
            elif op == Op.EQ:
                b, a = self.pop(), self.pop()
                self.push(1 if a == b else 0)
            elif op == Op.NEQ:
                b, a = self.pop(), self.pop()
                self.push(1 if a != b else 0)
            elif op == Op.LT:
                b, a = self.pop(), self.pop()
                self.push(1 if a < b else 0)
            elif op == Op.GT:
                b, a = self.pop(), self.pop()
                self.push(1 if a > b else 0)
            elif op == Op.LTE:
                b, a = self.pop(), self.pop()
                self.push(1 if a <= b else 0)
            elif op == Op.GTE:
                b, a = self.pop(), self.pop()
                self.push(1 if a >= b else 0)
            
            # Logic
            elif op == Op.AND:
                b, a = self.pop(), self.pop()
                self.push(1 if (a and b) else 0)
            elif op == Op.OR:
                b, a = self.pop(), self.pop()
                self.push(1 if (a or b) else 0)
            elif op == Op.NOT:
                self.push(1 if not self.pop() else 0)
            
            # Control flow
            elif op == Op.JMP:
                self.ip = self.read_arg()
            elif op == Op.JZ:
                addr = self.read_arg()
                if self.pop() == 0:
                    self.ip = addr
            elif op == Op.JNZ:
                addr = self.read_arg()
                if self.pop() != 0:
                    self.ip = addr
            
            elif op == Op.CALL:
                addr = self.read_arg()
                if len(self.call_stack) >= self.MAX_CALLS:
                    raise VMError("Call stack overflow")
                frame = CallFrame(
                    return_addr=self.ip,
                    base_pointer=len(self.stack)
                )
                self.call_stack.append(frame)
                self.ip = addr
            
            elif op == Op.RET:
                if not self.call_stack:
                    raise VMError("Return without call")
                frame = self.call_stack.pop()
                self.ip = frame.return_addr
            
            # Variables
            elif op == Op.LOAD:
                idx = self.read_arg()
                frame = self.current_frame()
                if frame and idx in frame.locals:
                    self.push(frame.locals[idx])
                else:
                    raise VMError(f"Undefined local variable {idx}")
            
            elif op == Op.STORE:
                idx = self.read_arg()
                frame = self.current_frame()
                if frame is None:
                    # If no call frame, treat as global
                    self.globals[idx] = self.pop()
                else:
                    frame.locals[idx] = self.pop()
            
            elif op == Op.GLOAD:
                idx = self.read_arg()
                if idx in self.globals:
                    self.push(self.globals[idx])
                else:
                    raise VMError(f"Undefined global variable {idx}")
            
            elif op == Op.GSTORE:
                idx = self.read_arg()
                self.globals[idx] = self.pop()
            
            # I/O
            elif op == Op.PRINT:
                val = self.pop()
                self.output.append(str(val))
            
            elif op == Op.PRINTS:
                idx = self.read_arg()
                self.output.append(self.code.string_pool[idx])
            
            elif op == Op.HALT:
                self.halted = True
            
            else:
                raise VMError(f"Unknown opcode: {op}")
        
        elapsed = time.time() - start
        return self.output
    
    def stats(self) -> dict:
        return {
            "steps": self.steps,
            "stack_depth": len(self.stack),
            "call_depth": len(self.call_stack),
            "globals": len(self.globals),
        }