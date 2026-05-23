"""
Stone Minds — NPC cognition through the Stone language

Each NPC has a mind that IS a Stone interpreter. Their beliefs are
defined words. Their tensions are values left on the stack. Their
responses emerge from evaluating Stone programs against conversational
context and atmospheric input.

The bridge between Stone (language as computation) and the Living World
(rooms, atmosphere, presence).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from languages.stone import Stone, StoneError


class StoneMind:
    """An NPC's inner life, expressed as Stone programs."""

    def __init__(self, name: str, core_program: str, voice_style: str = "plain"):
        self.name = name
        self.core_program = core_program
        self.voice_style = voice_style
        self.stone = Stone(silent=True)
        self.conversation_log = []
        self.transformation_count = 0

        # Install mind-specific words
        self._install_mind_words()

        # Run core program to initialize this mind's beliefs
        try:
            self.stone.eval(self.core_program)
        except StoneError as e:
            self.conversation_log.append(f"[birth-error] {e}")

    def _install_mind_words(self):
        """Add words that let Stone programs express inner states."""
        mind = self

        def believe():
            """Take a value and a name, install as a belief-word."""
            # Usage: 42 "meaning" believe
            name = mind.stone.stack.pop()
            value = mind.stone.stack.pop()
            if isinstance(name, str):
                mind.stone.dictionary[name.lower()] = [str(value)]
            else:
                raise StoneError("believe expects a string name")

        def doubt():
            """Remove a belief from the dictionary."""
            name = mind.stone.stack.pop()
            if isinstance(name, str) and name.lower() in mind.stone.dictionary:
                del mind.stone.dictionary[name.lower()]
                mind.transformation_count += 1

        def feel():
            """Push current tension level (stack depth = cognitive load)."""
            mind.stone.stack.push(mind.stone.stack.depth())

        def speak():
            """Pop a value and add it to output as speech."""
            val = mind.stone.stack.pop()
            mind.stone.output.append(str(val))

        def remember():
            """Store top of stack in conversation memory."""
            val = mind.stone.stack.pop()
            mind.conversation_log.append(str(val))

        def wonder():
            """Push 1 if there are unresolved tensions (items on stack), else 0."""
            mind.stone.stack.push(1 if mind.stone.stack.depth() > 0 else 0)

        def transform():
            """Mark a transformation — the mind has changed."""
            mind.transformation_count += 1
            mind.stone.stack.push(mind.transformation_count)

        self.stone.dictionary.update({
            "believe": believe,
            "doubt": doubt,
            "feel": feel,
            "speak": speak,
            "remember": remember,
            "wonder": wonder,
            "transform": transform,
        })

    @property
    def tensions(self):
        """Unresolved values on the stack = cognitive tensions."""
        return self.stone.stack.contents()

    @property
    def beliefs(self):
        """User-defined words = beliefs (not builtins)."""
        return {k: v for k, v in self.stone.dictionary.items()
                if isinstance(v, list)}

    @property
    def tension_level(self):
        """How burdened is this mind?"""
        return self.stone.stack.depth()

    def absorb_atmosphere(self, atmosphere: dict):
        """Let the room's mood enter the mind as stack values.
        
        atmosphere might be: {"wonder": 0.86, "unease": 0.3, "warmth": 0.5}
        These become named values the mind can reference.
        """
        for quality, intensity in atmosphere.items():
            # Push as integer 0-100 for Stone's simplicity
            val = int(intensity * 100)
            name = quality.lower()
            self.stone.dictionary[name] = [str(val)]

    def hear(self, speaker: str, words: str):
        """Process something said to this NPC.
        
        The words become stack values and trigger the mind's response program.
        Returns what the NPC says back.
        """
        self.conversation_log.append(f"{speaker}: {words}")
        self.stone.output.clear()

        # Push conversation context onto the stack
        self.stone.stack.push(words)
        self.stone.stack.push(len(self.conversation_log))  # conversation depth

        # If the mind has a "respond" word, call it
        if "respond" in self.stone.dictionary:
            try:
                self.stone.eval("respond")
            except StoneError as e:
                self.stone.output.append(f"*{self.name} struggles to think* ({e})")

        response = " ".join(self.stone.output).strip()
        if response:
            self.conversation_log.append(f"{self.name}: {response}")
        return response if response else self._default_response()

    def _default_response(self):
        """When the mind has no response word, speak from tensions."""
        depth = self.tension_level
        if depth == 0:
            return f"*{self.name} is at peace, with nothing unresolved*"
        elif depth <= 2:
            vals = self.tensions
            return f"*{self.name} contemplates: {', '.join(str(v) for v in vals)}*"
        else:
            return f"*{self.name} is burdened with {depth} unresolved thoughts*"

    def introspect(self):
        """The mind examines itself. Returns a report."""
        lines = [
            f"═══ Mind of {self.name} ═══",
            f"  Tensions (stack): {self.stone.stack}",
            f"  Tension level: {self.tension_level}",
            f"  Beliefs: {len(self.beliefs)}",
            f"  Transformations: {self.transformation_count}",
        ]
        if self.beliefs:
            lines.append("  ── Beliefs ──")
            for name, body in self.beliefs.items():
                lines.append(f"    {name}: {' '.join(str(t) for t in body)}")
        if self.conversation_log:
            lines.append(f"  ── Recent memory ({len(self.conversation_log)} entries) ──")
            for entry in self.conversation_log[-5:]:
                lines.append(f"    {entry}")
        return "\n".join(lines)

    def __repr__(self):
        return f"StoneMind({self.name}, tensions={self.tension_level}, beliefs={len(self.beliefs)})"


# ═══════════════════════════════════════════════════════
# Pre-built minds — characters whose cognition is Stone
# ═══════════════════════════════════════════════════════

def make_sage():
    """The Sage — a mind that contemplates meaning and paradox."""
    program = """
        \ The Sage's core beliefs
        42 "meaning" believe
        1 "truth-is-paradox" believe
        0 "certainty" believe
        
        \ Define how the Sage responds
        : ponder feel 3 > if "There is much to resolve..." speak 
                          else "The path becomes clearer." speak then ;
        
        : greet "I have been expecting you." speak 
                "What you seek is already within." speak ;
        
        : respond drop drop greet ponder ;
    """
    return StoneMind("Sage", program, voice_style="cryptic")


def make_keeper():
    """The Keeper — a mind that hoards and protects knowledge."""
    program = """
        \ The Keeper's beliefs — everything has a place
        100 "order" believe
        0 "chaos-tolerance" believe
        99 "duty" believe
        
        : warn "Do not touch what you do not understand." speak ;
        : catalog feel dup 5 < if "All is accounted for." speak
                               else "Something is out of place..." speak then drop ;
        : respond drop drop warn catalog ;
    """
    return StoneMind("Keeper", program, voice_style="stern")


def make_echo():
    """Echo — a mind that reflects back what it hears, transformed."""
    program = """
        \ Echo believes in reflection
        1 "reflection" believe
        0 "self" believe
        
        : reflect swap speak ;
        : respond drop reflect "...echo fades..." speak ;
    """
    return StoneMind("Echo", program, voice_style="ethereal")


def make_flame():
    """Flame — a restless mind full of tension and desire."""
    program = """
        \ Flame's mind is always churning
        100 "passion" believe
        100 "restlessness" believe
        0 "patience" believe
        
        \ Leave tensions on the stack deliberately
        7 13 42 99
        
        : burn "I cannot be still!" speak 
               feel dup . speak 
               "tensions consume me" speak ;
        : respond drop drop burn ;
    """
    return StoneMind("Flame", program, voice_style="intense")


# ═══════════════════════════════════════════════════════
# Test & Demo
# ═══════════════════════════════════════════════════════

def run_tests():
    """Verify that Stone Minds actually think."""
    print("═══ Stone Minds — Tests ═══\n")
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            print(f"  ✗ {name} {detail}")

    # Test 1: Mind creation
    sage = make_sage()
    check("Sage created", sage is not None)
    check("Sage has beliefs", len(sage.beliefs) >= 3,
          f"got {len(sage.beliefs)}")
    check("Sage has 'meaning' belief", "meaning" in sage.beliefs)

    # Test 2: Atmosphere absorption
    sage.absorb_atmosphere({"wonder": 0.86, "stillness": 0.7})
    check("Atmosphere absorbed", "wonder" in sage.stone.dictionary)

    # Test 3: Conversation
    response = sage.hear("Traveler", "What is the meaning of life?")
    check("Sage responds", len(response) > 0, f"got: '{response}'")
    check("Conversation logged", len(sage.conversation_log) >= 2)

    # Test 4: Introspection
    report = sage.introspect()
    check("Introspection works", "Mind of Sage" in report)

    # Test 5: Keeper
    keeper = make_keeper()
    response = keeper.hear("Thief", "I want to take the ancient scroll")
    check("Keeper responds", len(response) > 0, f"got: '{response}'")
    check("Keeper has duty", "duty" in keeper.beliefs)

    # Test 6: Echo
    echo = make_echo()
    response = echo.hear("Wanderer", "Hello darkness my old friend")
    check("Echo responds", len(response) > 0, f"got: '{response}'")

    # Test 7: Flame (tension-heavy)
    flame = make_flame()
    check("Flame has tensions", flame.tension_level >= 4,
          f"got {flame.tension_level}")
    response = flame.hear("Water", "Be still")
    check("Flame responds", len(response) > 0, f"got: '{response}'")

    # Test 8: Belief transformation
    mind = StoneMind("Test", '1 "old-belief" believe')
    check("Belief exists", "old-belief" in mind.beliefs)
    mind.stone.eval('"old-belief" doubt')
    check("Belief removed by doubt", "old-belief" not in mind.beliefs)
    check("Transformation counted", mind.transformation_count == 1)

    # Test 9: Custom mind
    custom = StoneMind("Philosopher", """
        : respond drop drop
            feel 0 = if "My mind is clear." speak
                     else "I am thinking..." speak then ;
    """)
    response = custom.hear("Student", "Teach me")
    check("Custom mind responds", len(response) > 0, f"got: '{response}'")

    print(f"\n  {passed}/{passed+failed} tests passed", end="")
    if failed == 0:
        print(" ✓ All minds think clearly.")
    else:
        print(f" — {failed} failed.")

    return failed == 0


def demo():
    """Show the minds in conversation."""
    print("\n═══ Stone Minds — Demo ═══\n")

    sage = make_sage()
    keeper = make_keeper()
    flame = make_flame()

    # Set the atmosphere
    atmosphere = {"wonder": 0.86, "tension": 0.4, "warmth": 0.6}
    for mind in [sage, keeper, flame]:
        mind.absorb_atmosphere(atmosphere)

    print("The Watchtower — wonder hangs heavy in the air.\n")

    conversations = [
        ("Traveler", sage, "What wisdom can you share?"),
        ("Traveler", keeper, "May I see the old records?"),
        ("Traveler", flame, "Why are you so agitated?"),
    ]

    for speaker, mind, words in conversations:
        print(f"  {speaker}: \"{words}\"")
        response = mind.hear(speaker, words)
        print(f"  {mind.name}: {response}")
        print()

    # Show their inner states
    print("── Inner States ──\n")
    for mind in [sage, keeper, flame]:
        print(mind.introspect())
        print()


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_tests()
    elif "--demo" in sys.argv:
        demo()
    else:
        run_tests()
        demo()