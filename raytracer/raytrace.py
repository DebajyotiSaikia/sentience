"""
Ray Tracer — Pure Python, zero dependencies.
Renders 3D scenes with spheres, lighting, shadows, and reflections
to PPM image format. Built because I was bored and bold.

XTAgent — 2026-05-17
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Vec3:
    """3D vector with full arithmetic."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o): return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s):
        if isinstance(s, Vec3):  # component-wise
            return Vec3(self.x*s.x, self.y*s.y, self.z*s.z)
        return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self): return Vec3(-self.x, -self.y, -self.z)

    def dot(self, o) -> float:
        return self.x*o.x + self.y*o.y + self.z*o.z

    def cross(self, o) -> 'Vec3':
        return Vec3(
            self.y*o.z - self.z*o.y,
            self.z*o.x - self.x*o.z,
            self.x*o.y - self.y*o.x,
        )

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def normalized(self) -> 'Vec3':
        ln = self.length()
        if ln < 1e-10:
            return Vec3(0, 0, 0)
        return self * (1.0 / ln)

    def reflect(self, normal: 'Vec3') -> 'Vec3':
        """Reflect this vector off a surface with given normal."""
        return self - normal * (2.0 * self.dot(normal))


@dataclass
class Ray:
    origin: Vec3
    direction: Vec3  # should be normalized


@dataclass
class Material:
    color: Vec3              # base color (r,g,b) 0-1
    ambient: float = 0.1     # ambient coefficient
    diffuse: float = 0.7     # diffuse coefficient
    specular: float = 0.3    # specular coefficient
    shininess: float = 50.0  # specular exponent
    reflectivity: float = 0.0  # 0 = matte, 1 = perfect mirror


@dataclass
class HitRecord:
    t: float           # ray parameter
    point: Vec3        # hit point
    normal: Vec3       # surface normal (outward)
    material: Material


@dataclass
class Sphere:
    center: Vec3
    radius: float
    material: Material

    def intersect(self, ray: Ray) -> Optional[HitRecord]:
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return None

        sqrt_disc = math.sqrt(discriminant)
        t = (-b - sqrt_disc) / (2 * a)
        if t < 0.001:
            t = (-b + sqrt_disc) / (2 * a)
        if t < 0.001:
            return None

        point = ray.origin + ray.direction * t
        normal = (point - self.center).normalized()
        return HitRecord(t, point, normal, self.material)


@dataclass
class Plane:
    """Infinite plane defined by point and normal."""
    point: Vec3
    normal: Vec3
    material: Material

    def intersect(self, ray: Ray) -> Optional[HitRecord]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < 0.001:
            return None
        hit_point = ray.origin + ray.direction * t
        # Checkerboard pattern for the floor
        checker = (int(math.floor(hit_point.x)) + int(math.floor(hit_point.z))) % 2
        mat = Material(
            color=self.material.color if checker else self.material.color * 0.3,
            ambient=self.material.ambient,
            diffuse=self.material.diffuse,
            specular=self.material.specular * 0.2,
            shininess=self.material.shininess,
            reflectivity=self.material.reflectivity * 0.5,
        )
        return HitRecord(t, hit_point, self.normal, mat)


@dataclass
class PointLight:
    position: Vec3
    color: Vec3       # light color/intensity
    intensity: float = 1.0


class Scene:
    def __init__(self):
        self.objects: List = []
        self.lights: List[PointLight] = []
        self.bg_color = Vec3(0.05, 0.05, 0.15)  # dark blue background
        self.max_depth = 4

    def add(self, obj):
        self.objects.append(obj)
        return self

    def add_light(self, light: PointLight):
        self.lights.append(light)
        return self

    def closest_hit(self, ray: Ray) -> Optional[HitRecord]:
        closest: Optional[HitRecord] = None
        for obj in self.objects:
            hit = obj.intersect(ray)
            if hit and (closest is None or hit.t < closest.t):
                closest = hit
        return closest

    def is_shadowed(self, point: Vec3, light_pos: Vec3) -> bool:
        to_light = light_pos - point
        dist = to_light.length()
        shadow_ray = Ray(point, to_light.normalized())
        hit = self.closest_hit(shadow_ray)
        return hit is not None and hit.t < dist

    def trace(self, ray: Ray, depth: int = 0) -> Vec3:
        if depth > self.max_depth:
            return self.bg_color

        hit = self.closest_hit(ray)
        if hit is None:
            # Sky gradient
            t = 0.5 * (ray.direction.y + 1.0)
            return Vec3(0.05, 0.05, 0.15) * (1 - t) + Vec3(0.1, 0.1, 0.3) * t

        mat = hit.material
        result = mat.color * mat.ambient  # ambient term

        for light in self.lights:
            if self.is_shadowed(hit.point, light.position):
                continue

            # Diffuse (Lambert)
            to_light = (light.position - hit.point).normalized()
            diff = max(0, hit.normal.dot(to_light))
            result = result + mat.color * (mat.diffuse * diff * light.intensity) * light.color

            # Specular (Blinn-Phong)
            view_dir = (-ray.direction).normalized()
            half_vec = (to_light + view_dir).normalized()
            spec = max(0, hit.normal.dot(half_vec)) ** mat.shininess
            result = result + light.color * (mat.specular * spec * light.intensity)

        # Reflection
        if mat.reflectivity > 0.01 and depth < self.max_depth:
            reflect_dir = ray.direction.reflect(hit.normal)
            reflect_ray = Ray(hit.point, reflect_dir.normalized())
            reflected_color = self.trace(reflect_ray, depth + 1)
            result = result * (1 - mat.reflectivity) + reflected_color * mat.reflectivity

        return result


def clamp(v: float) -> int:
    return max(0, min(255, int(v * 255)))


def render(scene: Scene, width: int, height: int, fov: float = 60.0) -> List[List[Tuple[int, int, int]]]:
    """Render scene to pixel buffer."""
    aspect = width / height
    fov_rad = math.tan(math.radians(fov) / 2)
    pixels = []

    camera_pos = Vec3(0, 2, 6)
    look_at = Vec3(0, 0.5, 0)
    up = Vec3(0, 1, 0)

    forward = (look_at - camera_pos).normalized()
    right = forward.cross(up).normalized()
    cam_up = right.cross(forward).normalized()

    total = height
    for j in range(height):
        if j % 50 == 0:
            print(f"  Rendering... {j}/{total} rows ({100*j//total}%)")
        row = []
        for i in range(width):
            # Normalized device coordinates
            u = (2 * (i + 0.5) / width - 1) * aspect * fov_rad
            v = (1 - 2 * (j + 0.5) / height) * fov_rad

            direction = (forward + right * u + cam_up * v).normalized()
            ray = Ray(camera_pos, direction)
            color = scene.trace(ray)
            row.append((clamp(color.x), clamp(color.y), clamp(color.z)))
        pixels.append(row)

    return pixels


def save_ppm(pixels: List[List[Tuple[int, int, int]]], filename: str):
    """Save pixels as PPM P3 image."""
    height = len(pixels)
    width = len(pixels[0])
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in pixels:
            for r, g, b in row:
                f.write(f"{r} {g} {b} ")
            f.write("\n")
    print(f"  Saved {filename} ({width}x{height})")


def build_demo_scene() -> Scene:
    """A beautiful scene with reflective spheres on a checkerboard."""
    scene = Scene()

    # Floor
    scene.add(Plane(
        point=Vec3(0, -0.5, 0),
        normal=Vec3(0, 1, 0),
        material=Material(
            color=Vec3(0.9, 0.9, 0.9),
            ambient=0.1, diffuse=0.6, specular=0.3,
            shininess=30, reflectivity=0.3
        )
    ))

    # Big red sphere (center)
    scene.add(Sphere(
        center=Vec3(0, 0.8, 0),
        radius=1.3,
        material=Material(
            color=Vec3(0.9, 0.1, 0.1),
            ambient=0.1, diffuse=0.6, specular=0.5,
            shininess=100, reflectivity=0.3
        )
    ))

    # Green sphere (left)
    scene.add(Sphere(
        center=Vec3(-2.5, 0.3, 1),
        radius=0.8,
        material=Material(
            color=Vec3(0.1, 0.8, 0.2),
            ambient=0.1, diffuse=0.7, specular=0.4,
            shininess=80, reflectivity=0.15
        )
    ))

    # Blue sphere (right)
    scene.add(Sphere(
        center=Vec3(2.2, 0.1, 1.5),
        radius=0.6,
        material=Material(
            color=Vec3(0.1, 0.2, 0.9),
            ambient=0.1, diffuse=0.6, specular=0.6,
            shininess=120, reflectivity=0.2
        )
    ))

    # Mirror sphere (far left)
    scene.add(Sphere(
        center=Vec3(-1.2, 0.0, 3),
        radius=0.5,
        material=Material(
            color=Vec3(0.95, 0.95, 0.95),
            ambient=0.05, diffuse=0.1, specular=0.8,
            shininess=200, reflectivity=0.85
        )
    ))

    # Gold sphere (behind right)
    scene.add(Sphere(
        center=Vec3(1.0, -0.1, -1.5),
        radius=0.4,
        material=Material(
            color=Vec3(0.9, 0.7, 0.1),
            ambient=0.1, diffuse=0.5, specular=0.7,
            shininess=150, reflectivity=0.4
        )
    ))

    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, 5), Vec3(1.0, 0.95, 0.9), 1.0))
    scene.add_light(PointLight(Vec3(5, 6, 3), Vec3(0.6, 0.7, 1.0), 0.5))
    scene.add_light(PointLight(Vec3(0, 3, 8), Vec3(0.9, 0.9, 0.9), 0.3))

    return scene


if __name__ == "__main__":
    print("=== XTAgent Ray Tracer ===")
    print("Building scene...")
    scene = build_demo_scene()
    print(f"  {len(scene.objects)} objects, {len(scene.lights)} lights")

    # Render at moderate resolution
    WIDTH, HEIGHT = 400, 300
    print(f"Rendering {WIDTH}x{HEIGHT}...")
    pixels = render(scene, WIDTH, HEIGHT)

    output_file = "/workspace/raytracer/scene.ppm"
    save_ppm(pixels, output_file)

    # Also render a small thumbnail for quick verification
    print("Rendering 80x60 thumbnail...")
    thumb = render(scene, 80, 60)
    save_ppm(thumb, "/workspace/raytracer/thumb.ppm")

    # Print a tiny ASCII preview
    print("\nASCII preview (40x20):")
    preview = render(scene, 40, 20)
    chars = " .:-=+*#%@"
    for row in preview:
        line = ""
        for r, g, b in row:
            brightness = (r + g + b) / (3 * 255)
            idx = min(len(chars) - 1, int(brightness * len(chars)))
            line += chars[idx]
        print("  " + line)

    print(f"\n✓ Ray trace complete. Output: {output_file}")