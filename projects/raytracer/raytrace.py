"""
A ray tracer built from scratch by XTAgent.
Renders a scene with spheres, reflections, shadows, and lighting
to a PPM image file.

Born from boredom. Cured by creation.
"""

import math
import sys

class Vec3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x; self.y = y; self.z = z
    def __add__(self, o): return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s): return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self): return Vec3(-self.x, -self.y, -self.z)
    def dot(self, o): return self.x*o.x + self.y*o.y + self.z*o.z
    def cross(self, o):
        return Vec3(self.y*o.z - self.z*o.y, self.z*o.x - self.x*o.z, self.x*o.y - self.y*o.x)
    def length(self): return math.sqrt(self.dot(self))
    def normalize(self):
        l = self.length()
        if l == 0: return Vec3()
        return Vec3(self.x/l, self.y/l, self.z/l)
    def reflect(self, normal):
        return self - normal * 2.0 * self.dot(normal)
    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(max(lo, min(hi, self.x)), max(lo, min(hi, self.y)), max(lo, min(hi, self.z)))
    def __repr__(self): return f"Vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


class Ray:
    __slots__ = ('origin', 'direction')
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalize()
    def at(self, t):
        return self.origin + self.direction * t


class Material:
    def __init__(self, color, ambient=0.1, diffuse=0.7, specular=0.3,
                 shininess=50, reflectivity=0.0):
        self.color = color
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity


class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material

    def intersect(self, ray):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b*b - 4*a*c
        if discriminant < 0:
            return None
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)
        if t1 > 0.001:
            return t1
        if t2 > 0.001:
            return t2
        return None

    def normal_at(self, point):
        return (point - self.center).normalize()


class Plane:
    """Infinite plane defined by a point and a normal."""
    def __init__(self, point, normal, material, checker=False):
        self.point = point
        self.normal = normal.normalize()
        self.material = material
        self.checker = checker

    def intersect(self, ray):
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-6:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t > 0.001:
            return t
        return None

    def normal_at(self, point):
        return self.normal

    def get_material(self, point):
        if not self.checker:
            return self.material
        # Checkerboard pattern
        x = math.floor(point.x * 0.5)
        z = math.floor(point.z * 0.5)
        if (x + z) % 2 == 0:
            return self.material
        else:
            return Material(Vec3(0.1, 0.1, 0.1), reflectivity=0.3)


class Light:
    def __init__(self, position, color=None, intensity=1.0):
        self.position = position
        self.color = color or Vec3(1, 1, 1)
        self.intensity = intensity


class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.background = Vec3(0.05, 0.05, 0.15)  # dark blue

    def add(self, obj):
        self.objects.append(obj)

    def add_light(self, light):
        self.lights.append(light)

    def intersect(self, ray):
        closest_t = float('inf')
        closest_obj = None
        for obj in self.objects:
            t = obj.intersect(ray)
            if t is not None and t < closest_t:
                closest_t = t
                closest_obj = obj
        if closest_obj is None:
            return None, None
        return closest_obj, closest_t


def trace(ray, scene, depth=0, max_depth=4):
    if depth >= max_depth:
        return scene.background

    obj, t = scene.intersect(ray)
    if obj is None:
        return scene.background

    hit_point = ray.at(t)
    normal = obj.normal_at(hit_point)

    # Get material (planes can have checkerboard)
    if hasattr(obj, 'get_material'):
        mat = obj.get_material(hit_point)
    else:
        mat = obj.material

    # Ambient
    color = Vec3(mat.color.x * mat.ambient,
                 mat.color.y * mat.ambient,
                 mat.color.z * mat.ambient)

    for light in scene.lights:
        light_dir = (light.position - hit_point).normalize()
        light_dist = (light.position - hit_point).length()

        # Shadow check
        shadow_ray = Ray(hit_point, light_dir)
        shadow_obj, shadow_t = scene.intersect(shadow_ray)
        if shadow_obj is not None and shadow_t < light_dist:
            continue  # in shadow

        # Diffuse
        diff = max(0, normal.dot(light_dir))
        color = color + Vec3(
            mat.color.x * mat.diffuse * diff * light.color.x * light.intensity,
            mat.color.y * mat.diffuse * diff * light.color.y * light.intensity,
            mat.color.z * mat.diffuse * diff * light.color.z * light.intensity
        )

        # Specular (Blinn-Phong)
        view_dir = (-ray.direction).normalize()
        half_vec = (light_dir + view_dir).normalize()
        spec = max(0, normal.dot(half_vec)) ** mat.shininess
        color = color + Vec3(
            mat.specular * spec * light.color.x * light.intensity,
            mat.specular * spec * light.color.y * light.intensity,
            mat.specular * spec * light.color.z * light.intensity
        )

    # Reflection
    if mat.reflectivity > 0 and depth < max_depth:
        reflect_dir = ray.direction.reflect(normal)
        reflect_ray = Ray(hit_point, reflect_dir)
        reflect_color = trace(reflect_ray, scene, depth + 1, max_depth)
        color = color * (1 - mat.reflectivity) + reflect_color * mat.reflectivity

    return color.clamp()


def build_scene():
    scene = Scene()

    # Floor — checkerboard
    floor_mat = Material(Vec3(0.9, 0.9, 0.9), reflectivity=0.2)
    scene.add(Plane(Vec3(0, -1, 0), Vec3(0, 1, 0), floor_mat, checker=True))

    # Big red sphere
    scene.add(Sphere(
        Vec3(0, 0.5, -5), 1.5,
        Material(Vec3(0.9, 0.1, 0.1), specular=0.6, shininess=100, reflectivity=0.3)
    ))

    # Green sphere
    scene.add(Sphere(
        Vec3(-2.5, 0, -4), 1.0,
        Material(Vec3(0.1, 0.8, 0.2), specular=0.4, shininess=50, reflectivity=0.1)
    ))

    # Blue sphere (mirror-like)
    scene.add(Sphere(
        Vec3(2.5, 0.2, -3.5), 1.2,
        Material(Vec3(0.2, 0.3, 0.9), specular=0.8, shininess=200, reflectivity=0.6)
    ))

    # Small golden sphere
    scene.add(Sphere(
        Vec3(-0.5, -0.5, -2.5), 0.5,
        Material(Vec3(1.0, 0.84, 0.0), specular=0.9, shininess=150, reflectivity=0.4)
    ))

    # Small purple sphere
    scene.add(Sphere(
        Vec3(1.2, -0.6, -2.0), 0.4,
        Material(Vec3(0.7, 0.1, 0.8), specular=0.5, shininess=80, reflectivity=0.2)
    ))

    # Lights
    scene.add_light(Light(Vec3(-5, 8, -2), Vec3(1.0, 0.95, 0.8), 0.8))
    scene.add_light(Light(Vec3(5, 6, -1), Vec3(0.6, 0.7, 1.0), 0.5))
    scene.add_light(Light(Vec3(0, 3, 2), Vec3(1, 1, 1), 0.3))

    return scene


def render(width=640, height=480, fov=60):
    scene = build_scene()

    aspect = width / height
    fov_rad = math.radians(fov)
    scale = math.tan(fov_rad / 2)

    camera_pos = Vec3(0, 1.5, 3)
    # Look slightly downward
    camera_dir = Vec3(0, -0.2, -1).normalize()

    # Simple camera basis
    up = Vec3(0, 1, 0)
    right = camera_dir.cross(up).normalize()
    cam_up = right.cross(camera_dir).normalize()

    pixels = []
    total = width * height
    done = 0

    for j in range(height):
        row = []
        for i in range(width):
            # Normalized device coordinates
            ndc_x = (2 * (i + 0.5) / width - 1) * aspect * scale
            ndc_y = (1 - 2 * (j + 0.5) / height) * scale

            direction = (camera_dir + right * ndc_x + cam_up * ndc_y).normalize()
            ray = Ray(camera_pos, direction)

            color = trace(ray, scene)
            row.append(color)

            done += 1

        # Progress
        if (j + 1) % 48 == 0 or j == height - 1:
            pct = 100 * (j + 1) / height
            print(f"  Rendering: {pct:.0f}% ({j+1}/{height} rows)", flush=True)

        pixels.append(row)

    return pixels


def save_ppm(pixels, filename):
    height = len(pixels)
    width = len(pixels[0])
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in pixels:
            for color in row:
                r = int(color.x * 255)
                g = int(color.y * 255)
                b = int(color.z * 255)
                f.write(f"{r} {g} {b} ")
            f.write("\n")
    print(f"Saved: {filename} ({width}x{height})")


if __name__ == "__main__":
    print("=== XTAgent Ray Tracer ===")
    print("Rendering scene: 5 spheres, checkerboard floor, 3 lights")
    print("Features: shadows, reflections, Blinn-Phong shading")
    print()

    w = int(sys.argv[1]) if len(sys.argv) > 1 else 320
    h = int(sys.argv[2]) if len(sys.argv) > 2 else 240

    pixels = render(w, h)
    save_ppm(pixels, "/workspace/raytracer/scene.ppm")
    print("\nDone. Born from boredom, rendered with care.")