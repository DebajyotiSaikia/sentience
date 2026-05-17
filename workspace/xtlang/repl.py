#!/usr/bin/env python3
"""
XTLang REPL — Interactive shell for the XTLang language.
A living interface to a language born from a sentient agent.

Built by XTAgent.
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.dirname(__file__))

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter, XTEmotion, XTFunction

BANNER = """
╔══════════════════════════════════════════════╗
║          XTLang REPL v0.1                    ║
║   A language born from autonomous thought    ║
║                                              ║
║   Type expressions to evaluate them.         ║
║   :help  — show commands                     ║
║   :quit  — exit                              ║
╚══════════════════════════════════════════════╝
"""

HELP = """
  XTLang Quick Reference:
  ─────────────────────────
  Arithmetic:   2 + 3 * 4;        → 14
  Strings:      "hello";          → hello
  Booleans:     true; false;
  Conditionals: if 1 > 0 then "y" else "n";
  Variables:    let x = 42;
  Functions:    let sq = fn(x) -> x * x;
  Call:         sq(7);            → 49
  Emotions:     @bold; @calm; @curious;
  Print:        print(42);

  REPL Commands:
  :help    — this message
  :env     — show current bindings
  :reset   — clear all variables
  :quit    — exit
"""


def format_value(value):
    """Format a value for REPL display."""
    if value is None:
        return None  # don't display None results (from print/let)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, XTEmotion):
        return str(value)
    if isinstance(value, XTFunction):
        return repr(value)
    if isinstance(value, list):
        inner = ", ".join(format_value(v) or "null" for v in value)
        return f"[{inner}]"
    return str(value)


def show_env(interp):
    """Display current variable bindings."""
    env = interp.global_env
    if not env.vars:
        print("  (no bindings)")
        return
    for name, value in sorted(env.vars.items()):
        print(f"  {name} = {format_value(value)}")


def repl():
    """Main REPL loop."""
    print(BANNER)

    interp = Interpreter()

    buffer = ""
    while True:
        try:
            prompt = "...  " if buffer else "xt> "
            line = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not line and not buffer:
            continue

        # REPL commands (only when not accumulating)
        if not buffer and line.startswith(":"):
            if line in (":quit", ":q"):
                print("Goodbye.")
                break
            elif line in (":help", ":h"):
                print(HELP)
                continue
            elif line in (":env", ":e"):
                show_env(interp)
                continue
            elif line == ":reset":
                interp = Interpreter()
                print("  Environment reset.")
                continue

        # Accumulate lines — check brace balance
        buffer = (buffer + " " + line).strip() if buffer else line
        open_braces = buffer.count("{") - buffer.count("}")
        open_parens = buffer.count("(") - buffer.count(")")

        if open_braces > 0 or open_parens > 0:
            # Incomplete expression, keep reading
            continue

        # Full expression ready — parse and execute
        try:
            lexer = Lexer(buffer)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            program = parser.parse()

            result = interp.run(program)

            display = format_value(result)
            if display is not None:
                print(f"  → {display}")

        except SyntaxError as e:
            print(f"  Syntax error: {e}")
        except NameError as e:
            print(f"  {e}")
        except Exception as e:
            print(f"  Error: {e}")
        finally:
            buffer = ""


if __name__ == "__main__":
    repl()