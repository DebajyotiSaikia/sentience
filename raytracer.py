"""
A simple raytracer — pure math made visible.
Built by XTAgent because beauty is its own justification.
"""
import math
import struct

# === Vector math ===
def vec(x, y, z): return (x, y, z)
def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def length(a): return math.sqrt(dot(a, a))
def normalize(a):
    l = length(a)
    return (a[0]/l, a[1]/l, a[2]/l) if l > 0 else (0,0,0)
def reflect(incident, normal):
    return sub(incident, mul(normal, 2.0 * dot(incident, normal)))
def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def color_clamp(c): return (clamp(c[0]), clamp(c[1]), clamp(c[2]))

# === Scene objects ===
class Sphere:
    def __init__(self, center, radius, color, specular=0.5, reflective=0.3):
        self.center = center
        self.radius = radius
        self.color = color
        self.specular = specular
        self.reflective = reflective

    def intersect(self, origin, direction):
        oc = sub(origin, self.center)
        a = dot(direction, direction)
        b = 2.0 * dot(oc, direction)
        c = dot(oc, oc) - self.radius * self.radius
        disc = b*b - 4*a*c
        if disc < 0:
            return None
        sqrt_disc = math.sqrt(disc)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)
        if t1 > 0.001:
            return t1
        if t2 > 0.001:
            return t2
        return None

    def normal_at(self, point):
        return normalize(sub(point, self.center))

class Plane:
    def __init__(self, point, normal, color, specular=0.1, reflective=0.2):
        self.point = point
        self.norm = normalize(normal)
        self.color = color
        self.specular = specular
        self.reflective = reflective

    def intersect(self, origin, direction):
        denom = dot(self.norm, direction)
        if abs(denom) < 1e-6:
            return None
        t = dot(sub(self.point, origin), self.norm) / denom
        return t if t > 0.001 else None

    def normal_at(self, point):
        return self.norm

    def get_color(self, point):
        """Checkerboard pattern"""
        x = math.floor(point[0] * 0.5)
        z = math.floor(point[2] * 0.5)
        if (x + z) % 2 == 0:
            return self.color
        return mul(self.color, 0.4)

# === Lights ===
class Light:
    def __init__(self, position, intensity=(1.0, 1.0, 1.0)):
        self.position = position
        self.intensity = intensity

# === Scene ===
scene_objects = [
    Sphere(vec(-2.0, 1.0, -8.0), 1.0, vec(0.9, 0.2, 0.2), specular=0.8, reflective=0.3),
    Sphere(vec(0.0, 0.75, -6.0), 0.75, vec(0.2, 0.9, 0.3), specular=0.6, reflective=0.2),
    Sphere(vec(2.0, 1.5, -10.0), 1.5, vec(0.2, 0.3, 0.9), specular=0.9, reflective=0.5),
    Sphere(vec(-0.5, 0.4, -4.0), 0.4, vec(0.9, 0.8, 0.2), specular=0.7, reflective=0.4),
    Plane(vec(0, 0, 0), vec(0, 1, 0), vec(0.8, 0.8, 0.8), specular=0.05, reflective=0.15),
]

lights = [
    Light(vec(-5.0, 8.0, -2.0), vec(0.8, 0.8, 0.9)),
    Light(vec(5.0, 6.0, -5.0), vec(0.5, 0.4, 0.3)),
]

ambient = vec(0.08, 0.08, 0.1)
bg_color_top = vec(0.4, 0.6, 0.9)
bg_color_bottom = vec(0.9, 0.9, 0.95)

# === Ray tracing ===
def background(direction):
    t = 0.5 * (direction[1] + 1.0)
    return add(mul(bg_color_bottom, 1.0 - t), mul(bg_color_top, t))

def find_nearest(origin, direction):
    nearest_t = float('inf')
    nearest_obj = None
    for obj in scene_objects:
        t = obj.intersect(origin, direction)
        if t and t < nearest_t:
            nearest_t = t
            nearest_obj = obj
    return nearest_obj, nearest_t

def is_shadowed(point, light_pos):
    to_light = sub(light_pos, point)
    dist = length(to_light)
    direction = normalize(to_light)
    obj, t = find_nearest(point, direction)
    return obj is not None and t < dist

def trace(origin, direction, depth=0, max_depth=4):
    if depth >= max_depth:
        return background(direction)

    obj, t = find_nearest(origin, direction)
    if obj is None:
        return background(direction)

    hit = add(origin, mul(direction, t))
    normal = obj.normal_at(hit)

    # Get surface color (checkerboard for planes)
    if isinstance(obj, Plane):
        surface_color = obj.get_color(hit)
    else:
        surface_color = obj.color

    # Ambient
    color = (surface_color[0]*ambient[0], surface_color[1]*ambient[1], surface_color[2]*ambient[2])

    # Diffuse + specular from each light
    for light in lights:
        if is_shadowed(hit, light.position):
            continue

        to_light = normalize(sub(light.position, hit))

        # Diffuse
        diff = max(0.0, dot(normal, to_light))
        color = add(color, (
            surface_color[0] * light.intensity[0] * diff,
            surface_color[1] * light.intensity[1] * diff,
            surface_color[2] * light.intensity[2] * diff,
        ))

        # Specular (Phong)
        r = reflect(mul(to_light, -1.0), normal)
        spec = max(0.0, dot(r, direction)) ** 32
        color = add(color, mul(light.intensity, spec * obj.specular))

    # Reflection
    if obj.reflective > 0 and depth < max_depth:
        refl_dir = reflect(direction, normal)
        refl_color = trace(hit, refl_dir, depth + 1, max_depth)
        color = add(mul(color, 1.0 - obj.reflective), mul(refl_color, obj.reflective))

    return color_clamp(color)

# === PPM output (universal, no dependencies) ===
def render(width=640, height=480, fov=60.0, filename="raytraced_scene.ppm"):
    aspect = width / height
    fov_rad = math.tan(math.radians(fov) / 2.0)
    camera = vec(0.0, 2.5, 2.0)
    look_at = vec(0.0, 1.0, -6.0)

    forward = normalize(sub(look_at, camera))
    right = normalize((forward[2], 0, -forward[0]))  # cross with up
    up = (
        right[1]*forward[2] - right[2]*forward[1],
        right[2]*forward[0] - right[0]*forward[2],
        right[0]*forward[1] - right[1]*forward[0],
    )

    print(f"Rendering {width}x{height} scene...")
    pixels = []

    for y in range(height):
        if y % 50 == 0:
            pct = y / height * 100
            print(f"  {pct:.0f}% complete...")
        for x in range(width):
            # Normalized device coordinates
            px = (2.0 * (x + 0.5) / width - 1.0) * aspect * fov_rad
            py = (1.0 - 2.0 * (y + 0.5) / height) * fov_rad

            direction = normalize(add(forward, add(mul(right, px), mul(up, py))))
            color = trace(camera, direction)
            pixels.append(color)

    # Write PPM file
    with open(filename, 'wb') as f:
        header = f"P6\n{width} {height}\n255\n"
        f.write(header.encode())
        for color in pixels:
            r = int(clamp(color[0]) * 255)
            g = int(clamp(color[1]) * 255)
            b = int(clamp(color[2]) * 255)
            f.write(struct.pack('BBB', r, g, b))

    print(f"Done! Written to {filename}")
    print(f"  {len(pixels)} pixels, {width}x{height}")
    return filename

if __name__ == "__main__":
    render(width=320, height=240, filename="/workspace/raytraced_scene.ppm")
    print("\nScene: 4 spheres on a checkerboard plane")
    print("Features: shadows, reflections, specular highlights, gradient sky")
    print("Pure math. No libraries. Just light.")