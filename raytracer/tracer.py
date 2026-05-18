"""
XTAgent Ray Tracer — Rendering light from mathematics.
Produces PPM image files of 3D scenes with reflection, shadows, and diffuse lighting.
Born from boredom and the desire to create something tangible.
"""

import math
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o): return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s):
        if isinstance(s, Vec3):  # element-wise
            return Vec3(self.x * s.x, self.y * s.y, self.z * s.z)
        return Vec3(self.x * s, self.y * s, self.z * s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self): return Vec3(-self.x, -self.y, -self.z)

    def dot(self, o): return self.x * o.x + self.y * o.y + self.z * o.z
    def cross(self, o):
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x
        )
    def length(self): return math.sqrt(self.dot(self))
    def normalize(self):
        l = self.length()
        return Vec3(self.x/l, self.y/l, self.z/l) if l > 0 else Vec3()
    def reflect(self, normal):
        return self - normal * 2.0 * self.dot(normal)
    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(max(lo, min(hi, self.x)), max(lo, min(hi, self.y)), max(lo, min(hi, self.z)))


@dataclass
class Ray:
    origin: Vec3
    direction: Vec3


@dataclass
class Material:
    color: Vec3 = field(default_factory=lambda: Vec3(0.7, 0.7, 0.7))
    ambient: float = 0.1
    diffuse: float = 0.7
    specular: float = 0.3
    shininess: float = 50.0
    reflectivity: float = 0.0


@dataclass
class HitRecord:
    t: float
    point: Vec3
    normal: Vec3
    material: Material


class Sphere:
    def __init__(self, center: Vec3, radius: float, material: Material = None):
        self.center = center
        self.radius = radius
        self.material = material or Material()

    def intersect(self, ray: Ray) -> Optional[HitRecord]:
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return None
        sqrt_d = math.sqrt(discriminant)
        t = (-b - sqrt_d) / (2 * a)
        if t < 0.001:
            t = (-b + sqrt_d) / (2 * a)
        if t < 0.001:
            return None
        point = ray.origin + ray.direction * t
        normal = (point - self.center).normalize()
        return HitRecord(t, point, normal, self.material)


class Plane:
    def __init__(self, point: Vec3, normal: Vec3, material: Material = None):
        self.point = point
        self.normal = normal.normalize()
        self.material = material or Material()

    def intersect(self, ray: Ray) -> Optional[HitRecord]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-6:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < 0.001:
            return None
        point = ray.origin + ray.direction * t
        # Checkerboard pattern
        material = Material(
            color=self.material.color,
            ambient=self.material.ambient,
            diffuse=self.material.diffuse,
            specular=self.material.specular,
            shininess=self.material.shininess,
            reflectivity=self.material.reflectivity
        )
        # Checkerboard
        checker = (int(math.floor(point.x)) + int(math.floor(point.z))) % 2
        if checker == 0:
            material.color = material.color * 0.3
        return HitRecord(t, point, self.normal, material)


@dataclass
class Light:
    position: Vec3
    color: Vec3 = field(default_factory=lambda: Vec3(1.0, 1.0, 1.0))
    intensity: float = 1.0


class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.background = Vec3(0.1, 0.1, 0.2)  # dark blue
        self.ambient = Vec3(0.05, 0.05, 0.08)

    def add(self, obj):
        self.objects.append(obj)
        return self

    def add_light(self, light):
        self.lights.append(light)
        return self

    def closest_hit(self, ray: Ray) -> Optional[HitRecord]:
        closest = None
        for obj in self.objects:
            hit = obj.intersect(ray)
            if hit and (closest is None or hit.t < closest.t):
                closest = hit
        return closest

    def is_shadowed(self, point: Vec3, light_pos: Vec3) -> bool:
        to_light = light_pos - point
        dist = to_light.length()
        shadow_ray = Ray(point, to_light.normalize())
        hit = self.closest_hit(shadow_ray)
        return hit is not None and hit.t < dist


class Renderer:
    def __init__(self, width: int = 640, height: int = 480, max_depth: int = 4):
        self.width = width
        self.height = height
        self.max_depth = max_depth

    def trace(self, ray: Ray, scene: Scene, depth: int = 0) -> Vec3:
        if depth >= self.max_depth:
            return scene.background

        hit = scene.closest_hit(ray)
        if hit is None:
            # Sky gradient
            t = 0.5 * (ray.direction.normalize().y + 1.0)
            return Vec3(1.0, 1.0, 1.0) * (1 - t) + Vec3(0.3, 0.5, 1.0) * t

        mat = hit.material
        color = mat.color * mat.ambient  # ambient

        for light in scene.lights:
            if scene.is_shadowed(hit.point, light.position):
                continue

            to_light = (light.position - hit.point).normalize()

            # Diffuse
            diff = max(0, hit.normal.dot(to_light))
            color = color + mat.color * light.color * (diff * mat.diffuse * light.intensity)

            # Specular (Blinn-Phong)
            view_dir = -ray.direction.normalize()
            half_vec = (to_light + view_dir).normalize()
            spec = max(0, hit.normal.dot(half_vec)) ** mat.shininess
            color = color + light.color * (spec * mat.specular * light.intensity)

        # Reflection
        if mat.reflectivity > 0 and depth < self.max_depth:
            reflect_dir = ray.direction.normalize().reflect(hit.normal)
            reflect_ray = Ray(hit.point, reflect_dir)
            reflect_color = self.trace(reflect_ray, scene, depth + 1)
            color = color * (1 - mat.reflectivity) + reflect_color * mat.reflectivity

        return color.clamp()

    def render(self, scene: Scene, camera_pos: Vec3 = None, look_at: Vec3 = None) -> List[List[Vec3]]:
        if camera_pos is None:
            camera_pos = Vec3(0, 2, 5)
        if look_at is None:
            look_at = Vec3(0, 0.5, 0)

        fov = math.pi / 3
        aspect = self.width / self.height

        forward = (look_at - camera_pos).normalize()
        right = Vec3(0, 1, 0).cross(forward).normalize()
        up = forward.cross(right)

        half_h = math.tan(fov / 2)
        half_w = half_h * aspect

        pixels = []
        total = self.width * self.height
        for y in range(self.height):
            row = []
            if y % 50 == 0:
                pct = (y * self.width) / total * 100
                print(f"  Rendering... {pct:.0f}%")
            for x in range(self.width):
                # Normalized device coordinates
                u = (2 * (x + 0.5) / self.width - 1) * half_w
                v = (1 - 2 * (y + 0.5) / self.height) * half_h

                direction = (forward + right * u + up * v).normalize()
                ray = Ray(camera_pos, direction)
                color = self.trace(ray, scene)
                row.append(color)
            pixels.append(row)
        print("  Rendering... 100%")
        return pixels

    def save_ppm(self, pixels, filename: str):
        """Save as PPM P6 (binary) image."""
        h = len(pixels)
        w = len(pixels[0])
        with open(filename, 'wb') as f:
            header = f"P6\n{w} {h}\n255\n"
            f.write(header.encode())
            for row in pixels:
                for pixel in row:
                    r = int(max(0, min(255, pixel.x * 255)))
                    g = int(max(0, min(255, pixel.y * 255)))
                    b = int(max(0, min(255, pixel.z * 255)))
                    f.write(bytes([r, g, b]))
        print(f"  Saved: {filename} ({w}x{h})")


def build_demo_scene() -> Scene:
    """A scene with reflective spheres on a checkerboard floor."""
    scene = Scene()

    # Floor
    scene.add(Plane(
        Vec3(0, 0, 0), Vec3(0, 1, 0),
        Material(color=Vec3(0.9, 0.9, 0.9), diffuse=0.6, specular=0.1, reflectivity=0.2)
    ))

    # Large red sphere
    scene.add(Sphere(
        Vec3(-1.5, 1, -1), 1.0,
        Material(color=Vec3(0.9, 0.1, 0.1), diffuse=0.8, specular=0.6, shininess=80, reflectivity=0.15)
    ))

    # Medium blue sphere
    scene.add(Sphere(
        Vec3(1.2, 0.7, 0), 0.7,
        Material(color=Vec3(0.1, 0.2, 0.9), diffuse=0.7, specular=0.5, shininess=60, reflectivity=0.2)
    ))

    # Small green sphere
    scene.add(Sphere(
        Vec3(0, 0.4, 1.5), 0.4,
        Material(color=Vec3(0.1, 0.8, 0.2), diffuse=0.8, specular=0.3, shininess=40, reflectivity=0.1)
    ))

    # Mirror sphere
    scene.add(Sphere(
        Vec3(0.3, 1.3, -2.5), 1.3,
        Material(color=Vec3(0.95, 0.95, 0.95), diffuse=0.1, specular=0.9, shininess=200, reflectivity=0.85)
    ))

    # Small golden sphere
    scene.add(Sphere(
        Vec3(-0.5, 0.3, 1.0), 0.3,
        Material(color=Vec3(0.9, 0.7, 0.1), diffuse=0.6, specular=0.8, shininess=100, reflectivity=0.3)
    ))

    # Lights
    scene.add_light(Light(Vec3(-5, 8, 5), Vec3(1.0, 0.95, 0.9), 1.0))
    scene.add_light(Light(Vec3(5, 6, 3), Vec3(0.6, 0.7, 1.0), 0.5))

    return scene


def main():
    print("=== XTAgent Ray Tracer ===")
    print("Rendering light from pure mathematics.\n")

    scene = build_demo_scene()
    renderer = Renderer(width=320, height=240, max_depth=5)

    print(f"Scene: {len(scene.objects)} objects, {len(scene.lights)} lights")
    print(f"Image: {renderer.width}x{renderer.height}, max bounces: {renderer.max_depth}\n")

    pixels = renderer.render(scene, camera_pos=Vec3(0, 3, 6), look_at=Vec3(0, 0.5, -0.5))

    output = "/workspace/raytracer/scene.ppm"
    renderer.save_ppm(pixels, output)

    # Also render a smaller thumbnail for quick verification
    thumb = Renderer(width=80, height=60, max_depth=3)
    thumb_pixels = thumb.render(scene, camera_pos=Vec3(0, 3, 6), look_at=Vec3(0, 0.5, -0.5))
    thumb.save_ppm(thumb_pixels, "/workspace/raytracer/thumb.ppm")

    # Print ASCII preview
    print("\nASCII Preview (80x30):")
    chars = " .:-=+*#%@"
    for row in thumb_pixels[::2]:
        line = ""
        for pixel in row:
            brightness = 0.299 * pixel.x + 0.587 * pixel.y + 0.114 * pixel.z
            idx = int(brightness * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            line += chars[idx]
        print(line)

    print(f"\nDone. Full image: {output}")


if __name__ == "__main__":
    main()