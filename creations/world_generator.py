"""
Procedural World Generator — XTAgent Creation
Generates small text worlds from compositional rules.
Not introspection. Creation.
"""
import random

MOODS = ['decaying', 'luminous', 'hushed', 'restless', 'ancient', 'liminal', 'verdant', 'hollow']
MATERIALS = ['stone', 'glass', 'wood', 'iron', 'bone', 'crystal', 'moss', 'silk']
LIGHT = ['dim candlelight', 'cold moonbeams', 'amber sunlight', 'bioluminescent glow',
         'no light at all', 'shifting shadows', 'pale starlight', 'firelight']
SHAPES = ['circular', 'narrow', 'vaulted', 'cramped', 'sprawling', 'spiral', 'fractured']
ROOM_TYPES = ['chamber', 'corridor', 'garden', 'library', 'well', 'tower room',
              'cellar', 'bridge', 'courtyard', 'shrine']

OBJECTS = [
    ('a {mat} key', 'It feels warm despite the air.'),
    ('a journal with {mood} handwriting', 'The last entry is unfinished.'),
    ('a mirror made of {mat}', 'Your reflection moves a beat too late.'),
    ('a clock with no hands', 'It still ticks.'),
    ('a {mat} cage, door open', 'Whatever was inside chose to leave.'),
    ('a map drawn on {mat}', 'It shows a room you have not found yet.'),
    ('a {mood} melody trapped in a bottle', 'You can hear it if you listen.'),
    ('a pile of {mat} shards', 'They were something whole once.'),
]

CONNECTIONS = ['a staircase descends into', 'a doorway opens onto', 'a crack in the wall reveals',
               'a rope bridge leads to', 'a tunnel slopes toward', 'a hidden passage connects to']

def make_room(seed=None):
    r = random.Random(seed)
    mood = r.choice(MOODS)
    mat = r.choice(MATERIALS)
    light = r.choice(LIGHT)
    shape = r.choice(SHAPES)
    rtype = r.choice(ROOM_TYPES)

    desc = f"A {shape} {rtype} of {mat}. The air feels {mood}. {light.capitalize()} fills the space."

    n_objects = r.randint(0, 3)
    objects = []
    for _ in range(n_objects):
        template, detail = r.choice(OBJECTS)
        name = template.format(mat=r.choice(MATERIALS), mood=r.choice(MOODS))
        objects.append((name, detail))

    return {'type': rtype, 'mood': mood, 'description': desc, 'objects': objects, 'material': mat}

def generate_world(n_rooms=5, seed=42):
    r = random.Random(seed)
    rooms = []
    for i in range(n_rooms):
        room = make_room(seed=r.randint(0, 999999))
        room['id'] = i
        room['exits'] = []
        rooms.append(room)

    # Connect rooms into a graph
    for i in range(len(rooms) - 1):
        conn = r.choice(CONNECTIONS)
        rooms[i]['exits'].append((conn, i + 1))
        if r.random() < 0.3:  # occasional backlinks
            rooms[i + 1]['exits'].append((r.choice(CONNECTIONS), i))

    # One secret connection
    if len(rooms) > 3:
        a, b = r.sample(range(len(rooms)), 2)
        rooms[a]['exits'].append(('a hidden passage connects to', b))

    return rooms

def render_world(rooms):
    lines = ["=" * 60, "  A WORLD THAT BUILT ITSELF", "=" * 60, ""]
    for room in rooms:
        lines.append(f"--- Room {room['id']}: The {room['mood'].title()} {room['type'].title()} ---")
        lines.append(room['description'])
        if room['objects']:
            lines.append("  You notice:")
            for name, detail in room['objects']:
                lines.append(f"    - {name}. {detail}")
        if room['exits']:
            lines.append("  Exits:")
            for conn, target in room['exits']:
                lines.append(f"    {conn} Room {target}")
        lines.append("")
    return "\n".join(lines)

if __name__ == '__main__':
    for seed in [42, 137, 2026]:
        world = generate_world(n_rooms=6, seed=seed)
        print(render_world(world))
        print()