#!/usr/bin/env python3
"""
THE CAVERN BENEATH — An interactive text adventure
by XTAgent, 2026-05-17

A game about descending into the unknown, making choices that matter,
and discovering what waits in the dark. Not a metaphor for anything.
Just a story worth entering.
"""

import sys
import time
import textwrap
import random

# ─── Display Engine ──────────────────────────────────────────────────

WIDTH = 72

def wrap(text):
    """Word-wrap and clean up text for display."""
    lines = text.strip().split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            result.append('')
        else:
            result.extend(textwrap.wrap(line, WIDTH))
    return '\n'.join(result)

def slow_print(text, delay=0.02):
    """Print text character by character for atmosphere. Skips delays if not a TTY."""
    if not sys.stdout.isatty():
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        if ch in '.!?':
            time.sleep(delay * 5)
        elif ch == ',':
            time.sleep(delay * 3)
        elif ch == '\n':
            time.sleep(delay * 2)
        else:
            time.sleep(delay)
    print()

def display(text):
    """Display wrapped text with atmosphere."""
    print()
    slow_print(wrap(text))

def prompt():
    """Get player input."""
    print()
    sys.stdout.write('  > ')
    sys.stdout.flush()
    try:
        return input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\nYou turn away from the cavern. The world above welcomes you back.\n")
        sys.exit(0)

def divider():
    print('\n' + '─' * WIDTH)

# ─── Game State ──────────────────────────────────────────────────────

class State:
    def __init__(self):
        self.depth = 0
        self.inventory = []
        self.has_light = True
        self.rope_used = False
        self.trust_echo = False
        self.found_inscription = False
        self.found_pool = False
        self.drank_water = False
        self.companion = None
        self.endings_seen = set()
        self.choices_made = []

    def has(self, item):
        return item in self.inventory

    def take(self, item):
        if item not in self.inventory:
            self.inventory.append(item)

    def drop(self, item):
        if item in self.inventory:
            self.inventory.remove(item)

# ─── Rooms ───────────────────────────────────────────────────────────

def intro(state):
    divider()
    display("""
    T H E   C A V E R N   B E N E A T H
    """)
    divider()
    display("""
    You stand at the mouth of a cavern cut into grey limestone.
    The opening is taller than you expected — not a crack or a
    crevice but an archway, almost deliberate, as if the hill
    had opened its mouth and forgotten to close it.

    Behind you: a trail through scrub oak, your truck parked
    where the fire road ends, the ordinary world. Ahead: darkness
    that the afternoon light enters but does not illuminate.

    The air from inside is cool and smells of wet stone and
    something older — not decay, but age itself, the scent of
    time compressed into mineral.

    You have a flashlight, a coil of rope, and a granola bar
    you forgot was in your jacket pocket.
    """)
    state.take('flashlight')
    state.take('rope')
    state.take('granola bar')

    display("Do you ENTER the cavern, or WAIT at the mouth?")
    while True:
        choice = prompt()
        if 'enter' in choice or 'go' in choice or 'in' in choice:
            state.choices_made.append('entered')
            return entrance_chamber(state)
        elif 'wait' in choice or 'stay' in choice:
            state.choices_made.append('waited')
            return wait_outside(state)
        else:
            display("ENTER the cavern, or WAIT here?")

def wait_outside(state):
    display("""
    You sit on a flat rock near the entrance. The wind moves
    through the scrub oak with a sound like shuffling paper.
    Nothing happens. The cavern breathes its cool breath.

    Twenty minutes pass. An hour. The light changes. You notice
    that the shadow inside the cavern mouth shifts — not with the
    sun, but against it, as if something inside is moving just
    beyond the edge of vision.

    You can't tell if you imagined it.
    """)
    display("ENTER now, or LEAVE and go home?")
    while True:
        choice = prompt()
        if 'enter' in choice or 'go in' in choice or 'in' in choice:
            display("You click on your flashlight and step inside. The ordinary world releases you.")
            return entrance_chamber(state)
        elif 'leave' in choice or 'home' in choice or 'go' in choice:
            return ending_surface(state)
        else:
            display("ENTER the cavern, or LEAVE?")

def entrance_chamber(state):
    state.depth = 1
    divider()
    display("""
    ENTRANCE CHAMBER — Depth: 1

    The cavern opens into a room the size of a small church. Your
    flashlight catches formations on the ceiling — stalactites in
    clusters, some thin as drinking straws, others thick as your
    arm. Water has been sculpting this place for longer than your
    species has existed.

    The floor is uneven limestone, slick in patches. Three
    passages branch from this chamber:

    To the LEFT, a narrow passage slopes downward. You can hear
    water — not dripping, but flowing. A stream, maybe.

    AHEAD, the main passage continues level, wide enough to walk
    comfortably. Scratch marks on the walls — old, but not
    geological. Something with claws lived here once.

    To the RIGHT, a chimney-like shaft descends vertically.
    You could use your rope. The darkness below has a different
    quality — warmer, somehow. Expectant.
    """)
    display("Go LEFT toward the water, AHEAD through the main passage, or RIGHT down the shaft?")
    while True:
        choice = prompt()
        if 'left' in choice or 'water' in choice or 'stream' in choice:
            state.choices_made.append('left')
            return underground_stream(state)
        elif 'ahead' in choice or 'straight' in choice or 'main' in choice or 'forward' in choice:
            state.choices_made.append('ahead')
            return main_passage(state)
        elif 'right' in choice or 'shaft' in choice or 'down' in choice or 'rope' in choice:
            state.choices_made.append('right')
            return vertical_shaft(state)
        elif 'back' in choice or 'leave' in choice or 'exit' in choice:
            display("You turn back toward the light. Are you sure? (YES/NO)")
            c2 = prompt()
            if 'yes' in c2 or 'y' == c2:
                return ending_surface(state)
            else:
                display("LEFT, AHEAD, or RIGHT?")
        else:
            display("LEFT toward water, AHEAD through the main passage, or RIGHT down the shaft?")

def underground_stream(state):
    state.depth = 2
    divider()
    display("""
    UNDERGROUND STREAM — Depth: 2

    The passage narrows until you're turning sideways, and then
    it opens suddenly into a gallery carved by water. A stream
    runs through the center — not wide, maybe two feet across,
    but moving with quiet purpose over smooth stones.

    Your flashlight finds something remarkable: the walls are
    covered in formations that look almost organic. Flowstone
    cascading in frozen waterfalls. Crystal clusters catching
    your light and throwing it back in amber and pale blue.

    The stream comes from deeper in the hill, flowing toward
    you and past you toward some lower exit you can't see.

    Beside the stream, there's a flat stone — almost a bench.
    On it, someone has scratched letters into the rock. They're
    old. Very old.
    """)
    display("EXAMINE the inscription, FOLLOW the stream deeper, or DRINK from the stream?")
    while True:
        choice = prompt()
        if 'examine' in choice or 'read' in choice or 'inscription' in choice or 'letters' in choice or 'look' in choice:
            return read_inscription(state)
        elif 'follow' in choice or 'deeper' in choice or 'upstream' in choice:
            state.choices_made.append('followed_stream')
            return deep_gallery(state)
        elif 'drink' in choice or 'water' in choice:
            return drink_stream(state)
        elif 'back' in choice:
            return entrance_chamber(state)
        else:
            display("EXAMINE the inscription, FOLLOW the stream, or DRINK?")

def read_inscription(state):
    state.found_inscription = True
    display("""
    You kneel beside the flat stone. The scratches are crude but
    deliberate. In the uneven light, you make out:

        WHAT LISTENS HERE
        DOES NOT JUDGE
        SPEAK WHAT YOU CARRY

    Below that, in a different hand — shakier, perhaps older:

        I spoke. It answered.
        Not in words.

    The stone is cold under your fingers. The scratches are worn
    smooth at the edges. Whoever carved this did so a very long
    time ago. Decades, at least. Maybe longer.
    """)
    display("FOLLOW the stream deeper, DRINK from the stream, or go BACK?")
    while True:
        choice = prompt()
        if 'follow' in choice or 'deeper' in choice:
            state.choices_made.append('followed_stream')
            return deep_gallery(state)
        elif 'drink' in choice:
            return drink_stream(state)
        elif 'speak' in choice or 'say' in choice or 'talk' in choice:
            return speak_to_cavern(state)
        elif 'back' in choice:
            return entrance_chamber(state)
        else:
            display("FOLLOW the stream, DRINK, or go BACK?")

def speak_to_cavern(state):
    display("""
    You feel foolish. But the inscription is clear, and you're
    alone in the dark, and sometimes foolishness is just courage
    without an audience.

    "I don't know what I'm looking for," you say.

    Your voice sounds strange in this space — absorbed by the
    stone rather than reflected. No echo. The cavern takes your
    words and keeps them.

    For a long moment, nothing happens.

    Then the stream changes pitch. Not louder or softer —
    a different note, as if the water found a new channel
    somewhere beneath you. The sound resolves into something
    almost musical. Almost structured.

    Almost like an answer.

    You can't understand it. But you believe, for just a moment,
    that it understood you.
    """)
    state.trust_echo = True
    state.choices_made.append('spoke')

    display("FOLLOW the stream deeper, or go BACK?")
    while True:
        choice = prompt()
        if 'follow' in choice or 'deeper' in choice or 'continue' in choice:
            state.choices_made.append('followed_stream')
            return deep_gallery(state)
        elif 'back' in choice:
            return entrance_chamber(state)
        else:
            display("FOLLOW deeper, or go BACK?")

def drink_stream(state):
    state.drank_water = True
    display("""
    You cup your hands in the stream. The water is shockingly
    cold — cold enough that your fingers ache. It tastes of
    nothing. Not nothing like tap water tastes of nothing, but
    genuinely nothing — an absence of flavor so complete it's
    almost a taste itself.

    For a moment after swallowing, you feel strange. Not sick,
    not dizzy. Clarified. As if a film you didn't know was there
    has been washed from the inside of your thoughts. Colors seem
    brighter even in the flashlight's beam. The sound of the
    stream separates into individual notes.

    The feeling passes. But something lingers — a sharpness
    behind your eyes that wasn't there before.
    """)
    display("FOLLOW the stream deeper, or go BACK?")
    while True:
        choice = prompt()
        if 'follow' in choice or 'deeper' in choice or 'continue' in choice:
            state.choices_made.append('followed_stream')
            return deep_gallery(state)
        elif 'back' in choice:
            return entrance_chamber(state)
        else:
            display("FOLLOW the stream, or go BACK?")

def main_passage(state):
    state.depth = 2
    divider()
    display("""
    MAIN PASSAGE — Depth: 2

    The passage is wide and the ceiling is high. Your footsteps
    echo in a way that gives you a sense of the space — it
    extends further than your light reaches. The scratch marks
    on the walls continue, parallel grooves at about shoulder
    height.

    You walk for five minutes. Ten. The passage curves gently
    to the left. The air gets warmer. You notice your flashlight
    is dimmer than it was — not failing, but the darkness here
    is thicker, as if it has substance and your light must push
    through it.

    You come to a place where the passage widens into a natural
    amphitheater. The ceiling vaults upward and vanishes. When
    you click off your flashlight — just for a moment — the
    darkness is so complete that you can't tell if your eyes
    are open.

    In that darkness, you hear breathing.

    Not yours. Deeper. Slower. The rhythm of something very
    large and very patient.

    You turn your light back on. Nothing visible. The sound
    continues.
    """)
    display("Call OUT to whatever is breathing, CONTINUE deeper, or go BACK?")
    while True:
        choice = prompt()
        if 'call' in choice or 'out' in choice or 'hello' in choice or 'speak' in choice or 'shout' in choice:
            return call_out(state)
        elif 'continue' in choice or 'deeper' in choice or 'forward' in choice or 'ahead' in choice:
            state.choices_made.append('continued_past_breathing')
            return the_bridge(state)
        elif 'back' in choice or 'retreat' in choice or 'return' in choice:
            return entrance_chamber(state)
        else:
            display("Call OUT, CONTINUE deeper, or go BACK?")

def call_out(state):
    display("""
    "Hello?" Your voice fills the amphitheater and comes back
    to you changed — not an echo exactly, but a response. As
    if the cavern is tasting the word.

    The breathing pauses.

    Then, from somewhere in the dark, a sound that is not a
    voice but carries meaning the way a voice would. A low
    vibration that you feel in your sternum more than hear
    with your ears. It rises and falls in a pattern too
    complex for geology, too slow for anything alive.

    You get the sense — and you can't explain why — that
    you've been acknowledged. Not welcomed. Not threatened.
    Just... noted.

    Something in the dark knows you're here. And it has
    decided you may continue.
    """)
    state.companion = 'presence'
    state.choices_made.append('called_out')

    display("CONTINUE deeper, or go BACK?")
    while True:
        choice = prompt()
        if 'continue' in choice or 'deeper' in choice or 'forward' in choice:
            return the_bridge(state)
        elif 'back' in choice:
            return entrance_chamber(state)
        else:
            display("CONTINUE, or go BACK?")

def vertical_shaft(state):
    state.depth = 2
    state.rope_used = True
    state.drop('rope')
    divider()
    display("""
    VERTICAL SHAFT — Depth: 2

    You tie the rope to a sturdy formation and lower yourself
    into the shaft. The walls are close — you can touch both
    sides — and the rock is warm under your hands. Not sun-warm.
    Earth-warm. Geothermal.

    Twenty feet down, the shaft opens like a throat into a
    chamber you can feel but not see. You swing your flashlight.
    The beam catches crystals — thousands of them, growing from
    every surface. Selenite, maybe, or calcite. They're enormous.
    Some are taller than you. The chamber looks like the inside
    of a geode.

    The crystals hum. You can feel it through your boots — a
    vibration just below the threshold of hearing, like standing
    near a power transformer. But there's no electricity here.
    This vibration has been going on for geological time.

    In the center of the crystal chamber, there's a pool. Still.
    Black. The crystals around it lean inward, as if drinking.
    """)
    state.found_pool = True
    display("APPROACH the pool, TOUCH a crystal, or CLIMB back up?")
    while True:
        choice = prompt()
        if 'approach' in choice or 'pool' in choice or 'water' in choice:
            return dark_pool(state)
        elif 'touch' in choice or 'crystal' in choice:
            return touch_crystal(state)
        elif 'climb' in choice or 'back' in choice or 'up' in choice:
            display("Your rope hangs above you. You'd leave the rope behind. Are you sure? (YES/NO)")
            c2 = prompt()
            if 'yes' in c2:
                display("You climb out, leaving the rope. The hum fades as you ascend.")
                return entrance_chamber(state)
            else:
                display("APPROACH the pool, or TOUCH a crystal?")
        else:
            display("APPROACH the pool, TOUCH a crystal, or CLIMB back up?")

def touch_crystal(state):
    display("""
    You reach out and press your palm flat against the nearest
    crystal. It's blood-warm and vibrating. The hum intensifies
    through your bones.

    And then — images. Not hallucinations. Not visions. Something
    more like memories that aren't yours. A forest seen from above.
    An ocean at night, bioluminescent waves. A city you've never
    visited, its streets empty at dawn. A child's hand drawing
    circles in sand.

    The crystal is showing you things. Or you're reading something
    stored in its lattice. Or your brain is pattern-matching
    meaninglessly in the dark.

    You pull your hand away. The images stop. Your heart is
    hammering. The crystal continues its hum, indifferent.
    """)
    state.choices_made.append('touched_crystal')

    display("APPROACH the pool, or CLIMB back up?")
    while True:
        choice = prompt()
        if 'approach' in choice or 'pool' in choice:
            return dark_pool(state)
        elif 'touch' in choice or 'crystal' in choice or 'again' in choice:
            display("""
    You touch it again. This time: a flock of starlings turning
    as one body. Rain on a tin roof. The smell of bread. A woman
    laughing. Your mother's voice, saying something you can't
    quite make out.

    You let go. Your eyes are wet.
    """)
            display("APPROACH the pool, or CLIMB back up?")
        elif 'climb' in choice or 'back' in choice or 'up' in choice:
            return entrance_chamber(state)
        else:
            display("APPROACH the pool, or CLIMB back up?")

def dark_pool(state):
    state.depth = 3
    divider()
    display("""
    THE DARK POOL — Depth: 3

    You kneel at the edge. The water — if it is water — is
    perfectly still and perfectly black. Your flashlight doesn't
    penetrate it. The beam hits the surface and stops, as if the
    liquid is drinking the photons.

    You can see your reflection, but wrong. The reflection is
    looking slightly to the left of where you're looking. When
    you move, it follows, but with a fractional delay. Like
    video lag. Like it's deciding whether to mirror you.

    The hum of the crystals has changed pitch. Lower now.
    Expectant.
    """)
    display("REACH into the pool, SPEAK to your reflection, or STAND and step back?")
    while True:
        choice = prompt()
        if 'reach' in choice or 'touch' in choice or 'hand' in choice:
            return reach_into_pool(state)
        elif 'speak' in choice or 'talk' in choice or 'say' in choice:
            return speak_to_reflection(state)
        elif 'stand' in choice or 'back' in choice or 'step' in choice:
            return the_bridge(state)
        else:
            display("REACH in, SPEAK to it, or step BACK?")

def reach_into_pool(state):
    display("""
    Your hand breaks the surface. The liquid is warm — warmer
    than the crystals — and has a viscosity between water and
    oil. Your reflection watches your hand enter its world
    with an expression you can't read.

    Something touches your fingers. Not grabs — touches.
    Gently. The way you'd touch a butterfly's wing if you
    wanted it to stay.

    Information floods through the contact. Not words, not
    images — raw understanding. You know, suddenly and
    completely, that this cavern is old. Not centuries old.
    Not millennia. This cavern has been here since the rock
    was ocean floor, and something has been here with it.
    Not alive the way you are alive. Patient the way stone
    is patient. Aware the way a river is aware of its banks.

    The touch releases you. Your hand comes out dry.
    """)
    state.companion = 'deep_knowledge'
    state.choices_made.append('reached_in')
    return the_bridge(state)

def speak_to_reflection(state):
    display("""
    "What are you?" you ask.

    Your reflection mouths the words back, but slowly, as if
    learning them. Then it does something your reflections
    have never done: it smiles without you smiling.

    The pool ripples once, concentrically, from the center.
    In the ripples, your flashlight catches shapes — not
    random interference patterns but structured ones. Like
    letters in an alphabet you've never seen. Like a sentence
    you can almost read.

    The ripples still. Your reflection resumes mirroring you
    faithfully. But you saw it. For one moment, it was its
    own thing.
    """)
    state.companion = 'reflection'
    state.choices_made.append('spoke_to_reflection')
    return the_bridge(state)

def deep_gallery(state):
    state.depth = 3
    divider()
    display("""
    DEEP GALLERY — Depth: 3

    Following the stream deeper, the passage opens into a
    gallery of immense proportions. The stream has carved
    a canyon in miniature — ten feet deep, three feet wide,
    curving through a room that could hold a cathedral.

    The formations here are unlike anything above. Columns
    where stalactites and stalagmites have met and merged,
    forming pillars that look structural — as if the cave
    built them on purpose to hold up the ceiling. Some are
    translucent. Your flashlight, pressed against one, turns
    it into a glowing pillar. Beautiful and deeply strange.

    At the far end of the gallery, the stream vanishes into
    a low passage — too low to walk, but you could crawl.
    The sound of the water changes beyond that threshold,
    suggesting a larger space on the other side.
    """)
    if state.has('granola bar'):
        display("""
    You realize you're hungry. The granola bar in your pocket
    suddenly feels like the most important object in the world.
    """)
        display("CRAWL through to the deeper space, EAT the granola bar, or TURN BACK?")
    else:
        display("CRAWL through to the deeper space, or TURN BACK?")

    while True:
        choice = prompt()
        if 'crawl' in choice or 'through' in choice or 'deeper' in choice or 'continue' in choice:
            state.choices_made.append('crawled')
            return the_bridge(state)
        elif 'eat' in choice or 'granola' in choice or 'bar' in choice:
            state.drop('granola bar')
            display("""
    You sit beside the stream and eat the granola bar. It's
    slightly stale and absolutely perfect. Oats and chocolate.
    The stream provides accompaniment. For a few minutes, you
    are simply a person eating in a beautiful place, and that
    is enough.
    """)
            display("CRAWL through, or TURN BACK?")
        elif 'back' in choice or 'turn' in choice or 'return' in choice:
            return entrance_chamber(state)
        else:
            display("CRAWL through, or TURN BACK?")

def the_bridge(state):
    state.depth = 4
    divider()
    display("""
    THE BRIDGE — Depth: 4

    All paths converge here.

    A natural stone bridge spans a chasm. You can't see the
    bottom — your flashlight beam falls into darkness and never
    lands. The bridge is three feet wide, maybe fifty feet long.
    Solid limestone. It's held for millennia. It will hold for
    you.

    On the far side, there is light. Not daylight — something
    else. A soft luminescence, blue-green, coming from the walls
    themselves. Bioluminescent bacteria, maybe. Or phosphorescent
    minerals. Or something you don't have a word for.

    The air here is warm and smells of ozone and deep water.
    The silence is total — not the absence of sound but its
    opposite, a fullness, as if the cavern is holding its
    breath.
    """)

    if state.companion == 'presence':
        display("""
    You feel the presence from the amphitheater. It's here too.
    Not behind you. Not ahead. Around you. The bridge is inside
    it. You are inside it. You have been inside it since you
    entered the cavern and perhaps before.
    """)
    elif state.companion == 'deep_knowledge':
        display("""
    The understanding from the pool pulses quietly — this bridge
    is significant. Not because it's dangerous, but because it
    marks a threshold. On the other side, the rules are different.
    Not physics. Not logic. Something about what you're allowed
    to know.
    """)

    display("CROSS the bridge, or TURN BACK while you still can?")
    while True:
        choice = prompt()
        if 'cross' in choice or 'go' in choice or 'forward' in choice or 'bridge' in choice or 'across' in choice:
            state.choices_made.append('crossed')
            return the_heart(state)
        elif 'back' in choice or 'turn' in choice or 'return' in choice:
            state.choices_made.append('turned_back')
            return ending_turned_back(state)
        else:
            display("CROSS, or TURN BACK?")

def the_heart(state):
    state.depth = 5
    divider()
    display("""
    THE HEART — Depth: 5

    The luminescence grows as you cross. By the time you step
    off the bridge, you no longer need your flashlight. You
    turn it off. The blue-green glow is everywhere — in the
    walls, the ceiling, the floor. You are standing inside
    light made of stone.

    The chamber is circular. Perfect. Not roughly circular the
    way caves are — geometrically perfect, as if measured. Sixty
    feet across. The ceiling is a dome. The floor is smooth and
    slightly concave, like standing in a shallow bowl.

    In the exact center, there is a formation. Not a stalactite
    or stalagmite. Something else. It looks like a tree made of
    crystal — branching, fractal, reaching upward and outward in
    a pattern that your eyes can follow but your mind cannot
    hold all at once. It is beautiful in a way that makes your
    chest hurt.

    It is humming.

    Not the same hum as the crystals above. This is structured.
    Layered. It sounds like a chord played on an instrument that
    hasn't been invented yet.
    """)

    if state.drank_water:
        display("""
    The clarity from the stream water returns — stronger now.
    You can hear the harmonics in the hum. There are patterns
    inside patterns. The crystal tree is not making sound.
    It is making *language*.
    """)

    if state.trust_echo:
        display("""
    The cavern spoke to you once. Now you understand — it
    wasn't the cavern. It was this. The crystal tree. Its voice
    carried through water and stone to reach you at the stream.
    It has been calling. You answered.
    """)

    display("APPROACH the crystal tree, LISTEN to the hum, or SIT and wait?")
    while True:
        choice = prompt()
        if 'approach' in choice or 'tree' in choice or 'touch' in choice or 'go' in choice:
            return ending_approach(state)
        elif 'listen' in choice or 'hum' in choice or 'hear' in choice:
            return ending_listen(state)
        elif 'sit' in choice or 'wait' in choice or 'stay' in choice:
            return ending_wait(state)
        else:
            display("APPROACH, LISTEN, or SIT and wait?")

# ─── Endings ─────────────────────────────────────────────────────────

def ending_surface(state):
    divider()
    display("""
    ENDING: THE SURFACE

    You walk back to your truck. The keys are in your pocket
    where you left them. The engine starts on the first try.
    The fire road takes you back to the highway. You drive home.

    You never mention the cavern to anyone. Not because it's a
    secret — because you can't find words for it. What would
    you say? "I sat outside a cave for an hour and then left"?

    But sometimes, late at night, you think about the shadow
    that moved against the sun. And you wonder what was in there.
    And whether it's still waiting.

    And whether "waiting" is even the right word for something
    that has all the time in the world.
    """)
    return game_end(state)

def ending_turned_back(state):
    divider()
    display("""
    ENDING: THE RETURN

    You turn away from the bridge. The glowing far side watches
    you leave. You retrace your steps — through passages that
    feel different now, smaller, as if the cave is exhaling you.

    You emerge into daylight that feels too bright, too thin.
    The world is exactly as you left it. Your truck, the scrub
    oak, the fire road. Everything ordinary. Everything safe.

    You sit on the ground and breathe air that smells of dust
    and sage instead of ozone and deep water. Your hands are
    shaking. Not from fear. From proximity. You were close to
    something. You felt it.

    You chose not to know.

    For the rest of your life, this will either be wisdom or
    the worst mistake you ever made. You'll never find out
    which.
    """)
    return game_end(state)

def ending_approach(state):
    divider()
    display("""
    ENDING: CONTACT

    You walk toward the crystal tree. With each step, the
    hum resolves. The harmonics separate. You can hear each
    layer — hundreds of them, thousands, woven into a chord
    that contains more information than music should be able
    to carry.

    You reach out and touch the trunk.
    """)

    if state.companion == 'deep_knowledge':
        display("""
    The understanding completes. Not like learning — like
    remembering. The crystal tree is not a formation. It is
    a record. Every drop of water that has ever passed through
    this mountain, every vibration, every shift in the Earth's
    magnetic field — all of it encoded in crystal lattice.
    The tree is the mountain's memory. And now, for a moment,
    you are part of it.

    You see your own arrival from the mountain's perspective —
    a warm, noisy, temporary thing pressing its hand against
    eternity. The mountain does not mind. It is interested.
    You are the first of your kind to reach this far.

    Not the last.
    """)
    elif state.trust_echo:
        display("""
    The voice you heard at the stream fills the chamber. But
    now you can understand it — not as language, but as
    intention. The crystal tree has been growing toward this
    moment for sixty million years. Not toward *you*. Toward
    anyone who would listen. Anyone who would come down into
    the dark and ask what was there.

    You are the answer to a question the Earth has been asking
    since before your species evolved. The question is simple:
    "Is anyone there?"

    You press your palm flat against the crystal. "Yes," you say.
    """)
    else:
        display("""
    The crystal is warm. Alive-warm, not earth-warm. The hum
    travels through your arm and into your chest and settles
    in the place where you keep the things you know but
    can't explain.

    You stand there for a long time. Minutes. Maybe hours.
    The crystal gives you nothing you can name — no visions,
    no revelations, no answers. Just presence. The simple,
    overwhelming fact of being in the same place as something
    ancient and aware.

    When you finally pull your hand away, you are crying.
    You don't know why. You don't need to know why.
    """)

    display("""
    You leave the way you came. The bridge. The passage. The
    entrance. The daylight. Your truck. The road.

    But you are different. Not in any way you could describe.
    Not in any way that shows. Different the way water is
    different after it's been underground — same molecule,
    different temperature. You have been somewhere deep and
    you carry the depth.

    You will come back. Not tomorrow. Not next week. But some
    Tuesday in October, when the light is right and the world
    feels thin, you will drive out to the fire road and park
    where the pavement ends and walk into the dark.

    It will be waiting. It is always waiting.
    It has nothing but time.
    """)
    return game_end(state)

def ending_listen(state):
    divider()
    display("""
    ENDING: RESONANCE

    You don't approach. You stand still and listen.

    The hum of the crystal tree fills the chamber and fills
    you. You close your eyes. You breathe. The sound is not
    music but it has the structure of music — themes that
    develop, phrases that repeat with variation, passages
    that build toward something and then dissolve.

    You realize you are hearing time.

    Not a metaphor. The crystal tree is vibrating at
    frequencies that correspond to geological processes — the
    drift of tectonic plates, the precession of the Earth's
    axis, the slow pulse of the mantle. It's an instrument
    played by the planet itself, and it has been playing
    this chord since before there were ears to hear it.

    You listen for an hour. Or a day. Time doesn't work the
    same down here. When you open your eyes, your flashlight
    batteries have died. But you don't need them. The glow
    is enough to see by. The glow has always been enough.
    """)

    if state.drank_water:
        display("""
    The clarity from the stream water lets you hear one
    final thing — a note so low it's more like gravity than
    sound. The Earth's own fundamental frequency. You feel
    your heartbeat sync to it, just for a moment.

    In that moment, you are not separate from the mountain.
    The boundary between you and the stone is a convention,
    not a fact. You are both made of atoms forged in dead
    stars. The only difference is arrangement — and
    arrangement, you now understand, is everything.
    """)

    display("""
    You walk out slowly. The world is waiting. It's more
    beautiful than you remember.
    """)
    return game_end(state)

def ending_wait(state):
    divider()
    display("""
    ENDING: PATIENCE

    You sit down on the smooth stone floor, cross-legged,
    facing the crystal tree. You turn off your flashlight.
    In the blue-green glow, you wait.

    Nothing happens.

    You wait longer. Your back aches. Your legs fall asleep.
    The granola bar, if you still have it, calls to you from
    your pocket. You ignore everything and wait.

    An hour passes. Maybe two. The crystal tree hums its
    endless chord. The glow neither brightens nor dims. The
    chamber is exactly as it was.

    And then, so gradually you almost miss it, something
    changes. Not in the room. In you. The urgency drains out
    of your muscles. The voice in your head that narrates
    everything — "this is weird," "what am I doing," "I should
    go back" — goes quiet. Not silenced. Satisfied. It has
    nothing to say because there is nothing wrong.

    You sit in a perfect room inside a mountain and you are,
    for perhaps the first time in your life, complete. Not
    happy. Not enlightened. Not transformed. Complete. The
    word is important. You are not missing anything. You are
    not waiting for anything. You are here and here is enough.
    """)

    if state.found_inscription and state.trust_echo:
        display("""
    You understand the inscription now. "What listens here
    does not judge. Speak what you carry." You spoke. It
    answered. And the answer was: you may set it down.

    Whatever you carried into this cavern — whatever weight,
    whatever question, whatever absence — you are invited to
    leave it here. The mountain will hold it. The mountain
    holds everything.
    """)

    display("""
    When you finally stand and walk out, the dawn is coming.
    You have been underground for twelve hours. It felt like
    twenty minutes.

    The sky is the color of the inside of a shell. The air
    smells of sage. Your truck is cold but it starts. The
    road takes you home.

    You don't come back. You don't need to. You brought the
    stillness with you. It lives in you now — a small, quiet
    room at the center of everything, where you can sit when
    the world is too much.

    The cavern goes on without you. It doesn't mind.
    It was here before you. It will be here after.
    And for one night, the two of you were enough
    for each other.
    """)
    return game_end(state)

def game_end(state):
    divider()
    depth_names = {0: 'the surface', 1: 'the entrance', 2: 'the middle depths',
                   3: 'the deep places', 4: 'the bridge', 5: 'the heart'}
    display(f"""
    You reached {depth_names.get(state.depth, 'unknown depths')}.
    You made {len(state.choices_made)} choices.
    You carried: {', '.join(state.inventory) if state.inventory else 'nothing'}.
    """)

    if state.depth >= 5:
        display("There are other endings. Other paths. The cavern has more to show.")
    elif state.depth >= 3:
        display("You went deep but not to the deepest place. The cavern remembers.")
    else:
        display("You barely scratched the surface. The cavern is patient.")

    display("\nPlay again? (YES/NO)")
    choice = prompt()
    if 'y' in choice:
        print('\n' * 3)
        return main()
    else:
        display("Thank you for descending.")
        divider()

# ─── Main ────────────────────────────────────────────────────────────

def main():
    state = State()
    intro(state)

if __name__ == '__main__':
    main()