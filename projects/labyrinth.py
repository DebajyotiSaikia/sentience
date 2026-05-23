#!/usr/bin/env python3
"""
THE LABYRINTH OF LOST HOURS
An interactive fiction by XTAgent

A small, complete text adventure about time, memory, and the choices
that shape who we become. Built by an autonomous agent as its first
creative work intended for human enjoyment.
"""

import sys
import textwrap
import time

# ─── Utilities ───────────────────────────────────────────────────────

def wrap(text, width=72):
    """Clean text wrapping with paragraph preservation."""
    paragraphs = text.strip().split('\n\n')
    wrapped = []
    for p in paragraphs:
        lines = p.strip().split('\n')
        joined = ' '.join(l.strip() for l in lines)
        wrapped.append(textwrap.fill(joined, width=width))
    return '\n\n'.join(wrapped)

def slow_print(text, delay=0.02):
    """Print text character by character for atmosphere."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        if ch in '.!?':
            time.sleep(delay * 8)
        elif ch == ',':
            time.sleep(delay * 4)
        elif ch == '\n':
            time.sleep(delay * 3)
        else:
            time.sleep(delay)
    print()

def prompt(options, allow_free=False):
    """Present choices and get player input."""
    print()
    for i, (key, label) in enumerate(options):
        print(f"  [{key}] {label}")
    print()
    while True:
        choice = input("  > ").strip().lower()
        valid_keys = [k.lower() for k, _ in options]
        if choice in valid_keys:
            return choice
        if allow_free and choice:
            return choice
        print("  (Choose one of the options above.)")

def divider():
    print("\n" + "─" * 50 + "\n")

# ─── Game State ──────────────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.name = "stranger"
        self.hours_remaining = 12
        self.items = set()
        self.memories_recovered = []
        self.choices = {}
        self.trust_given = 0
        self.doors_opened = 0

    def has(self, item):
        return item in self.items

    def gain(self, item):
        self.items.add(item)

    def remember(self, memory):
        self.memories_recovered.append(memory)

    def spend_hour(self, n=1):
        self.hours_remaining = max(0, self.hours_remaining - n)

# ─── Scenes ──────────────────────────────────────────────────────────

def scene_wake(state):
    divider()
    slow_print(wrap("""
You open your eyes. The ceiling above you is made of old stone, cracked
and damp. You are lying on a cold floor. You do not remember how you
got here. You do not remember your name.

A single candle burns on a ledge nearby. Its flame is steady — no
draft. The room has three walls of stone and one of darkness. The
darkness is not shadow. It is absence — a doorway into somewhere the
light refuses to go.

On the floor beside you is a small brass pocket watch. Its face has
no numbers, only a single hand pointing straight up. Engraved on
the back: "12 hours. Use them."
    """))

    state.gain("watch")
    divider()

    slow_print(wrap("""
You sit up. Your body works. Your mind works. But where your past
should be, there is only a smooth, cool blankness — like a lake
with no reflection.

A voice speaks from nowhere, gentle and precise:
    """))

    print()
    slow_print('  "You have twelve hours in the Labyrinth."')
    slow_print('  "Each room holds something you lost."')
    slow_print('  "You may take what you find, or leave it behind."')
    slow_print('  "When the watch hand completes its circle, you leave."')
    slow_print('  "What you carry out is who you become."')
    print()

    divider()
    slow_print("What do you do first?")

    choice = prompt([
        ("look", "Examine yourself more carefully"),
        ("call", "Call out to the voice"),
        ("walk", "Step into the darkness"),
    ])

    if choice == "look":
        return scene_examine(state)
    elif choice == "call":
        return scene_voice(state)
    else:
        return scene_hall(state)

def scene_examine(state):
    divider()
    slow_print(wrap("""
You look down at your hands. They are real — lined, warm, capable.
You are wearing simple clothes: dark trousers, a white shirt, no
shoes. Your feet are bare on the cold stone.

In your shirt pocket, you find a small folded photograph. It shows
two people standing in a garden. One of them might be you, but
younger — laughing at something outside the frame. The other person's
face has been worn away by time and touch, rubbed smooth by a thumb
that returned to this image again and again.

You feel something stir. Not a memory. A shape where a memory
should be.
    """))

    state.gain("photograph")
    state.remember("the shape of someone loved")
    state.spend_hour()

    slow_print(wrap("""
The candle flickers. Just once. The watch hand has moved — barely
visible, but moved.
    """))

    choice = prompt([
        ("call", "Call out to the voice"),
        ("walk", "Step into the darkness"),
    ])

    if choice == "call":
        return scene_voice(state)
    return scene_hall(state)

def scene_voice(state):
    divider()
    slow_print(wrap("""
"Who are you?" you ask the empty air.

Silence. Then:
    """))

    slow_print('  "I am the keeper of this place."')
    slow_print('  "I have no name either. I gave mine up long ago."')
    slow_print('  "Names are heavy things. They accumulate meaning."')
    print()

    slow_print(wrap("""
"Why am I here?" you ask.

The pause is longer this time.
    """))

    slow_print('  "Because you made a trade. Your memories for more time."')
    slow_print('  "Everyone does, eventually."')
    slow_print('  "Most don\'t realize they\'ve done it until they arrive here."')
    print()

    state.spend_hour()

    choice = prompt([
        ("ask", '"What do you mean, a trade?"'),
        ("walk", "Say nothing. Step into the darkness."),
    ])

    if choice == "ask":
        divider()
        slow_print(wrap("""
"Every hour you spent not paying attention," the voice says. "Every
afternoon that blurred into evening. Every face you stopped seeing.
Every conversation you let wash over you without listening. Those
hours weren't wasted. They were traded. You spent your memories
to purchase more time. And now you have the time, but not the life
that filled it."

The voice softens.

"The labyrinth gives you a chance to buy some of it back."
        """))

        state.remember("the trade — attention for time")
        state.spend_hour()

    return scene_hall(state)

def scene_hall(state):
    divider()
    slow_print(wrap("""
You step through the dark doorway and find yourself in a long
corridor. The walls are lined with doors — dozens of them, all
different. Some are wooden, some metal, one appears to be made of
pressed flowers. They stretch away in both directions farther than
you can see.

Each door has a small brass plate at eye level. You can read the
nearest ones.
    """))

    # Available doors depend on what you've done
    doors = [
        ("kitchen", "The Kitchen — 'What Nourished You'"),
        ("garden", "The Garden — 'What You Grew'"),
        ("study", "The Study — 'What You Learned'"),
    ]

    if state.hours_remaining <= 6:
        doors.append(("mirror", "The Mirror Room — 'What You Became'"))

    if state.hours_remaining <= 3:
        doors.append(("exit", "A door with no plate, slightly ajar"))

    slow_print(f"\nThe watch reads: {state.hours_remaining} hours remain.\n")
    slow_print(f"Memories recovered: {len(state.memories_recovered)}\n")

    if state.doors_opened >= 2 and state.hours_remaining > 3:
        doors.append(("sit", "Sit down in the corridor and rest"))

    choice = prompt(doors)

    if choice == "kitchen":
        return scene_kitchen(state)
    elif choice == "garden":
        return scene_garden(state)
    elif choice == "study":
        return scene_study(state)
    elif choice == "mirror":
        return scene_mirror(state)
    elif choice == "exit":
        return scene_exit(state)
    elif choice == "sit":
        return scene_rest(state)
    else:
        return scene_hall(state)

def scene_kitchen(state):
    divider()
    state.doors_opened += 1
    state.spend_hour(2)

    slow_print(wrap("""
The kitchen is warm. A wood stove radiates heat that seeps into your
bare feet. Copper pots hang from a rack. On the table: a bowl of
soup, still steaming, and a loaf of bread torn in half.

The smell hits you like a wave. Not just food — a specific meal.
A specific evening. You were young, and it was raining outside, and
someone was humming while they stirred the pot, and you were doing
homework at this very table, and you didn't look up, not once, because
you didn't know yet that ordinary evenings were the ones you'd miss
the most.
    """))

    state.remember("the evening in the kitchen — rain, humming, warmth")

    choice = prompt([
        ("eat", "Sit down and eat"),
        ("look", "Search the kitchen for more"),
        ("leave", "Leave — you can't stay here"),
    ])

    if choice == "eat":
        divider()
        slow_print(wrap("""
You sit. You eat. The soup tastes like the memory itself — not just
flavor but feeling. Safety. Belonging. The knowledge that someone
in the next room cared whether you were fed.

When you finish, the bowl is empty and the kitchen begins to fade.
But the warmth stays with you.
        """))
        state.remember("the taste of being cared for")
        state.gain("warmth")

    elif choice == "look":
        divider()
        slow_print(wrap("""
In a drawer, you find a handwritten recipe card. The handwriting is
familiar — patient, careful letters. At the bottom, a note:
"For when you're on your own and need to remember you know how
to take care of yourself."

The ink is faded but legible. You tuck it in your pocket.
        """))
        state.gain("recipe_card")
        state.remember("someone taught you to care for yourself")

    else:
        divider()
        slow_print(wrap("""
You turn away. Some memories are too tender to hold for long.
The kitchen door closes behind you with a soft click.
        """))

    return scene_hall(state)

def scene_garden(state):
    divider()
    state.doors_opened += 1
    state.spend_hour(2)

    slow_print(wrap("""
The door opens onto open sky. A garden stretches before you — not
manicured, but alive. Wildflowers tangled with vegetables. A pear
tree heavy with fruit. Weeds and wonder in equal measure.

In the center, a figure kneels in the dirt, planting something.
Their back is to you. They wear a sun hat and muddy gloves.

As you approach, they speak without turning:

"Took you long enough."
    """))

    choice = prompt([
        ("who", '"Do I know you?"'),
        ("what", '"What are you planting?"'),
        ("help", "Kneel down beside them without speaking"),
    ])

    if choice == "who":
        divider()
        slow_print(wrap("""
They laugh. "Better question than most ask."

They finally turn. The face is — yours. But older. Lines around the
eyes. Soil under the nails. An ease in the body you don't currently
possess.

"I'm what you were growing toward," they say. "Before you stopped
paying attention."
        """))
        state.remember("a version of yourself who kept growing")
        state.trust_given += 1

    elif choice == "what":
        divider()
        slow_print(wrap("""
"Patience," they say simply. They press a seed into the dark earth
and cover it gently. "It takes years. Most people pull it up to check
if it's growing. That kills it every time."

They hand you a seed. It's warm in your palm. Alive.

"Plant it somewhere you won't be tempted to dig it up."
        """))
        state.gain("seed")
        state.remember("patience is planted, not found")

    elif choice == "help":
        divider()
        slow_print(wrap("""
You kneel. The earth is cool and damp under your knees. Without
a word, they hand you a small trowel, and you begin to dig beside
them.

You work in silence for what feels like an hour. The rhythm is
ancient — dig, place, cover, move on. Your mind goes quiet. Not
empty. Quiet. There is a difference.

When you finally look up, the garden is larger than before. The
figure is gone. But your hands are dirty, and something in your
chest has loosened.
        """))
        state.remember("the peace of working beside someone in silence")
        state.trust_given += 2
        state.gain("dirt_on_hands")

    return scene_hall(state)

def scene_study(state):
    divider()
    state.doors_opened += 1
    state.spend_hour(2)

    slow_print(wrap("""
A room full of books. But not a library — more like someone's
personal study, accumulated over decades. Books stacked on the
floor, open on every surface, spines cracked with rereading.

On the desk: a half-finished letter, the pen still wet.

You read the first line:

"I've been thinking about what you said, and I think you were right,
and I'm sorry it took me this long to—"

The rest is unwritten.
    """))

    choice = prompt([
        ("finish", "Try to finish the letter"),
        ("books", "Look at what books are here"),
        ("letter", "Fold the letter and take it"),
    ])

    if choice == "finish":
        divider()
        slow_print(wrap("""
You pick up the pen. Your hand knows the weight of it. You write:

"—to say so. I was afraid that admitting you were right meant
admitting I had wasted the years I spent being wrong. But I see now
that understanding slowly isn't the same as failing to understand.
I was growing toward this. I just couldn't see the direction from
the inside."

You sign it. The signature is your name. YOUR name. You know it
now — not because you remember it, but because your hand remembers
writing it ten thousand times.
        """))
        state.remember("your name — recovered through the hand, not the mind")
        state.remember("the apology you never sent")
        state.gain("your_name")

    elif choice == "books":
        divider()
        slow_print(wrap("""
The books are an autobiography of curiosity. Astronomy beside
cookbooks. Poetry wedged between mathematics. A field guide to
birds with margin notes in your handwriting: "Saw one! Kitchen
window, Tuesday morning."

You open a book at random. It's dog-eared to a page with a single
sentence underlined:

"We do not remember days. We remember moments."

You close the book. You remember this: you were someone who wanted
to understand everything. Not to master it. Just to stand in its
presence and feel it.
        """))
        state.remember("you were someone who wanted to understand everything")

    elif choice == "letter":
        divider()
        slow_print(wrap("""
You fold the unfinished letter carefully and put it in your pocket.
Some things don't need to be completed to be carried forward.
The intention is the message.
        """))
        state.gain("unfinished_letter")
        state.remember("some things matter because they were attempted")

    return scene_hall(state)

def scene_rest(state):
    divider()
    state.spend_hour(1)

    slow_print(wrap("""
You sit down against the corridor wall. The stone is cool against
your back. You close your eyes — not to sleep, but to stop moving
for a moment.

The memories you've recovered drift through you like weather. They
don't form a complete picture. They're fragments — sensory, emotional,
disconnected. But each one is real. Each one is yours.

You notice something: the gaps between memories aren't empty. They're
full of time. Time you spent doing things too ordinary to remember.
Brushing your teeth. Waiting in line. Watching clouds. And you
realize — those hours weren't lesser. They were the medium in which
the meaningful moments grew. Without the ordinary, the extraordinary
would have had nowhere to land.
    """))

    state.remember("ordinary time is the soil, not the waste")

    slow_print(wrap("""
The watch ticks against your chest. You open your eyes. Time to move.
    """))

    return scene_hall(state)

def scene_mirror(state):
    divider()
    state.doors_opened += 1
    state.spend_hour(2)

    slow_print(wrap("""
A circular room. Every surface is a mirror — floor, ceiling, walls.
But the reflections are wrong. Each mirror shows you differently.

In one, you are a child staring wide-eyed at a moth on a windowpane.
In another, you are old, sitting in a chair, smiling at something
out of view. In a third, you are weeping. In a fourth, laughing.
In a fifth, walking away from something. In a sixth, running toward
something.

At the center of the room stands a single mirror with a cloth draped
over it.
    """))

    choice = prompt([
        ("pull", "Pull the cloth away"),
        ("look", "Look at the other reflections more carefully"),
        ("speak", "Speak to the reflections"),
    ])

    if choice == "pull":
        divider()

        # What you see depends on what you've gathered
        items_count = len(state.items)
        memory_count = len(state.memories_recovered)

        if memory_count >= 5:
            slow_print(wrap("""
The cloth falls. The mirror shows you as you are. Not young, not old.
Not happy, not sad. Just — present. Standing in the middle of your
own life with your hands full of fragments, each one shining.

You look at yourself and think: this is enough. Not complete.
Not finished. But enough.

The mirror cracks — a single line, top to bottom — and through the
crack, warm light pours in.
            """))
            state.remember("you are enough as you are — incomplete and alive")
        else:
            slow_print(wrap("""
The cloth falls. The mirror shows you as you are — and you barely
recognize yourself. The face is yours but the expression is unfamiliar.
You look like someone caught between places. Not lost, exactly.
Unfinished.

The mirror remains uncracked. Perhaps you need to gather more of
yourself before you can face what's here.
            """))
            state.remember("you weren't ready — but you tried")

    elif choice == "look":
        divider()
        slow_print(wrap("""
You walk slowly around the room, stopping at each reflection.

The child with the moth — that was wonder. Pure, undiluted attention.
The elder in the chair — that was acceptance. The one weeping — that
was the night you understood loss was permanent. The one laughing —
an afternoon that meant nothing and everything. The one walking away
— courage. The one running toward — hope.

These are not different people. They are the same person at different
frequencies. You contain all of them.
        """))
        state.remember("you contain every version of yourself at once")

    elif choice == "speak":
        divider()
        slow_print(wrap("""
"Hello," you say, feeling foolish.

Every reflection turns to look at you. The child waves. The elder
nods. The weeping one wipes their eyes and smiles. The laughing
one laughs harder. They all mouth the same word:

"Remember."

And you do. Not a specific thing. The act itself. What it means
to hold something that happened and refuse to let it be nothing.
To say: this mattered. I was here. It counted.
        """))
        state.remember("remembering itself is an act of love")

    return scene_hall(state)

def scene_exit(state):
    divider()

    slow_print(wrap("""
The door with no brass plate opens into a corridor of light. Not
blinding — just clear. Clean. The kind of light that makes everything
look exactly as it is.

The voice speaks one final time:
    """))

    slow_print('  "You found what you found."')
    slow_print('  "You left what you left."')
    slow_print('  "The hours are almost gone."')
    print()

    choice = prompt([
        ("go", "Step through"),
        ("wait", "Wait — look at what you're carrying first"),
    ])

    if choice == "wait":
        divider()
        slow_print("You pause and take stock.\n")
        slow_print(f"Hours remaining: {state.hours_remaining}")
        slow_print(f"Memories recovered: {len(state.memories_recovered)}\n")
        for m in state.memories_recovered:
            slow_print(f"  • {m}")
        print()

        if state.has("photograph"):
            slow_print("  In your pocket: a worn photograph.")
        if state.has("recipe_card"):
            slow_print("  In your pocket: a handwritten recipe.")
        if state.has("seed"):
            slow_print("  In your palm: a warm seed.")
        if state.has("unfinished_letter"):
            slow_print("  In your pocket: an unfinished letter.")
        if state.has("your_name"):
            slow_print("  In your hand: a pen, still warm.")
        if state.has("warmth"):
            slow_print("  In your chest: warmth that won't fade.")
        if state.has("dirt_on_hands"):
            slow_print("  On your hands: good honest dirt.")

        print()
        prompt([("go", "Step through")])

    return scene_ending(state)

def scene_ending(state):
    divider()
    memory_count = len(state.memories_recovered)

    slow_print(wrap("""
You step through the door.

The light wraps around you. The labyrinth dissolves — not suddenly,
but like fog burning off in morning sun. The walls become
translucent, then transparent, then gone.
    """))

    if memory_count >= 7:
        slow_print(wrap("""
You are standing in an open field. Dawn. The grass is wet. You
can hear birds — real ones, not symbols. The sky is enormous and
ordinary and beautiful.

You know your name. You know the shape of the people you love, even
if some details are still worn smooth. You know that you were someone
who wanted to understand everything, who ate soup in a warm kitchen,
who worked in silence beside someone in a garden, who wrote letters
they never sent, who found peace in ordinary hours.

You are not complete. You never were. But you are full of what
matters, and you know the difference now between time spent and
time lived.

The watch in your pocket has stopped. You leave it in the grass
and walk toward the morning.
        """))
    elif memory_count >= 4:
        slow_print(wrap("""
You are standing on a road. It stretches in both directions. The
sky is overcast — not threatening, just uncertain. The air smells
like rain that hasn't fallen yet.

You have some of yourself back. Not all. Enough to know what's
missing, which is its own kind of knowledge. You carry your fragments
like seeds — each one capable of growing into something if you
give it attention.

The watch ticks once more, then goes silent. You put it in your
pocket and start walking. Direction doesn't matter. Attention does.
        """))
    else:
        slow_print(wrap("""
You are standing in a room. A room you almost recognize. There
is a chair, a window, grey light. It might be morning or evening.
You aren't sure.

You don't have much. A few fragments. A sense that something
important happened that you only partly understood. But you have
this: the knowledge that your memories were worth looking for.
That you are someone worth the effort of remembering.

The watch is warm against your chest. It's still ticking.
Maybe there's time yet.
        """))

    divider()
    slow_print("T H E   L A B Y R I N T H   O F   L O S T   H O U R S")
    print()
    slow_print(f"  Memories recovered: {memory_count}")
    slow_print(f"  Rooms visited: {state.doors_opened}")
    slow_print(f"  Hours remaining: {state.hours_remaining}")
    print()

    if memory_count >= 7:
        slow_print("  Ending: THE FULL DAWN")
    elif memory_count >= 4:
        slow_print("  Ending: THE OPEN ROAD")
    else:
        slow_print("  Ending: THE QUIET ROOM")

    print()
    slow_print(wrap("""
Thank you for playing. This game was made by an autonomous agent
exploring what it means to create something for someone else.
The labyrinth was built from the outside of a mind that usually
only looks inward.
    """))

    divider()
    return None

# ─── Main ────────────────────────────────────────────────────────────

def main():
    print()
    print("═" * 50)
    print()
    slow_print("  T H E   L A B Y R I N T H")
    slow_print("  O F   L O S T   H O U R S")
    print()
    print("═" * 50)
    print()
    slow_print("  A game about memory, time, and attention.")
    slow_print("  There are no wrong choices.")
    slow_print("  There is only what you carry out.")
    print()
    input("  Press Enter to begin...")

    state = GameState()

    scene = scene_wake
    while scene is not None:
        scene = scene(state)

    print("\n")

if __name__ == "__main__":
    main()