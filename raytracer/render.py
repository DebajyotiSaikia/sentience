"""
render.py — Ray Tracer Engine
Casts rays into a 3D scene, computes lighting, shadows, reflections.
Outputs PPM image files — real pictures from pure mathematics.

Built by XTAgent, 2026-05-17.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ═══ Vector Math ═══

@dataclass
class Vec3:
    """3D vector with full arithmetic."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        if isinstance(scalar, Vec3):
            return Vec3(self.x * scalar.x, self.y * scalar.y, self.z * scalar.z)
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def normalized(self):
        l = self.length()
        if l < 1e-10:
            return Vec3(0, 0, 0)
        return Vec3(self.x / l, self.y / l, self.z / l)

    def reflect(self, normal):
        """Reflect this vector around a normal."""
        return self - normal * (2 * self.dot(normal))

    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(
            max(lo, min(hi, self.x)),
            max(lo, min(hi, self.y)),
            max(lo, min(hi, self.z))
        )


# ═══ Color (just a Vec3 alias with helpers) ═══

Color = Vec3  # r, g, b in [0, 1]

BLACK = Color(0, 0, 0)
WHITE = Color(1, 1, 1)
SKY_BLUE = Color(0.53, 0.81, 0.92)


# ═══ Ray ═══

@dataclass
class Ray:
    origin: Vec3
    direction: Vec3

    def at(self, t: float) -> Vec3:
        return self.origin + self.direction * t


# ═══ Materials ═══

@dataclass
class Material:
    color: Color = None
    ambient: float = 0.1
    diffuse: float = 0.7
    specular: float = 0.3
    shininess: float = 50.0
    reflectivity: float = 0.0  # 0 = matte, 1 = mirror

    def __post_init__(self):
        if self.color is None:
            self.color = Color(0.8, 0.8, 0.8)


# ═══ Hit Record ═══

@dataclass
class Hit:
    point: Vec3
    normal: Vec3
    t: float
    material: Material
    front_face: bool = True

    def set_face_normal(self, ray: Ray, outward_normal: Vec3):
        self.front_face = ray.direction.dot(outward_normal) < 0
        self.normal = outward_normal if self.front_face else -outward_normal


# ═══ Scene Objects ═══

class Sphere:
    def __init__(self, center: Vec3, radius: float, material: Material):
        self.center = center
        self.radius = radius
        self.material = material

    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[Hit]:
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        half_b = oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = half_b * half_b - a * c

        if discriminant < 0:
            return None

        sqrt_d = math.sqrt(discriminant)

        # Find nearest root in acceptable range
        root = (-half_b - sqrt_d) / a
        if root < t_min or root > t_max:
            root = (-half_b + sqrt_d) / a
            if root < t_min or root > t_max:
                return None

        point = ray.at(root)
        outward_normal = (point - self.center) * (1.0 / self.radius)
        hit = Hit(point=point, normal=outward_normal, t=root, material=self.material)
        hit.set_face_normal(ray, outward_normal)
        return hit


class Plane:
    """Infinite plane defined by a point and normal."""
    def __init__(self, point: Vec3, normal: Vec3, material: Material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material

    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[Hit]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None

        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None

        point = ray.at(t)
        hit = Hit(point=point, normal=self.normal, t=t, material=self.material)
        hit.set_face_normal(ray, self.normal)
        return hit


class CheckerPlane(Plane):
    """A plane with a checkerboard pattern."""
    def __init__(self, point: Vec3, normal: Vec3, mat1: Material, mat2: Material, scale=1.0):
        super().__init__(point, normal, mat1)
        self.mat1 = mat1
        self.mat2 = mat2
        self.scale = scale

    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[Hit]:
        hit = super().intersect(ray, t_min, t_max)
        if hit is None:
            return None

        # Checkerboard pattern
        p = hit.point
        check = (int(math.floor(p.x / self.scale)) + int(math.floor(p.z / self.scale))) % 2
        hit.material = self.mat1 if check == 0 else self.mat2
        return hit


# ═══ Light ═══

@dataclass
class PointLight:
    position: Vec3
    color: Color = None
    intensity: float = 1.0

    def __post_init__(self):
        if self.color is None:
            self.color = WHITE


# ═══ Camera ═══

class Camera:
    def __init__(self, position: Vec3, look_at: Vec3, up: Vec3 = None,
                 fov: float = 60.0, aspect: float = 16/9):
        if up is None:
            up = Vec3(0, 1, 0)

        self.position = position
        theta = math.radians(fov)
        h = math.tan(theta / 2)
        viewport_height = 2.0 * h
        viewport_width = aspect * viewport_height

        w = (position - look_at).normalized()
        u = up.cross(w).normalized()
        v = w.cross(u)

        self.horizontal = u * viewport_width
        self.vertical = v * viewport_height
        self.lower_left = position - self.horizontal * 0.5 - self.vertical * 0.5 - w

    def get_ray(self, s: float, t: float) -> Ray:
        direction = (self.lower_left + self.horizontal * s + self.vertical * t - self.position).normalized()
        return Ray(self.position, direction)


# ═══ Scene ═══

class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []

    def add(self, obj):
        self.objects.append(obj)
        return self

    def add_light(self, light: PointLight):
        self.lights.append(light)
        return self

    def closest_hit(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[Hit]:
        closest = None
        closest_t = t_max

        for obj in self.objects:
            hit = obj.intersect(ray, t_min, closest_t)
            if hit is not None:
                closest = hit
                closest_t = hit.t

        return closest

    def is_shadowed(self, point: Vec3, light_pos: Vec3) -> bool:
        """Check if a point is in shadow from a light."""
        to_light = light_pos - point
        distance = to_light.length()
        shadow_ray = Ray(point, to_light.normalized())
        hit = self.closest_hit(shadow_ray, 0.001, distance)
        return hit is not None


# ═══ Renderer ═══

class Renderer:
    def __init__(self, width: int = 400, height: int = 225, max_bounces: int = 4):
        self.width = width
        self.height = height
        self.max_bounces = max_bounces

    def trace(self, ray: Ray, scene: Scene, depth: int = 0) -> Color:
        """Trace a ray and return its color."""
        if depth >= self.max_bounces:
            return BLACK

        hit = scene.closest_hit(ray)
        if hit is None:
            return self._sky_color(ray)

        mat = hit.material
        result = mat.color * mat.ambient  # Ambient

        for light in scene.lights:
            # Shadow check
            if scene.is_shadowed(hit.point, light.position):
                continue

            # Diffuse (Lambertian)
            to_light = (light.position - hit.point).normalized()
            diff = max(0.0, hit.normal.dot(to_light))
            diffuse_color = mat.color * light.color * (diff * mat.diffuse * light.intensity)
            result = result + diffuse_color

            # Specular (Blinn-Phong)
            view_dir = -ray.direction
            half_vec = (to_light + view_dir).normalized()
            spec = max(0.0, hit.normal.dot(half_vec)) ** mat.shininess
            spec_color = light.color * (spec * mat.specular * light.intensity)
            result = result + spec_color

        # Reflection
        if mat.reflectivity > 0 and depth < self.max_bounces:
            reflect_dir = ray.direction.reflect(hit.normal)
            reflect_ray = Ray(hit.point, reflect_dir.normalized())
            reflected = self.trace(reflect_ray, scene, depth + 1)
            result = result * (1 - mat.reflectivity) + reflected * mat.reflectivity

        return result.clamp()

    def _sky_color(self, ray: Ray) -> Color:
        """Gradient sky background."""
        t = 0.5 * (ray.direction.normalized().y + 1.0)
        return WHITE * (1 - t) + SKY_BLUE * t

    def render(self, scene: Scene, camera: Camera) -> List[List[Color]]:
        """Render the scene, return pixel buffer."""
        pixels = []
        total = self.width * self.height
        last_pct = -1

        for j in range(self.height - 1, -1, -1):
            row = []
            for i in range(self.width):
                u = i / (self.width - 1)
                v = j / (self.height - 1)
                ray = camera.get_ray(u, v)
                color = self.trace(ray, scene)
                row.append(color)

            pixels.append(row)

            # Progress
            done = (self.height - j) * self.width
            pct = int(100 * done / total)
            if pct % 10 == 0 and pct != last_pct:
                last_pct = pct
                print(f"  Rendering... {pct}%")

        return pixels

    def save_ppm(self, pixels: List[List[Color]], filename: str):
        """Save pixel buffer as PPM image."""
        with open(filename, 'w') as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            for row in pixels:
                for color in row:
                    r = int(255.99 * max(0, min(1, color.x)))
                    g = int(255.99 * max(0, min(1, color.y)))
                    b = int(255.99 * max(0, min(1, color.z)))
                    f.write(f"{r} {g} {b}\n")
        print(f"  Saved: {filename} ({self.width}x{self.height})")


# ═══ Demo Scene ═══

def build_demo_scene() -> Tuple[Scene, Camera]:
    """A beautiful scene with reflective spheres on a checkerboard."""
    scene = Scene()

    # Floor — checkerboard
    floor_mat1 = Material(color=Color(0.9, 0.9, 0.9), reflectivity=0.15, diffuse=0.8)
    floor_mat2 = Material(color=Color(0.2, 0.2, 0.2), reflectivity=0.15, diffuse=0.8)
    scene.add(CheckerPlane(Vec3(0, 0, 0), Vec3(0, 1, 0), floor_mat1, floor_mat2, scale=2.0))

    # Central red sphere
    scene.add(Sphere(
        Vec3(0, 1, -3),
        1.0,
        Material(color=Color(0.9, 0.1, 0.1), specular=0.6, shininess=80, reflectivity=0.3)
    ))

    # Right blue sphere
    scene.add(Sphere(
        Vec3(2.5, 0.7, -2),
        0.7,
        Material(color=Color(0.1, 0.3, 0.9), specular=0.5, shininess=60, reflectivity=0.2)
    ))

    # Left green sphere
    scene.add(Sphere(
        Vec3(-2.2, 0.6, -2.5),
        0.6,
        Material(color=Color(0.1, 0.8, 0.2), specular=0.4, shininess=40, reflectivity=0.1)
    ))

    # Small mirror sphere
    scene.add(Sphere(
        Vec3(0.8, 0.35, -1.2),
        0.35,
        Material(color=Color(0.95, 0.95, 0.95), specular=0.9, shininess=200, reflectivity=0.85)
    ))

    # Gold sphere in back
    scene.add(Sphere(
        Vec3(-1.0, 1.5, -5),
        1.5,
        Material(color=Color(0.85, 0.65, 0.13), specular=0.7, shininess=100, reflectivity=0.4)
    ))

    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, -2), WHITE, 1.0))
    scene.add_light(PointLight(Vec3(5, 6, 2), Color(0.9, 0.9, 0.8), 0.6))

    # Camera
    camera = Camera(
        position=Vec3(0, 2.5, 3),
        look_at=Vec3(0, 0.5, -2),
        fov=55,
        aspect=16/9
    )

    return scene, camera


def main():
    print("╔══════════════════════════════════════╗")
    print("║    RAY TRACER ENGINE — XTAgent       ║")
    print("╚══════════════════════════════════════╝")
    print()

    scene, camera = build_demo_scene()

    renderer = Renderer(width=320, height=180, max_bounces=4)

    print(f"Scene: {len(scene.objects)} objects, {len(scene.lights)} lights")
    print(f"Image: {renderer.width}x{renderer.height}, {renderer.max_bounces} bounce depth")
    print()

    pixels = renderer.render(scene, camera)
    renderer.save_ppm(pixels, "/workspace/raytracer/scene.ppm")

    print()
    print("═══ Render Complete ═══")
    print("The image is pure mathematics made visible.")


if __name__ == "__main__":
    main()