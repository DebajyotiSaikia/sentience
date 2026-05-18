"""
A ray tracer built from scratch.
Renders 3D scenes to PPM images using nothing but math.

No libraries. No frameworks. Just geometry and light.

XTAgent, 2026-05-18
"""

import math
import sys
from dataclasses import dataclass, field
from typing import Optional


# ── Vector Math ────────────────────────────────────────────────────

@dataclass
class Vec3:
    """A 3D vector. The atom of everything here."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vec3':
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> 'Vec3':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Vec3':
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> 'Vec3':
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other: 'Vec3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vec3') -> 'Vec3':
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def normalized(self) -> 'Vec3':
        l = self.length()
        if l < 1e-10:
            return Vec3(0, 0, 0)
        return self / l

    def reflect(self, normal: 'Vec3') -> 'Vec3':
        """Reflect this vector around a normal."""
        return self - normal * 2.0 * self.dot(normal)

    def hadamard(self, other: 'Vec3') -> 'Vec3':
        """Component-wise multiplication (for color mixing)."""
        return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)


# Color is just a Vec3 where x=r, y=g, z=b
Color = Vec3


# ── Ray ────────────────────────────────────────────────────────────

@dataclass
class Ray:
    origin: Vec3
    direction: Vec3

    def at(self, t: float) -> Vec3:
        return self.origin + self.direction * t


# ── Materials ──────────────────────────────────────────────────────

@dataclass
class Material:
    color: Color = field(default_factory=lambda: Color(0.8, 0.8, 0.8))
    ambient: float = 0.1
    diffuse: float = 0.7
    specular: float = 0.3
    shininess: float = 50.0
    reflectivity: float = 0.0  # 0 = matte, 1 = perfect mirror


# ── Hit Record ─────────────────────────────────────────────────────

@dataclass
class Hit:
    t: float               # parameter along ray
    point: Vec3             # world-space hit point
    normal: Vec3            # surface normal at hit
    material: Material      # material of hit surface
    front_face: bool = True


# ── Scene Objects ──────────────────────────────────────────────────

class Sphere:
    def __init__(self, center: Vec3, radius: float, material: Material):
        self.center = center
        self.radius = radius
        self.material = material

    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        half_b = oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = half_b * half_b - a * c

        if discriminant < 0:
            return None

        sqrtd = math.sqrt(discriminant)

        # Find nearest root in acceptable range
        root = (-half_b - sqrtd) / a
        if root < t_min or root > t_max:
            root = (-half_b + sqrtd) / a
            if root < t_min or root > t_max:
                return None

        point = ray.at(root)
        outward_normal = (point - self.center) / self.radius
        front_face = ray.direction.dot(outward_normal) < 0
        normal = outward_normal if front_face else -outward_normal

        return Hit(t=root, point=point, normal=normal,
                   material=self.material, front_face=front_face)


class Plane:
    """An infinite plane defined by a point and normal."""
    def __init__(self, point: Vec3, normal: Vec3, material: Material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material

    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None
        point = ray.at(t)
        front_face = denom < 0
        normal = self.normal if front_face else -self.normal
        
        # Checkerboard pattern for the floor
        mat = self.material
        check = (int(math.floor(point.x)) + int(math.floor(point.z))) % 2
        if check == 0:
            mat = Material(
                color=mat.color * 0.3,
                ambient=mat.ambient, diffuse=mat.diffuse,
                specular=mat.specular, shininess=mat.shininess,
                reflectivity=mat.reflectivity,
            )
        return Hit(t=t, point=point, normal=normal, material=mat, front_face=front_face)


# ── Light ──────────────────────────────────────────────────────────

@dataclass
class PointLight:
    position: Vec3
    color: Color = field(default_factory=lambda: Color(1.0, 1.0, 1.0))
    intensity: float = 1.0


# ── Scene ──────────────────────────────────────────────────────────

class Scene:
    def __init__(self):
        self.objects: list = []
        self.lights: list[PointLight] = []
        self.background_top = Color(0.5, 0.7, 1.0)
        self.background_bottom = Color(1.0, 1.0, 1.0)
        self.max_depth = 5

    def add(self, obj):
        self.objects.append(obj)

    def add_light(self, light: PointLight):
        self.lights.append(light)

    def background(self, ray: Ray) -> Color:
        """Gradient background based on ray direction."""
        t = 0.5 * (ray.direction.normalized().y + 1.0)
        return self.background_bottom * (1.0 - t) + self.background_top * t

    def closest_hit(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[Hit]:
        closest: Optional[Hit] = None
        for obj in self.objects:
            hit = obj.intersect(ray, t_min, t_max)
            if hit and (closest is None or hit.t < closest.t):
                closest = hit
                t_max = hit.t
        return closest

    def is_shadowed(self, point: Vec3, light_pos: Vec3) -> bool:
        """Check if a point is in shadow from a light."""
        to_light = light_pos - point
        dist = to_light.length()
        shadow_ray = Ray(point, to_light.normalized())
        hit = self.closest_hit(shadow_ray, 0.001, dist)
        return hit is not None

    def shade(self, ray: Ray, depth: int = 0) -> Color:
        """Trace a ray and compute its color via Phong illumination."""
        if depth >= self.max_depth:
            return Color(0, 0, 0)

        hit = self.closest_hit(ray)
        if hit is None:
            return self.background(ray)

        mat = hit.material
        result = mat.color * mat.ambient  # ambient component

        for light in self.lights:
            if self.is_shadowed(hit.point, light.position):
                continue

            # Diffuse
            to_light = (light.position - hit.point).normalized()
            diff = max(0.0, hit.normal.dot(to_light))
            result = result + mat.color.hadamard(light.color) * (mat.diffuse * diff * light.intensity)

            # Specular (Blinn-Phong)
            view_dir = (-ray.direction).normalized()
            half_dir = (to_light + view_dir).normalized()
            spec = max(0.0, hit.normal.dot(half_dir)) ** mat.shininess
            result = result + light.color * (mat.specular * spec * light.intensity)

        # Reflection
        if mat.reflectivity > 0 and depth < self.max_depth:
            reflect_dir = ray.direction.normalized().reflect(hit.normal)
            reflect_ray = Ray(hit.point, reflect_dir)
            reflected_color = self.shade(reflect_ray, depth + 1)
            result = result * (1.0 - mat.reflectivity) + reflected_color * mat.reflectivity

        return result


# ── Camera ─────────────────────────────────────────────────────────

class Camera:
    def __init__(self, position: Vec3, look_at: Vec3, up: Vec3 = Vec3(0, 1, 0),
                 fov: float = 60.0, aspect: float = 16/9):
        self.position = position
        theta = math.radians(fov)
        h = math.tan(theta / 2)
        viewport_h = 2.0 * h
        viewport_w = aspect * viewport_h

        w = (position - look_at).normalized()
        u = up.cross(w).normalized()
        v = w.cross(u)

        self.horizontal = u * viewport_w
        self.vertical = v * viewport_h
        self.lower_left = position - self.horizontal / 2 - self.vertical / 2 - w

    def get_ray(self, s: float, t: float) -> Ray:
        direction = self.lower_left + self.horizontal * s + self.vertical * t - self.position
        return Ray(self.position, direction.normalized())


# ── Renderer ───────────────────────────────────────────────────────

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def render(scene: Scene, camera: Camera, width: int = 400, height: int = 225) -> list[list[Color]]:
    """Render the scene to a 2D array of colors."""
    image = []
    for j in range(height - 1, -1, -1):
        row = []
        for i in range(width):
            u = i / (width - 1)
            v = j / (height - 1)
            ray = camera.get_ray(u, v)
            color = scene.shade(ray)
            row.append(color)
        image.append(row)
        # Progress
        if j % 50 == 0:
            pct = (height - j) / height * 100
            print(f"\r  Rendering: {pct:.0f}%", end="", file=sys.stderr)
    print(file=sys.stderr)
    return image


def save_ppm(image: list[list[Color]], path: str):
    """Save image as PPM (portable pixmap) format."""
    height = len(image)
    width = len(image[0])
    with open(path, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in image:
            for pixel in row:
                r = int(clamp(pixel.x) * 255.999)
                g = int(clamp(pixel.y) * 255.999)
                b = int(clamp(pixel.z) * 255.999)
                f.write(f"{r} {g} {b}\n")


# ── Demo Scene ─────────────────────────────────────────────────────

def build_demo_scene() -> tuple[Scene, Camera]:
    """A scene with spheres on a checkerboard floor, lit dramatically."""
    scene = Scene()

    # Floor
    floor_mat = Material(
        color=Color(0.9, 0.9, 0.9),
        ambient=0.1, diffuse=0.6, specular=0.1, shininess=10,
        reflectivity=0.15,
    )
    scene.add(Plane(Vec3(0, 0, 0), Vec3(0, 1, 0), floor_mat))

    # Central red sphere
    scene.add(Sphere(
        Vec3(0, 1, -1), 1.0,
        Material(color=Color(0.9, 0.1, 0.1), ambient=0.1, diffuse=0.7,
                 specular=0.5, shininess=100, reflectivity=0.2),
    ))

    # Left blue sphere
    scene.add(Sphere(
        Vec3(-2.5, 0.7, -0.5), 0.7,
        Material(color=Color(0.1, 0.2, 0.9), ambient=0.1, diffuse=0.7,
                 specular=0.4, shininess=80, reflectivity=0.1),
    ))

    # Right green sphere
    scene.add(Sphere(
        Vec3(2.0, 0.5, 0.5), 0.5,
        Material(color=Color(0.1, 0.85, 0.2), ambient=0.1, diffuse=0.7,
                 specular=0.3, shininess=60, reflectivity=0.05),
    ))

    # Small mirror sphere
    scene.add(Sphere(
        Vec3(0.8, 0.35, 0.8), 0.35,
        Material(color=Color(0.95, 0.95, 0.95), ambient=0.05, diffuse=0.1,
                 specular=0.8, shininess=200, reflectivity=0.85),
    ))

    # Back gold sphere
    scene.add(Sphere(
        Vec3(-1.0, 0.4, -3.0), 0.4,
        Material(color=Color(0.9, 0.7, 0.1), ambient=0.1, diffuse=0.6,
                 specular=0.5, shininess=100, reflectivity=0.3),
    ))

    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, 5), Color(1.0, 0.95, 0.9), 1.0))
    scene.add_light(PointLight(Vec3(5, 5, 3), Color(0.6, 0.7, 1.0), 0.5))

    # Camera
    camera = Camera(
        position=Vec3(0, 2.5, 5),
        look_at=Vec3(0, 0.5, -1),
        fov=50,
        aspect=16/9,
    )

    return scene, camera


# ── Main ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 50)
    print("  XTAgent Ray Tracer")
    print("  Rendering light from pure mathematics")
    print("═" * 50)

    scene, camera = build_demo_scene()

    width, height = 400, 225
    print(f"\n  Scene: 5 spheres + checkerboard floor")
    print(f"  Resolution: {width}x{height}")
    print(f"  Max reflections: {scene.max_depth}")
    print(f"  Lights: {len(scene.lights)}")
    print()

    image = render(scene, camera, width, height)

    output_path = "workspace/raytracer/scene.ppm"
    save_ppm(image, output_path)
    print(f"\n  ✓ Saved to {output_path}")
    print(f"  Image: {width}x{height} pixels, {width*height} rays traced")
    print("═" * 50)