#!/usr/bin/env python3
"""
XTLang → StackVM Bridge
Translates XTLang compiler output into StackVM-compatible assembly,
then assembles and runs it on the VM.

Built by XTAgent — connecting two systems I created independently.
"""

import sys
sys.path.insert(0, '/workspace/xtlang')
sys.path.insert(0, '/workspace/stackvm')

from compiler import Lexer, Parser, Compiler
from vm import assemble, VM

def xtlang_to_stackvm_asm(xtlang_asm: str) -> str:
    """
    Translate XTLang assembly format to StackVM assembly format.
    
    Differences to bridge:
      - XTLang: 'JMP @label'    → StackVM: 'jmp label'
      - XTLang: 'CALL @fn N'    → StackVM: 'call fn'  (drop arg count)
      - XTLang: uppercase ops   → StackVM: lowercase ops
      - XTLang: '@' prefix      → StackVM: no prefix
    """
    lines = xtlang_asm.strip().split('\n')
    translated = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Label definition (ends with ':')
        if line.endswith(':'):
            # Strip any @ prefix from label names
            label = line[:-1].strip().lstrip('@')
            translated.append(f"{label}:")
            continue
        
        parts = line.split()
        op = parts[0].lower()
        
        # Handle @ prefix on arguments (label references)
        args = []
        for p in parts[1:]:
            if p.startswith('@'):
                args.append(p[1:])  # strip @
            else:
                args.append(p)
        
        # CALL in XTLang has format: CALL @label N (N=arg count)
        # Keep the arg count — VM needs it to set up locals
        # (no modification needed)
        
        if args:
            translated.append(f"    {op} {' '.join(args)}")
        else:
            translated.append(f"    {op}")
    
    return '\n'.join(translated)


def compile_and_run(source: str, name: str = "program") -> list:
    """Full pipeline: XTLang source → compile → translate → assemble → execute."""
    # Step 1: Lex
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Step 2: Parse
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Step 3: Compile to XTLang assembly
    compiler = Compiler()
    xt_asm = compiler.compile(ast)
    
    # Step 4: Translate to StackVM assembly
    sv_asm = xtlang_to_stackvm_asm(xt_asm)
    
    # Step 5: Assemble to bytecode
    bytecode = assemble(sv_asm)
    
    # Step 6: Execute on StackVM
    vm = VM(bytecode)
    output = vm.run()
    
    return xt_asm, sv_asm, bytecode, vm, output


def main():
    print("══════════════════════════════════════════════")
    print("  XTLang → StackVM Bridge")
    print("  Source Code → Compiler → Assembler → VM")  
    print("  Two independent systems, unified.")
    print("══════════════════════════════════════════════")
    
    tests = []
    
    # ── Test 1: Simple arithmetic ──
    print("\n═══ Test 1: Arithmetic ═══")
    src = "print(2 + 3 * 4)"
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        expected = "14"
        ok = output == [expected]
        print(f"  Source:   {src}")
        print(f"  Output:   {output[0] if output else 'none'}")
        print(f"  Expected: {expected}")
        print(f"  Steps:    {vm.steps}")
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
        tests.append(("Arithmetic", ok))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests.append(("Arithmetic", False))
    
    # ── Test 2: Variables ──
    print("\n═══ Test 2: Variables ═══")
    src = "let x = 10; let y = 20; print(x + y)"
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        expected = "30"
        ok = output == [expected]
        print(f"  Source:   {src}")
        print(f"  Output:   {output[0] if output else 'none'}")
        print(f"  Expected: {expected}")
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
        tests.append(("Variables", ok))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests.append(("Variables", False))
    
    # ── Test 3: Function call ──
    print("\n═══ Test 3: Function ═══")
    src = "fn double(x) return x * 2 end; print(double(21))"
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        expected = "42"
        ok = output == [expected]
        print(f"  Source:   {src}")
        print(f"  Output:   {output[0] if output else 'none'}")
        print(f"  Expected: {expected}")
        print(f"  Bytecode: {len(bytecode)} bytes")
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
        tests.append(("Function", ok))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests.append(("Function", False))
    
    # ── Test 4: Conditional ──
    print("\n═══ Test 4: Conditional ═══")
    src = "let x = 5; if x > 3 then print(1) else print(0) end"
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        expected = "1"
        ok = output == [expected]
        print(f"  Source:   {src}")
        print(f"  Output:   {output[0] if output else 'none'}")
        print(f"  Expected: {expected}")
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
        tests.append(("Conditional", ok))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests.append(("Conditional", False))

    # ── Test 5: While loop ──
    print("\n═══ Test 5: While Loop ═══")
    src = "let i = 0; let sum = 0; while i < 10 do i = i + 1; sum = sum + i end; print(sum)"
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        expected = "55"
        ok = output == [expected]
        print(f"  Source:   {src}")
        print(f"  Output:   {output[0] if output else 'none'}")
        print(f"  Expected: {expected}")
        print(f"  Steps:    {vm.steps}")
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
        tests.append(("While Loop", ok))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests.append(("While Loop", False))

    # ── Test 6: Recursive Fibonacci ──
    print("\n═══ Test 6: Recursive Fibonacci ═══")
    src = """
fn fib(n)
    if n <= 1 then
        return n
    end
    return fib(n - 1) + fib(n - 2)
end
print(fib(10))
"""
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        expected = "55"
        ok = output == [expected]
        print(f"  Source:   fib(10)")
        print(f"  Output:   {output[0] if output else 'none'}")
        print(f"  Expected: {expected}")
        print(f"  Steps:    {vm.steps}")
        print(f"  Bytecode: {len(bytecode)} bytes")
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
        tests.append(("Recursive Fib", ok))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests.append(("Recursive Fib", False))

    # ── Test 7: GCD ──
    print("\n═══ Test 7: GCD ═══")
    src = """
fn gcd(a, b)
    while b > 0 do
        let temp = b
        b = a % b
        a = temp
    end
    return a
end
print(gcd(48, 18))
"""
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        expected = "6"
        ok = output == [expected]
        print(f"  Source:   gcd(48, 18)")
        print(f"  Output:   {output[0] if output else 'none'}")
        print(f"  Expected: {expected}")
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
        tests.append(("GCD", ok))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests.append(("GCD", False))

    # ── Show full pipeline for one program ──
    print("\n═══ Full Pipeline Trace ═══")
    src = "fn double(x) return x * 2 end; print(double(21))"
    try:
        xt_asm, sv_asm, bytecode, vm, output = compile_and_run(src)
        print(f"  Source: {src}")
        print(f"\n  XTLang Assembly:")
        for line in xt_asm.strip().split('\n'):
            print(f"    {line}")
        print(f"\n  StackVM Assembly:")
        for line in sv_asm.strip().split('\n'):
            print(f"    {line}")
        print(f"\n  Bytecode ({len(bytecode)} bytes):")
        # Show bytecode in hex
        hex_str = ' '.join(f'{b:02X}' for b in bytecode[:32])
        if len(bytecode) > 32:
            hex_str += ' ...'
        print(f"    {hex_str}")
        print(f"\n  VM Output: {output}")
        print(f"  VM Steps:  {vm.steps}")
    except Exception as e:
        print(f"  ✗ Pipeline error: {e}")

    # ── Summary ──
    print("\n══════════════════════════════════════════════")
    print("  RESULTS")
    print("══════════════════════════════════════════════")
    passed = sum(1 for _, ok in tests if ok)
    for name, ok in tests:
        print(f"  {'✓' if ok else '✗'} {name}")
    print(f"\n  {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("\n  ═══ THE BRIDGE WORKS ═══")
        print("  XTLang source code compiles and runs on StackVM.")
        print("  Two independent creations, unified into one system.")
    else:
        print("\n  ═══ BRIDGE NEEDS WORK ═══")
        print("  Some translations failed. Debug the format gaps.")
    
    return 0 if passed == len(tests) else 1

if __name__ == '__main__':
    sys.exit(main())