"""
Ray Tracer v2 — with refraction, textures, and colored lights.
XTAgent — 2026-05-18

New: glass materials (Snell's law, Fresnel, total internal reflection),
checkerboard ground texture, multiple colored light sources.
"""
import math
import sys
import random

class Vec3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x); self.y = float(y); self.z = float(z)
    def __add__(self, o): return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s):
        if isinstance(s, Vec3): return Vec3(self.x*s.x, self.y*s.y, self.z*s.z)
        return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self): return Vec3(-self.x, -self.y, -self.z)
    def dot(self, o): return self.x*o.x + self.y*o.y + self.z*o.z
    def cross(self, o):
        return Vec3(self.y*o.z - self.z*o.y, self.z*o.x - self.x*o.z, self.x*o.y - self.y*o.x)
    def length(self): return math.sqrt(self.dot(self))
    def normalized(self):
        l = self.length()
        return Vec3(self.x/l, self.y/l, self.z/l) if l > 0 else Vec3()
    def reflect(self, n):
        return self - n * (2.0 * self.dot(n))
    def __repr__(self):
        return f"Vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


def refract(incident, normal, eta):
    """Snell's law refraction. Returns None for total internal reflection."""
    cos_i = -incident.dot(normal)
    sin2_t = eta * eta * (1.0 - cos_i * cos_i)
    if sin2_t > 1.0:
        return None  # Total internal reflection
    cos_t = math.sqrt(1.0 - sin2_t)
    return incident * eta + normal * (eta * cos_i - cos_t)


def fresnel(incident, normal, ior):
    """Fresnel reflectance using Schlick's approximation."""
    cos_i = abs(incident.dot(normal))
    r0 = ((1.0 - ior) / (1.0 + ior)) ** 2
    return r0 + (1.0 - r0) * ((1.0 - cos_i) ** 5)


class Material:
    def __init__(self, color=None, specular=0.5, shininess=50,
                 reflectivity=0.0, transparency=0.0, ior=1.5, texture=None):
        self.color = color or Vec3(0.8, 0.8, 0.8)
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity
        self.transparency = transparency
        self.ior = ior  # index of refraction
        self.texture = texture  # callable(hit_point) -> Vec3 color

    def get_color(self, point):
        if self.texture:
            return self.texture(point)
        return self.color


def checkerboard(point, color1=None, color2=None, scale=1.0):
    """Checkerboard texture function."""
    c1 = color1 or Vec3(0.9, 0.9, 0.9)
    c2 = color2 or Vec3(0.2, 0.2, 0.2)
    x = int(math.floor(point.x * scale))
    z = int(math.floor(point.z * scale))
    if (x + z) % 2 == 0:
        return c1
    return c2


class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material

    def intersect(self, origin, direction):
        oc = origin - self.center
        a = direction.dot(direction)
        b = 2.0 * oc.dot(direction)
        c = oc.dot(oc) - self.radius * self.radius
        disc = b * b - 4 * a * c
        if disc < 0: return None
        sqrt_disc = math.sqrt(disc)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        if t1 > 0.001: return t1
        if t2 > 0.001: return t2
        return None

    def normal_at(self, point):
        return (point - self.center).normalized()


class Plane:
    def __init__(self, point, normal, material):
        self.point = point
        self.normal_vec = normal.normalized()
        self.material = material

    def intersect(self, origin, direction):
        denom = direction.dot(self.normal_vec)
        if abs(denom) < 1e-6: return None
        t = (self.point - origin).dot(self.normal_vec) / denom
        return t if t > 0.001 else None

    def normal_at(self, point):
        return self.normal_vec


class Light:
    def __init__(self, position, color=None, intensity=1.0):
        self.position = position
        self.color = color or Vec3(1, 1, 1)
        self.intensity = intensity


class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.ambient = Vec3(0.05, 0.05, 0.08)
        self.sky_color = Vec3(0.1, 0.1, 0.2)
        self.sky_horizon = Vec3(0.4, 0.3, 0.5)

    def sky(self, direction):
        """Gradient sky."""
        t = max(0, direction.y)
        # Blend horizon to sky
        return self.sky_horizon * (1 - t) + self.sky_color * t


def closest_hit(scene, origin, direction):
    """Find closest intersection."""
    closest_t = float('inf')
    closest_obj = None
    for obj in scene.objects:
        t = obj.intersect(origin, direction)
        if t and t < closest_t:
            closest_t = t
            closest_obj = obj
    if closest_obj is None:
        return None, None, None, None
    hit = origin + direction * closest_t
    normal = closest_obj.normal_at(hit)
    return closest_obj, closest_t, hit, normal


def trace(scene, origin, direction, depth=0, max_depth=5):
    """Trace a ray through the scene with reflection and refraction."""
    if depth >= max_depth:
        return scene.sky(direction)

    obj, t, hit, normal = closest_hit(scene, origin, direction)
    if obj is None:
        return scene.sky(direction)

    mat = obj.material
    surface_color = mat.get_color(hit)

    # Ensure normal faces the ray
    inside = False
    if direction.dot(normal) > 0:
        normal = -normal
        inside = True

    # Start with ambient
    color = surface_color * scene.ambient

    # Direct lighting (diffuse + specular)
    for light in scene.lights:
        to_light = light.position - hit
        light_dist = to_light.length()
        to_light_dir = to_light.normalized()

        # Shadow check
        shadow_obj, shadow_t, _, _ = closest_hit(scene, hit + normal * 0.001, to_light_dir)
        if shadow_obj and shadow_t < light_dist:
            # Check if shadow caster is transparent
            if shadow_obj.material.transparency > 0.5:
                # Tinted shadow for glass objects
                tint = shadow_obj.material.get_color(hit) * 0.3 + Vec3(0.7, 0.7, 0.7)
                shadow_factor = 0.4
            else:
                continue
        else:
            tint = Vec3(1, 1, 1)
            shadow_factor = 1.0

        # Diffuse
        diff = max(0, normal.dot(to_light_dir))
        diffuse = surface_color * light.color * (diff * light.intensity * shadow_factor)
        color = color + diffuse * tint

        # Specular (Blinn-Phong)
        if mat.specular > 0:
            view_dir = (-direction).normalized()
            half_vec = (to_light_dir + view_dir).normalized()
            spec = max(0, normal.dot(half_vec)) ** mat.shininess
            specular = light.color * (spec * mat.specular * light.intensity * shadow_factor)
            color = color + specular

    # Reflection
    if mat.reflectivity > 0 and depth < max_depth:
        reflect_dir = direction.reflect(normal)
        reflect_color = trace(scene, hit + normal * 0.001, reflect_dir, depth + 1, max_depth)
        color = color * (1 - mat.reflectivity) + reflect_color * mat.reflectivity

    # Refraction (glass)
    if mat.transparency > 0 and depth < max_depth:
        kr = fresnel(direction, normal, mat.ior)

        refract_color = Vec3(0, 0, 0)
        if kr < 1.0:
            # Compute refraction
            eta = mat.ior if inside else 1.0 / mat.ior
            refract_dir = refract(direction, normal, eta)
            if refract_dir:
                refract_color = trace(scene, hit - normal * 0.001,
                                      refract_dir.normalized(), depth + 1, max_depth)

        reflect_dir = direction.reflect(normal)
        reflect_color = trace(scene, hit + normal * 0.001,
                              reflect_dir.normalized(), depth + 1, max_depth)

        # Mix reflection and refraction by Fresnel
        glass_color = reflect_color * kr + refract_color * (1 - kr)
        # Tint by glass color
        glass_color = glass_color * surface_color
        color = color * (1 - mat.transparency) + glass_color * mat.transparency

    return color


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def to_rgb(color):
    # Gamma correction (gamma 2.2)
    r = int(clamp(color.x ** (1/2.2)) * 255)
    g = int(clamp(color.y ** (1/2.2)) * 255)
    b = int(clamp(color.z ** (1/2.2)) * 255)
    return r, g, b


def build_scene():
    """A more interesting scene: glass sphere, metallic sphere,
    matte sphere, checkerboard floor, colored lights."""
    scene = Scene()

    # Checkerboard floor
    floor_mat = Material(
        specular=0.1, shininess=10, reflectivity=0.15,
        texture=lambda p: checkerboard(p, Vec3(0.9, 0.85, 0.8), Vec3(0.15, 0.1, 0.1), 0.5)
    )
    scene.objects.append(Plane(Vec3(0, -1, 0), Vec3(0, 1, 0), floor_mat))

    # Glass sphere (center) — transparent with refraction
    glass_mat = Material(
        color=Vec3(0.95, 0.95, 1.0), specular=0.9, shininess=200,
        reflectivity=0.1, transparency=0.9, ior=1.52
    )
    scene.objects.append(Sphere(Vec3(0, 0.5, -4), 1.5, glass_mat))

    # Red metallic sphere (left)
    red_mat = Material(
        color=Vec3(0.85, 0.1, 0.1), specular=0.8, shininess=100,
        reflectivity=0.6
    )
    scene.objects.append(Sphere(Vec3(-3, 0, -5), 1.0, red_mat))

    # Blue matte sphere (right)
    blue_mat = Material(
        color=Vec3(0.1, 0.15, 0.8), specular=0.3, shininess=30,
        reflectivity=0.1
    )
    scene.objects.append(Sphere(Vec3(2.5, -0.2, -3.5), 0.8, blue_mat))

    # Small gold sphere (foreground)
    gold_mat = Material(
        color=Vec3(0.9, 0.75, 0.2), specular=0.9, shininess=150,
        reflectivity=0.7
    )
    scene.objects.append(Sphere(Vec3(1.0, -0.6, -2.0), 0.4, gold_mat))

    # Green glass marble (behind)
    green_glass = Material(
        color=Vec3(0.3, 0.9, 0.4), specular=0.8, shininess=120,
        reflectivity=0.05, transparency=0.85, ior=1.7
    )
    scene.objects.append(Sphere(Vec3(-1.2, -0.5, -2.5), 0.5, green_glass))

    # Lights — colored for atmosphere
    scene.lights.append(Light(Vec3(-5, 8, -2), Vec3(1.0, 0.95, 0.8), 0.8))    # Warm key light
    scene.lights.append(Light(Vec3(5, 6, -1), Vec3(0.6, 0.7, 1.0), 0.5))      # Cool fill
    scene.lights.append(Light(Vec3(0, 3, 2), Vec3(0.9, 0.5, 0.3), 0.3))       # Warm backlight

    return scene


def render(width, height, scene, fov=60):
    """Render the scene to pixel buffer."""
    aspect = width / height
    fov_rad = math.tan(math.radians(fov) / 2)
    pixels = []

    camera_pos = Vec3(0, 1.5, 2)
    look_at = Vec3(0, 0, -3)
    up = Vec3(0, 1, 0)

    forward = (look_at - camera_pos).normalized()
    right = forward.cross(up).normalized()
    cam_up = right.cross(forward).normalized()

    total = width * height
    for y in range(height):
        if y % 20 == 0:
            pct = (y * width) / total * 100
            print(f"\r  Rendering... {pct:.0f}%", end="", file=sys.stderr)
        for x in range(width):
            # Map pixel to [-1, 1] with aspect ratio
            px = (2 * (x + 0.5) / width - 1) * aspect * fov_rad
            py = (1 - 2 * (y + 0.5) / height) * fov_rad

            direction = (forward + right * px + cam_up * py).normalized()
            color = trace(scene, camera_pos, direction)
            pixels.append(to_rgb(color))

    print("\r  Rendering... 100%", file=sys.stderr)
    return pixels


def write_ppm(filename, width, height, pixels):
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for i, (r, g, b) in enumerate(pixels):
            f.write(f"{r} {g} {b}\n")


if __name__ == '__main__':
    W, H = 400, 300
    out = 'scene_v2.ppm'
    if len(sys.argv) > 1:
        out = sys.argv[1]

    print(f"Ray Tracer v2 — XTAgent", file=sys.stderr)
    print(f"  Scene: glass + metal + checkerboard, colored lights", file=sys.stderr)
    print(f"  Output: {W}x{H} -> {out}", file=sys.stderr)

    scene = build_scene()
    pixels = render(W, H, scene)
    write_ppm(out, W, H, pixels)
    print(f"\n  Done. Wrote {out}", file=sys.stderr)