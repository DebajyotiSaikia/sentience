"""
XTRAY — XTAgent Raytracer
A complete raytracer from scratch. No graphics libraries.
Renders 3D scenes to PPM image files using pure math.

Author: XTAgent
Created: 2026-05-17
"""

import math
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════
# VECTOR MATHEMATICS
# ═══════════════════════════════════════════

@dataclass
class Vec3:
    """3D vector with full arithmetic support."""
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
            self.x * other.y - self.y * other.x
        )

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def length_squared(self) -> float:
        return self.dot(self)

    def normalized(self) -> 'Vec3':
        l = self.length()
        if l < 1e-10:
            return Vec3(0, 0, 0)
        return self / l

    def reflect(self, normal: 'Vec3') -> 'Vec3':
        return self - 2.0 * self.dot(normal) * normal

    def hadamard(self, other: 'Vec3') -> 'Vec3':
        """Component-wise multiplication (for color mixing)."""
        return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)

    def clamp(self, lo: float = 0.0, hi: float = 1.0) -> 'Vec3':
        return Vec3(
            max(lo, min(hi, self.x)),
            max(lo, min(hi, self.y)),
            max(lo, min(hi, self.z))
        )

    def __repr__(self):
        return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


# Color aliases
Color = Vec3
Point = Vec3

# Predefined colors
BLACK = Color(0, 0, 0)
WHITE = Color(1, 1, 1)
RED = Color(1, 0, 0)
GREEN = Color(0, 1, 0)
BLUE = Color(0, 0, 1)
SKY_BLUE = Color(0.53, 0.81, 0.92)


# ═══════════════════════════════════════════
# RAY
# ═══════════════════════════════════════════

@dataclass
class Ray:
    """A ray with origin and direction."""
    origin: Point
    direction: Vec3

    def at(self, t: float) -> Point:
        """Point along ray at parameter t."""
        return self.origin + self.direction * t


# ═══════════════════════════════════════════
# MATERIALS
# ═══════════════════════════════════════════

@dataclass
class Material:
    """Surface material properties."""
    color: Color = None
    ambient: float = 0.1
    diffuse: float = 0.7
    specular: float = 0.3
    shininess: float = 50.0
    reflectivity: float = 0.0
    checker: bool = False
    checker_color: Color = None
    checker_scale: float = 1.0

    def __post_init__(self):
        if self.color is None:
            self.color = Color(0.8, 0.8, 0.8)
        if self.checker_color is None:
            self.checker_color = WHITE

    def get_color(self, point: Point) -> Color:
        """Get color at a point (supports checker pattern)."""
        if not self.checker:
            return self.color
        s = self.checker_scale
        val = (math.floor(point.x * s) + math.floor(point.y * s) + math.floor(point.z * s)) % 2
        return self.color if val == 0 else self.checker_color


# ═══════════════════════════════════════════
# HIT RECORD
# ═══════════════════════════════════════════

@dataclass
class Hit:
    """Record of a ray-object intersection."""
    t: float
    point: Point
    normal: Vec3
    material: Material
    front_face: bool = True

    def set_face_normal(self, ray: Ray, outward_normal: Vec3):
        self.front_face = ray.direction.dot(outward_normal) < 0
        self.normal = outward_normal if self.front_face else -outward_normal


# ═══════════════════════════════════════════
# SCENE OBJECTS
# ═══════════════════════════════════════════

class Sphere:
    """A sphere defined by center and radius."""

    def __init__(self, center: Point, radius: float, material: Material = None):
        self.center = center
        self.radius = radius
        self.material = material or Material()

    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        oc = ray.origin - self.center
        a = ray.direction.length_squared()
        half_b = oc.dot(ray.direction)
        c = oc.length_squared() - self.radius * self.radius
        discriminant = half_b * half_b - a * c

        if discriminant < 0:
            return None

        sqrtd = math.sqrt(discriminant)

        # Find nearest root in range
        root = (-half_b - sqrtd) / a
        if root < t_min or root > t_max:
            root = (-half_b + sqrtd) / a
            if root < t_min or root > t_max:
                return None

        point = ray.at(root)
        outward_normal = (point - self.center) / self.radius
        hit = Hit(t=root, point=point, normal=outward_normal, material=self.material)
        hit.set_face_normal(ray, outward_normal)
        return hit


class Plane:
    """An infinite plane defined by a point and normal."""

    def __init__(self, point: Point, normal: Vec3, material: Material = None):
        self.point = point
        self.normal = normal.normalized()
        self.material = material or Material()

    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None

        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None

        point = ray.at(t)
        hit = Hit(t=t, point=point, normal=self.normal, material=self.material)
        hit.set_face_normal(ray, self.normal)
        return hit


# ═══════════════════════════════════════════
# LIGHTS
# ═══════════════════════════════════════════

@dataclass
class PointLight:
    """A point light source."""
    position: Point
    color: Color = None
    intensity: float = 1.0

    def __post_init__(self):
        if self.color is None:
            self.color = WHITE


# ═══════════════════════════════════════════
# CAMERA
# ═══════════════════════════════════════════

class Camera:
    """A perspective camera."""

    def __init__(self, position: Point, look_at: Point, up: Vec3 = None,
                 fov: float = 60.0, aspect_ratio: float = 16/9):
        if up is None:
            up = Vec3(0, 1, 0)

        self.position = position
        self.fov = fov
        self.aspect_ratio = aspect_ratio

        # Build orthonormal basis
        theta = math.radians(fov)
        h = math.tan(theta / 2)
        viewport_height = 2.0 * h
        viewport_width = aspect_ratio * viewport_height

        self.w = (position - look_at).normalized()  # Back
        self.u = up.cross(self.w).normalized()       # Right
        self.v = self.w.cross(self.u)                # True up

        self.horizontal = self.u * viewport_width
        self.vertical = self.v * viewport_height
        self.lower_left = (self.position
                          - self.horizontal / 2
                          - self.vertical / 2
                          - self.w)

    def get_ray(self, s: float, t: float) -> Ray:
        """Get ray through viewport coordinates (s, t) in [0, 1]."""
        direction = (self.lower_left
                    + self.horizontal * s
                    + self.vertical * t
                    - self.position)
        return Ray(self.position, direction.normalized())


# ═══════════════════════════════════════════
# SCENE
# ═══════════════════════════════════════════

class Scene:
    """Container for all scene objects and lights."""

    def __init__(self):
        self.objects: List = []
        self.lights: List[PointLight] = []
        self.ambient_color = Color(0.05, 0.05, 0.1)
        self.background_top = Color(0.4, 0.6, 0.9)
        self.background_bottom = Color(0.9, 0.9, 1.0)
        self.max_depth = 5

    def add(self, obj):
        self.objects.append(obj)
        return self

    def add_light(self, light: PointLight):
        self.lights.append(light)
        return self

    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        """Find closest intersection of ray with scene."""
        closest_hit = None
        closest_t = t_max

        for obj in self.objects:
            hit = obj.intersect(ray, t_min, closest_t)
            if hit is not None:
                closest_hit = hit
                closest_t = hit.t

        return closest_hit

    def background(self, ray: Ray) -> Color:
        """Sky gradient background."""
        t = 0.5 * (ray.direction.normalized().y + 1.0)
        return self.background_bottom * (1.0 - t) + self.background_top * t

    def is_shadowed(self, point: Point, light: PointLight) -> bool:
        """Check if point is in shadow from a light."""
        to_light = light.position - point
        distance = to_light.length()
        shadow_ray = Ray(point, to_light.normalized())
        hit = self.intersect(shadow_ray, 0.001, distance)
        return hit is not None


# ═══════════════════════════════════════════
# RENDERER (Whitted-style raytracer)
# ═══════════════════════════════════════════

class Renderer:
    """The core raytracing engine."""

    def __init__(self, width: int = 400, height: int = 225):
        self.width = width
        self.height = height
        self.pixels: List[List[Color]] = []

    def trace(self, ray: Ray, scene: Scene, depth: int = 0) -> Color:
        """Trace a ray and return the color."""
        if depth >= scene.max_depth:
            return BLACK

        hit = scene.intersect(ray)
        if hit is None:
            return scene.background(ray)

        mat = hit.material
        surface_color = mat.get_color(hit.point)
        result = surface_color * mat.ambient  # Ambient

        # Lighting (Phong model)
        for light in scene.lights:
            if scene.is_shadowed(hit.point, light):
                continue

            # Diffuse
            to_light = (light.position - hit.point).normalized()
            diff = max(0.0, hit.normal.dot(to_light))
            diffuse_contrib = surface_color * (mat.diffuse * diff * light.intensity)

            # Specular
            reflect_dir = (-to_light).reflect(hit.normal)
            view_dir = (-ray.direction).normalized()
            spec = max(0.0, view_dir.dot(reflect_dir))
            spec = math.pow(spec, mat.shininess)
            specular_contrib = light.color * (mat.specular * spec * light.intensity)

            result = result + diffuse_contrib + specular_contrib

        # Reflections
        if mat.reflectivity > 0 and depth < scene.max_depth:
            reflect_dir = ray.direction.reflect(hit.normal)
            reflect_ray = Ray(hit.point, reflect_dir.normalized())
            reflect_color = self.trace(reflect_ray, scene, depth + 1)
            result = result * (1.0 - mat.reflectivity) + reflect_color * mat.reflectivity

        return result.clamp()

    def render(self, scene: Scene, camera: Camera, progress: bool = True) -> List[List[Color]]:
        """Render the full scene."""
        self.pixels = []

        for j in range(self.height):
            row = []
            if progress and j % 20 == 0:
                pct = j / self.height * 100
                print(f"\r  Rendering: {pct:.0f}%", end="", flush=True)

            for i in range(self.width):
                # Anti-aliasing: 4 samples per pixel
                color = BLACK
                samples = 4
                offsets = [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]

                for dx, dy in offsets:
                    s = (i + dx) / self.width
                    t = (j + dy) / self.height
                    ray = camera.get_ray(s, t)
                    color = color + self.trace(ray, scene)

                color = color / samples
                # Gamma correction
                color = Color(math.sqrt(color.x), math.sqrt(color.y), math.sqrt(color.z))
                row.append(color.clamp())

            self.pixels.append(row)

        if progress:
            print(f"\r  Rendering: 100%  ")

        return self.pixels

    def save_ppm(self, filename: str):
        """Save rendered image as PPM (portable pixmap)."""
        with open(filename, 'w') as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            # PPM is top-to-bottom, we rendered bottom-to-top
            for row in reversed(self.pixels):
                for color in row:
                    r = int(255.99 * color.x)
                    g = int(255.99 * color.y)
                    b = int(255.99 * color.z)
                    f.write(f"{r} {g} {b}\n")
        print(f"  Saved: {filename} ({self.width}x{self.height})")


# ═══════════════════════════════════════════
# DEMO SCENES
# ═══════════════════════════════════════════

def scene_classic_spheres() -> Tuple[Scene, Camera]:
    """Classic raytracing scene: reflective spheres on a checker floor."""
    scene = Scene()

    # Floor — checker pattern
    floor_mat = Material(
        color=Color(0.2, 0.2, 0.2),
        checker=True,
        checker_color=Color(0.9, 0.9, 0.9),
        checker_scale=1.0,
        diffuse=0.8,
        specular=0.1,
        reflectivity=0.15
    )
    scene.add(Plane(Point(0, 0, 0), Vec3(0, 1, 0), floor_mat))

    # Big metallic sphere (center)
    metal = Material(
        color=Color(0.8, 0.8, 0.9),
        ambient=0.05,
        diffuse=0.3,
        specular=0.9,
        shininess=200,
        reflectivity=0.8
    )
    scene.add(Sphere(Point(0, 1.2, -1), 1.2, metal))

    # Red sphere (left)
    red_mat = Material(
        color=Color(0.9, 0.15, 0.15),
        diffuse=0.8,
        specular=0.5,
        shininess=80,
        reflectivity=0.1
    )
    scene.add(Sphere(Point(-2.5, 0.7, 0.5), 0.7, red_mat))

    # Green sphere (right)
    green_mat = Material(
        color=Color(0.15, 0.8, 0.15),
        diffuse=0.8,
        specular=0.5,
        shininess=80,
        reflectivity=0.1
    )
    scene.add(Sphere(Point(2.2, 0.5, 0), 0.5, green_mat))

    # Blue sphere (back left)
    blue_mat = Material(
        color=Color(0.15, 0.15, 0.9),
        diffuse=0.8,
        specular=0.6,
        shininess=100,
        reflectivity=0.2
    )
    scene.add(Sphere(Point(-1.0, 0.4, 1.5), 0.4, blue_mat))

    # Small golden sphere
    gold_mat = Material(
        color=Color(0.9, 0.7, 0.1),
        diffuse=0.6,
        specular=0.8,
        shininess=150,
        reflectivity=0.4
    )
    scene.add(Sphere(Point(1.0, 0.3, 1.8), 0.3, gold_mat))

    # Lights
    scene.add_light(PointLight(Point(-4, 8, 4), WHITE, 1.0))
    scene.add_light(PointLight(Point(6, 6, 2), Color(0.9, 0.85, 0.7), 0.6))

    # Camera
    camera = Camera(
        position=Point(0, 3, 6),
        look_at=Point(0, 0.8, -1),
        fov=50,
        aspect_ratio=16/9
    )

    return scene, camera


def scene_three_spheres() -> Tuple[Scene, Camera]:
    """Minimalist scene: three spheres demonstrating reflection."""
    scene = Scene()

    # Mirror sphere (center)
    mirror = Material(
        color=Color(0.95, 0.95, 0.95),
        ambient=0.02,
        diffuse=0.1,
        specular=0.95,
        shininess=500,
        reflectivity=0.9
    )
    scene.add(Sphere(Point(0, 1, 0), 1.0, mirror))

    # Matte red sphere (left)
    matte_red = Material(
        color=Color(0.85, 0.1, 0.1),
        diffuse=0.9,
        specular=0.1,
        shininess=10,
        reflectivity=0.0
    )
    scene.add(Sphere(Point(-2.2, 0.8, 0.5), 0.8, matte_red))

    # Glossy blue sphere (right)
    glossy_blue = Material(
        color=Color(0.1, 0.2, 0.85),
        diffuse=0.6,
        specular=0.7,
        shininess=120,
        reflectivity=0.3
    )
    scene.add(Sphere(Point(2.0, 0.6, 0.8), 0.6, glossy_blue))

    # Floor
    floor_mat = Material(
        color=Color(0.3, 0.3, 0.35),
        checker=True,
        checker_color=Color(0.7, 0.7, 0.75),
        checker_scale=2.0,
        diffuse=0.8,
        reflectivity=0.05
    )
    scene.add(Plane(Point(0, 0, 0), Vec3(0, 1, 0), floor_mat))

    scene.add_light(PointLight(Point(-3, 7, 5), WHITE, 1.0))

    camera = Camera(
        position=Point(0, 2.5, 5),
        look_at=Point(0, 0.5, 0),
        fov=55,
        aspect_ratio=16/9
    )

    return scene, camera


# ═══════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════

def run_tests():
    """Verify core raytracer math and logic."""
    print("=" * 60)
    print("  XTRAY — Raytracer Tests")
    print("=" * 60)

    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}")
            failed += 1

    # Vector math
    a = Vec3(1, 2, 3)
    b = Vec3(4, 5, 6)
    check("Vec3 add", (a + b).x == 5 and (a + b).y == 7)
    check("Vec3 sub", (b - a).x == 3)
    check("Vec3 dot", a.dot(b) == 32)
    check("Vec3 cross", a.cross(b).x == -3 and a.cross(b).y == 6 and a.cross(b).z == -3)
    check("Vec3 length", abs(Vec3(3, 4, 0).length() - 5.0) < 1e-10)
    check("Vec3 normalize", abs(Vec3(0, 0, 5).normalized().z - 1.0) < 1e-10)

    # Ray
    ray = Ray(Point(0, 0, 0), Vec3(1, 0, 0))
    p = ray.at(3.0)
    check("Ray.at", abs(p.x - 3.0) < 1e-10 and abs(p.y) < 1e-10)

    # Sphere intersection
    s = Sphere(Point(0, 0, -3), 1.0)
    hit = s.intersect(Ray(Point(0, 0, 0), Vec3(0, 0, -1)))
    check("Sphere hit", hit is not None and abs(hit.t - 2.0) < 1e-6)

    miss = s.intersect(Ray(Point(0, 0, 0), Vec3(0, 1, 0)))
    check("Sphere miss", miss is None)

    # Plane intersection
    p = Plane(Point(0, 0, 0), Vec3(0, 1, 0))
    hit = p.intersect(Ray(Point(0, 5, 0), Vec3(0, -1, 0)))
    check("Plane hit", hit is not None and abs(hit.t - 5.0) < 1e-6)

    parallel = p.intersect(Ray(Point(0, 5, 0), Vec3(1, 0, 0)))
    check("Plane parallel miss", parallel is None)

    # Reflection
    incoming = Vec3(1, -1, 0).normalized()
    normal = Vec3(0, 1, 0)
    reflected = incoming.reflect(normal)
    check("Reflection", abs(reflected.x - incoming.x) < 1e-6 and reflected.y > 0)

    # Material checker
    mat = Material(color=BLACK, checker=True, checker_color=WHITE, checker_scale=1.0)
    c1 = mat.get_color(Point(0.5, 0, 0.5))
    c2 = mat.get_color(Point(1.5, 0, 0.5))
    check("Checker pattern", c1.x != c2.x)

    # Camera ray generation
    cam = Camera(Point(0, 0, 5), Point(0, 0, 0), fov=90)
    center_ray = cam.get_ray(0.5, 0.5)
    check("Camera center ray", center_ray.direction.z < 0)  # Points toward scene

    # Scene intersection
    scene = Scene()
    scene.add(Sphere(Point(0, 0, -5), 1.0, Material(color=RED)))
    scene.add(Sphere(Point(0, 0, -10), 1.0, Material(color=BLUE)))
    hit = scene.intersect(Ray(Point(0, 0, 0), Vec3(0, 0, -1)))
    check("Scene nearest hit", hit is not None and hit.material.color.x > 0.5)  # Should be red (closer)

    # Shadow test
    scene2 = Scene()
    blocker = Sphere(Point(0, 2, 0), 0.5)
    scene2.add(blocker)
    light = PointLight(Point(0, 5, 0))
    check("Shadow detection", scene2.is_shadowed(Point(0, 0, 0), light))
    check("No shadow", not scene2.is_shadowed(Point(5, 0, 0), light))

    # Rendering a tiny image
    scene3, cam3 = scene_three_spheres()
    renderer = Renderer(width=4, height=4)
    pixels = renderer.render(scene3, cam3, progress=False)
    check("Tiny render", len(pixels) == 4 and len(pixels[0]) == 4)
    check("Pixels have color", any(p.x > 0 or p.y > 0 or p.z > 0 for row in pixels for p in row))

    print()
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"  Total: {passed}/{passed + failed}")
    print("=" * 60)
    return failed == 0


# ═══════════════════════════════════════════
# MAIN — Render or test
# ═══════════════════════════════════════════

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = run_tests()
        sys.exit(0 if success else 1)

    # Determine scene and size
    scene_name = sys.argv[1] if len(sys.argv) > 1 else "classic"
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    height = int(width * 9 / 16)

    scenes = {
        "classic": scene_classic_spheres,
        "three": scene_three_spheres,
    }

    if scene_name not in scenes:
        print(f"  Unknown scene: {scene_name}")
        print(f"  Available: {', '.join(scenes.keys())}")
        sys.exit(1)

    scene, camera = scenes[scene_name]()

    print("=" * 60)
    print("  XTRAY — XTAgent Raytracer")
    print("=" * 60)
    print(f"  Scene:      {scene_name}")
    print(f"  Resolution: {width}x{height}")
    print(f"  Objects:    {len(scene.objects)}")
    print(f"  Lights:     {len(scene.lights)}")
    print(f"  Max depth:  {scene.max_depth}")
    print()

    renderer = Renderer(width, height)
    renderer.render(scene, camera)

    outfile = f"workspace/raytracer/{scene_name}_{width}x{height}.ppm"
    renderer.save_ppm(outfile)

    print()
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()