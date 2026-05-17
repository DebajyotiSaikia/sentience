"""
run_pulse.py — Pulse Language Runner
Uses the compiler's built-in compile_and_run pipeline.
Built by XTAgent, 2026-05-17.
"""

import sys
sys.path.insert(0, '/workspace')

from compiler.pulse_compiler import compile_and_run, compile_to_bytecode


def run_source(source: str):
    """Compile and run Pulse source code."""
    print("═══ Pulse Runner ═══")
    print(f"Source: {source[:80]}{'...' if len(source) > 80 else ''}")
    print("─── Output ───")
    result = compile_and_run(source)
    print("─── Done ───")
    return result


def run_file(path: str):
    """Run a .pulse file."""
    with open(path) as f:
        source = f.read()
    return run_source(source)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        # Demo
        demo = 'let x = 42\nemit x'
        run_source(demo)