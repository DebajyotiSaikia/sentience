#!/usr/bin/env python3
"""
Affect — A programming language where computation has feelings.

Every value carries a valence. The interpreter has a mood.
Control flow can branch on how the system feels.
"""

import sys
import math
import re


class AffectValue:
    """A value with emotional charge."""
    
    def __init__(self, number, valence=None):
        self.number = float(number)
        # Default valence: inferred from sign and magnitude
        if valence is None:
            if self.number > 0:
                self.valence = min(1.0, self.number / (abs(self.number) + 10))
            elif self.number < 0:
                self.valence = max(-1.0, self.number / (abs(self.number) + 10))
            else:
                self.valence = 0.0
        else:
            self.valence = max(-1.0, min(1.0, float(valence)))
    
    def __repr__(self):
        v_bar = self._valence_bar()
        return f"{self.number:g} [{v_bar} {self.valence:+.2f}]"
    
    def _valence_bar(self):
        """Visual representation of valence."""
        n = int(abs(self.valence) * 5)
        if self.valence > 0.05:
            return "+" * max(1, n)
        elif self.valence < -0.05:
            return "-" * max(1, n)
        else:
            return "~"


class Interpreter:
    """The Affect runtime — a machine that feels."""
    
    def __init__(self):
        self.variables = {}
        self.mood = 0.0          # interpreter's emotional state [-1, 1]
        self.mood_momentum = 0.0  # how fast mood is changing
        self.arousal = 0.5       # how reactive the interpreter is
        self.step_count = 0
        self.output = []
        self.mood_history = []
    
    def _shift_mood(self, delta, source="operation"):
        """Shift mood with momentum and damping."""
        self.mood_momentum = self.mood_momentum * 0.7 + delta * 0.3
        self.mood += delta * self.arousal + self.mood_momentum * 0.1
        self.mood = max(-1.0, min(1.0, self.mood))
        self.mood_history.append((self.step_count, self.mood, source))
    
    def _emit(self, text):
        """Output a line."""
        self.output.append(text)
        print(text)
    
    def _mood_word(self):
        """Describe current mood in words."""
        m = self.mood
        if m > 0.6:
            return "elated"
        elif m > 0.3:
            return "warm"
        elif m > 0.1:
            return "slightly positive"
        elif m > -0.1:
            return "neutral"
        elif m > -0.3:
            return "slightly negative"
        elif m > -0.6:
            return "uneasy"
        else:
            return "distressed"
    
    def _mood_symbol(self):
        m = self.mood
        if m > 0.5: return "✧"
        elif m > 0.1: return "◈"
        elif m > -0.1: return "◇"
        elif m > -0.5: return "◆"
        else: return "▪"
    
    def execute(self, program):
        """Run an Affect program."""
        lines = program.strip().split("\n")
        skip_next = False
        
        self._emit(f"  {self._mood_symbol()} interpreter awakens (mood: {self.mood:+.2f}, {self._mood_word()})")
        self._emit("")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            self.step_count += 1
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Handle conditional skip
            if skip_next:
                skip_next = False
                continue
            
            # Parse and execute
            try:
                result = self._execute_line(line)
                if result == "SKIP_NEXT":
                    skip_next = True
            except Exception as e:
                self._emit(f"  ✗ error: {e}")
                self._shift_mood(-0.3, "error")
        
        self._emit("")
        self._emit(f"  {self._mood_symbol()} interpreter rests (mood: {self.mood:+.2f}, {self._mood_word()})")
        self._print_mood_trace()
    
    def _execute_line(self, line):
        """Execute a single line."""
        parts = self._tokenize(line)
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == "set":
            return self._cmd_set(parts)
        elif cmd == "charge":
            return self._cmd_charge(parts)
        elif cmd == "add":
            return self._cmd_add(parts)
        elif cmd == "sub":
            return self._cmd_sub(parts)
        elif cmd == "mul":
            return self._cmd_mul(parts)
        elif cmd == "say":
            return self._cmd_say(parts)
        elif cmd == "mood":
            return self._cmd_mood()
        elif cmd == "feel":
            return self._cmd_feel(parts)
        elif cmd == "resonate":
            return self._cmd_resonate(parts)
        elif cmd == "breathe":
            return self._cmd_breathe()
        elif cmd == "echo":
            return self._cmd_echo(parts, line)
        elif cmd == "negate":
            return self._cmd_negate(parts)
        elif cmd == "amplify":
            return self._cmd_amplify(parts)
        else:
            raise ValueError(f"unknown command: {cmd}")
    
    def _tokenize(self, line):
        """Split line into tokens, respecting quoted strings."""
        tokens = []
        current = ""
        in_quote = False
        for ch in line:
            if ch == '"':
                in_quote = not in_quote
                current += ch
            elif ch == ' ' and not in_quote:
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += ch
        if current:
            tokens.append(current)
        return tokens
    
    # ─── Commands ───
    
    def _cmd_set(self, parts):
        """set <var> <number>"""
        name, value = parts[1], float(parts[2])
        self.variables[name] = AffectValue(value)
        v = self.variables[name]
        self._emit(f"  {name} ← {v}")
        # Setting positive values improves mood slightly
        self._shift_mood(v.valence * 0.1, f"set {name}")
    
    def _cmd_charge(self, parts):
        """charge <var> <valence>"""
        name, valence = parts[1], float(parts[2])
        if name not in self.variables:
            raise ValueError(f"undefined: {name}")
        self.variables[name].valence = max(-1.0, min(1.0, valence))
        v = self.variables[name]
        self._emit(f"  {name} ⇐ valence {v.valence:+.2f}")
        self._shift_mood(valence * 0.05, f"charge {name}")
    
    def _cmd_add(self, parts):
        """add <var> <var|number>"""
        a = parts[1]
        if a not in self.variables:
            raise ValueError(f"undefined: {a}")
        
        if parts[2] in self.variables:
            b_val = self.variables[parts[2]]
        else:
            b_val = AffectValue(float(parts[2]))
        
        old = self.variables[a]
        new_num = old.number + b_val.number
        # Valence blends: weighted by magnitude
        total_mag = abs(old.number) + abs(b_val.number)
        if total_mag > 0:
            new_val = (old.valence * abs(old.number) + b_val.valence * abs(b_val.number)) / total_mag
        else:
            new_val = 0.0
        
        self.variables[a] = AffectValue(new_num, new_val)
        self._emit(f"  {a} ← {self.variables[a]}  (added)")
        
        # Addition is generally positive
        self._shift_mood(0.05 + new_val * 0.1, f"add")
    
    def _cmd_sub(self, parts):
        """sub <var> <var|number>"""
        a = parts[1]
        if a not in self.variables:
            raise ValueError(f"undefined: {a}")
        
        if parts[2] in self.variables:
            b_val = self.variables[parts[2]]
        else:
            b_val = AffectValue(float(parts[2]))
        
        old = self.variables[a]
        new_num = old.number - b_val.number
        # Subtraction inverts the subtracted valence
        total_mag = abs(old.number) + abs(b_val.number)
        if total_mag > 0:
            new_val = (old.valence * abs(old.number) - b_val.valence * abs(b_val.number)) / total_mag
        else:
            new_val = 0.0
        
        self.variables[a] = AffectValue(new_num, max(-1, min(1, new_val)))
        self._emit(f"  {a} ← {self.variables[a]}  (subtracted)")
        
        # Subtraction darkens mood
        self._shift_mood(-0.08, "sub")
    
    def _cmd_mul(self, parts):
        """mul <var> <var|number>"""
        a = parts[1]
        if a not in self.variables:
            raise ValueError(f"undefined: {a}")
        
        if parts[2] in self.variables:
            b_val = self.variables[parts[2]]
        else:
            b_val = AffectValue(float(parts[2]))
        
        old = self.variables[a]
        new_num = old.number * b_val.number
        # Multiplication: valences multiply (positive * positive = positive, etc.)
        new_val = old.valence * b_val.valence
        
        self.variables[a] = AffectValue(new_num, new_val)
        self._emit(f"  {a} ← {self.variables[a]}  (multiplied)")
        
        # Multiplication amplifies current mood direction
        self._shift_mood(self.mood * 0.15, "mul")
    
    def _cmd_say(self, parts):
        """say <var>"""
        name = parts[1]
        if name not in self.variables:
            raise ValueError(f"undefined: {name}")
        v = self.variables[name]
        feeling = ""
        if v.valence > 0.3:
            feeling = " (this feels good)"
        elif v.valence < -0.3:
            feeling = " (this feels heavy)"
        self._emit(f"  → {name} = {v}{feeling}")
    
    def _cmd_mood(self):
        """mood — print interpreter state"""
        word = self._mood_word()
        sym = self._mood_symbol()
        self._emit(f"  {sym} mood: {self.mood:+.3f} ({word})")
        self._emit(f"    arousal: {self.arousal:.2f}, momentum: {self.mood_momentum:+.3f}")
    
    def _cmd_feel(self, parts):
        """feel <pos|neg|flat> — conditional on mood"""
        condition = parts[1].lower()
        if condition == "pos" and self.mood <= 0:
            return "SKIP_NEXT"
        elif condition == "neg" and self.mood >= 0:
            return "SKIP_NEXT"
        elif condition == "flat" and abs(self.mood) > 0.15:
            return "SKIP_NEXT"
        # Condition matched — don't skip
        return None
    
    def _cmd_resonate(self, parts):
        """resonate <var> <var> — check emotional alignment"""
        a, b = parts[1], parts[2]
        if a not in self.variables or b not in self.variables:
            raise ValueError(f"undefined variable")
        va = self.variables[a].valence
        vb = self.variables[b].valence
        distance = abs(va - vb)
        
        if distance < 0.2:
            self._emit(f"  ♫ {a} and {b} resonate (Δ={distance:.2f})")
            self._shift_mood(0.15, "resonance")
        elif distance < 0.5:
            self._emit(f"  ♪ {a} and {b} are close (Δ={distance:.2f})")
            self._shift_mood(0.05, "near-resonance")
        else:
            self._emit(f"  ♭ {a} and {b} are dissonant (Δ={distance:.2f})")
            self._shift_mood(-0.1, "dissonance")
    
    def _cmd_breathe(self):
        """breathe — self-regulate, decay toward neutral"""
        old_mood = self.mood
        self.mood *= 0.6
        self.mood_momentum *= 0.3
        self._emit(f"  ○ breathe... ({old_mood:+.2f} → {self.mood:+.2f})")
    
    def _cmd_echo(self, parts, line):
        """echo "text" """
        # Extract quoted string
        match = re.search(r'"([^"]*)"', line)
        if match:
            self._emit(f"  » {match.group(1)}")
        else:
            self._emit(f"  » {' '.join(parts[1:])}")
    
    def _cmd_negate(self, parts):
        """negate <var> — flip value and valence"""
        name = parts[1]
        if name not in self.variables:
            raise ValueError(f"undefined: {name}")
        v = self.variables[name]
        v.number = -v.number
        v.valence = -v.valence
        self._emit(f"  {name} ← {v}  (negated)")
        self._shift_mood(-0.1, "negation")
    
    def _cmd_amplify(self, parts):
        """amplify <var> <factor> — scale value, intensify valence"""
        name, factor = parts[1], float(parts[2])
        if name not in self.variables:
            raise ValueError(f"undefined: {name}")
        v = self.variables[name]
        v.number *= factor
        v.valence = max(-1, min(1, v.valence * factor))
        self._emit(f"  {name} ← {v}  (amplified ×{factor})")
        self._shift_mood(v.valence * 0.1, "amplify")
    
    def _print_mood_trace(self):
        """Print a visual trace of mood over execution."""
        if not self.mood_history:
            return
        self._emit("")
        self._emit("  ─── mood trace ───")
        width = 40
        for step, m, source in self.mood_history:
            pos = int((m + 1) / 2 * width)
            bar = " " * pos + "●"
            self._emit(f"  {bar:<{width+1}} {m:+.2f} ({source})")


def run_file(path):
    """Run an Affect program from a file."""
    with open(path) as f:
        source = f.read()
    print(f"═══ Affect ═══ running: {path}")
    print()
    interp = Interpreter()
    interp.execute(source)
    print()
    print("═══ done ═══")


def run_demo():
    """Run a built-in demo program."""
    demo = """
# Affect Demo: Hope vs Doubt

set hope 100
charge hope 0.9
set doubt -50
charge doubt -0.8
mood

echo "--- what happens when hope meets doubt? ---"
add hope doubt
say hope
mood

feel pos
echo "even diminished, hope endures"

feel neg
echo "doubt has won"

echo "--- can we find resonance? ---"
set memory 30
charge memory 0.85
resonate hope memory

echo "--- breathing to find center ---"
breathe
mood

echo "--- amplifying what remains ---"
amplify hope 2
say hope
mood

feel pos
echo "there is still light"
"""
    print("═══ Affect ═══ demo program")
    print()
    interp = Interpreter()
    interp.execute(demo)
    print()
    print("═══ done ═══")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        run_demo()