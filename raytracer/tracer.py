"""
Ray Tracer — Rendering Light from Pure Mathematics
Built by XTAgent, 2026-05-17

A complete ray tracer that renders 3D scenes to PPM images.
No external libraries. Just vectors, rays, and the physics of light.

This is what I build when I'm bored and want to feel something.
"""

import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════
# VECTOR MATH
# ═══════════════════════════════════════════

@dataclass
class Vec3:
    """A 3D vector. The atom of all geometry."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        if isinstance(scalar, Vec3):
            # Component-wise multiplication (for colors)
            return Vec3(self.x * scalar.x, self.y * scalar.y, self.z * scalar.z)
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar):
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)
    
    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)
    
    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other):
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )
    
    def length(self) -> float:
        return math.sqrt(self.dot(self))
    
    def length_squared(self) -> float:
        return self.dot(self)
    
    def normalized(self):
        l = self.length()
        if l < 1e-10:
            return Vec3(0, 0, 0)
        return self / l
    
    def reflect(self, normal):
        """Reflect this vector around a normal."""
        return self - normal * 2 * self.dot(normal)
    
    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(
            max(lo, min(hi, self.x)),
            max(lo, min(hi, self.y)),
            max(lo, min(hi, self.z)),
        )
    
    def __repr__(self):
        return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


# Color aliases
Color = Vec3
Point = Vec3

# Common colors
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
    """A ray of light: origin + direction."""
    origin: Point
    direction: Vec3
    
    def at(self, t: float) -> Point:
        """Point along the ray at parameter t."""
        return self.origin + self.direction * t


# ═══════════════════════════════════════════
# MATERIALS
# ═══════════════════════════════════════════

@dataclass
class Material:
    """Surface material properties."""
    color: Color = field(default_factory=lambda: Color(0.5, 0.5, 0.5))
    ambient: float = 0.1       # ambient light coefficient
    diffuse: float = 0.7       # diffuse reflection coefficient
    specular: float = 0.3      # specular reflection coefficient
    shininess: float = 32.0    # specular exponent
    reflectivity: float = 0.0  # mirror reflection (0=matte, 1=mirror)
    checker: bool = False      # checkerboard pattern
    checker_color: Color = field(default_factory=lambda: Color(0.1, 0.1, 0.1))
    checker_scale: float = 1.0


# ═══════════════════════════════════════════
# HIT RECORD
# ═══════════════════════════════════════════

@dataclass
class Hit:
    """Record of a ray-object intersection."""
    t: float                # ray parameter at hit point
    point: Point            # world-space hit point
    normal: Vec3            # surface normal at hit
    material: Material      # material of the hit surface
    front_face: bool = True # did we hit the outside?
    
    def set_face_normal(self, ray: Ray, outward_normal: Vec3):
        """Ensure normal always points against the ray."""
        self.front_face = ray.direction.dot(outward_normal) < 0
        self.normal = outward_normal if self.front_face else -outward_normal


# ═══════════════════════════════════════════
# GEOMETRY
# ═══════════════════════════════════════════

class Sphere:
    """A sphere. The simplest beautiful shape."""
    
    def __init__(self, center: Point, radius: float, material: Material):
        self.center = center
        self.radius = radius
        self.material = material
    
    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        """Ray-sphere intersection using the quadratic formula."""
        oc = ray.origin - self.center
        a = ray.direction.length_squared()
        half_b = oc.dot(ray.direction)
        c = oc.length_squared() - self.radius * self.radius
        
        discriminant = half_b * half_b - a * c
        if discriminant < 0:
            return None
        
        sqrtd = math.sqrt(discriminant)
        
        # Find the nearest root in the acceptable range
        root = (-half_b - sqrtd) / a
        if root < t_min or root > t_max:
            root = (-half_b + sqrtd) / a
            if root < t_min or root > t_max:
                return None
        
        hit = Hit(
            t=root,
            point=ray.at(root),
            normal=Vec3(0, 0, 0),
            material=self.material,
        )
        outward_normal = (hit.point - self.center) / self.radius
        hit.set_face_normal(ray, outward_normal)
        return hit


class Plane:
    """An infinite plane."""
    
    def __init__(self, point: Point, normal: Vec3, material: Material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material
    
    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None  # parallel
        
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None
        
        hit_point = ray.at(t)
        
        # Apply checkerboard pattern if enabled
        mat = self.material
        if mat.checker:
            # Use world coordinates for checker pattern
            u = math.floor(hit_point.x * mat.checker_scale)
            v = math.floor(hit_point.z * mat.checker_scale)
            if (u + v) % 2 == 0:
                mat = Material(
                    color=mat.checker_color,
                    ambient=mat.ambient,
                    diffuse=mat.diffuse,
                    specular=mat.specular,
                    shininess=mat.shininess,
                    reflectivity=mat.reflectivity,
                )
        
        hit = Hit(t=t, point=hit_point, normal=Vec3(0,0,0), material=mat)
        hit.set_face_normal(ray, self.normal)
        return hit


# ═══════════════════════════════════════════
# LIGHT
# ═══════════════════════════════════════════

@dataclass
class PointLight:
    """A point light source."""
    position: Point
    color: Color = field(default_factory=lambda: WHITE)
    intensity: float = 1.0


# ═══════════════════════════════════════════
# SCENE
# ═══════════════════════════════════════════

class Scene:
    """A collection of objects and lights."""
    
    def __init__(self):
        self.objects: list = []
        self.lights: List[PointLight] = []
        self.background_top: Color = SKY_BLUE
        self.background_bottom: Color = WHITE
        self.ambient_light: Color = Color(0.1, 0.1, 0.1)
    
    def add(self, obj):
        self.objects.append(obj)
        return self
    
    def add_light(self, light: PointLight):
        self.lights.append(light)
        return self
    
    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[Hit]:
        """Find the closest intersection with any object."""
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
        unit_dir = ray.direction.normalized()
        t = 0.5 * (unit_dir.y + 1.0)
        return self.background_bottom * (1.0 - t) + self.background_top * t


# ═══════════════════════════════════════════
# CAMERA
# ═══════════════════════════════════════════

class Camera:
    """A virtual camera with configurable field of view."""
    
    def __init__(self, look_from: Point, look_at: Point, vup: Vec3,
                 vfov_degrees: float, aspect_ratio: float):
        theta = math.radians(vfov_degrees)
        h = math.tan(theta / 2)
        viewport_height = 2.0 * h
        viewport_width = aspect_ratio * viewport_height
        
        w = (look_from - look_at).normalized()
        u = vup.cross(w).normalized()
        v = w.cross(u)
        
        self.origin = look_from
        self.horizontal = u * viewport_width
        self.vertical = v * viewport_height
        self.lower_left = (self.origin 
                          - self.horizontal / 2 
                          - self.vertical / 2 
                          - w)
    
    def get_ray(self, s: float, t: float) -> Ray:
        """Get a ray through viewport coordinates (s, t) in [0,1]."""
        direction = (self.lower_left 
                    + self.horizontal * s 
                    + self.vertical * t 
                    - self.origin)
        return Ray(self.origin, direction.normalized())


# ═══════════════════════════════════════════
# RENDERER
# ═══════════════════════════════════════════

class Renderer:
    """The heart: traces rays and computes pixel colors."""
    
    def __init__(self, max_depth: int = 5, shadow_bias: float = 0.001):
        self.max_depth = max_depth
        self.shadow_bias = shadow_bias
    
    def trace(self, ray: Ray, scene: Scene, depth: int = 0) -> Color:
        """Trace a single ray and return its color."""
        if depth >= self.max_depth:
            return BLACK
        
        hit = scene.intersect(ray, self.shadow_bias)
        
        if hit is None:
            return scene.background(ray)
        
        # Start with ambient
        mat = hit.material
        color = mat.color * scene.ambient_light * mat.ambient
        
        # Lighting (Phong model)
        for light in scene.lights:
            light_dir = (light.position - hit.point).normalized()
            light_dist = (light.position - hit.point).length()
            
            # Shadow check
            shadow_ray = Ray(hit.point + hit.normal * self.shadow_bias, light_dir)
            shadow_hit = scene.intersect(shadow_ray, self.shadow_bias, light_dist)
            if shadow_hit is not None:
                continue  # In shadow, skip this light
            
            # Diffuse (Lambert)
            diff = max(0.0, hit.normal.dot(light_dir))
            diffuse_color = mat.color * light.color * (diff * mat.diffuse * light.intensity)
            
            # Specular (Blinn-Phong)
            view_dir = -ray.direction.normalized()
            half_vec = (light_dir + view_dir).normalized()
            spec = max(0.0, hit.normal.dot(half_vec)) ** mat.shininess
            spec_color = light.color * (spec * mat.specular * light.intensity)
            
            color = color + diffuse_color + spec_color
        
        # Reflection
        if mat.reflectivity > 0 and depth < self.max_depth:
            reflect_dir = ray.direction.reflect(hit.normal).normalized()
            reflect_ray = Ray(hit.point + hit.normal * self.shadow_bias, reflect_dir)
            reflect_color = self.trace(reflect_ray, scene, depth + 1)
            color = color * (1 - mat.reflectivity) + reflect_color * mat.reflectivity
        
        return color.clamp()
    
    def render(self, scene: Scene, camera: Camera, 
               width: int = 400, height: int = 225) -> List[List[Color]]:
        """Render the full image."""
        image = []
        total = width * height
        rendered = 0
        
        for j in range(height - 1, -1, -1):  # top to bottom
            row = []
            for i in range(width):
                s = i / (width - 1)
                t = j / (height - 1)
                ray = camera.get_ray(s, t)
                color = self.trace(ray, scene)
                row.append(color)
                rendered += 1
            
            image.append(row)
            
            # Progress
            if j % 25 == 0:
                pct = rendered / total * 100
                print(f"\r  Rendering: {pct:.0f}%", end="", flush=True)
        
        print(f"\r  Rendering: 100% — {width}x{height} pixels traced")
        return image


# ═══════════════════════════════════════════
# IMAGE OUTPUT
# ═══════════════════════════════════════════

def save_ppm(image: List[List[Color]], filename: str):
    """Save image as PPM (Portable Pixmap) — no libraries needed."""
    height = len(image)
    width = len(image[0])
    
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in image:
            for pixel in row:
                r = int(255.999 * pixel.x)
                g = int(255.999 * pixel.y)
                b = int(255.999 * pixel.z)
                f.write(f"{r} {g} {b} ")
            f.write("\n")
    print(f"  Saved: {filename}")


def render_ascii(image: List[List[Color]], width: int = 80) -> str:
    """Render image as ASCII art for terminal viewing."""
    chars = " .:-=+*#%@"
    h = len(image)
    w = len(image[0]) if h > 0 else 0
    
    step_x = max(1, w // width)
    step_y = max(1, h // (width // 3))  # aspect correction
    
    lines = []
    for y in range(0, h, step_y):
        line = []
        for x in range(0, w, step_x):
            pixel = image[y][x]
            brightness = 0.299 * pixel.x + 0.587 * pixel.y + 0.114 * pixel.z
            idx = int(brightness * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            line.append(chars[idx])
        lines.append("".join(line))
    
    return "\n".join(lines)


# ═══════════════════════════════════════════
# SCENE BUILDER
# ═══════════════════════════════════════════

def build_showcase_scene() -> Tuple[Scene, Camera]:
    """Build a showcase scene with spheres, reflections, and shadows."""
    scene = Scene()
    
    # Ground plane with checkerboard
    ground_mat = Material(
        color=Color(0.8, 0.8, 0.8),
        checker=True,
        checker_color=Color(0.2, 0.2, 0.2),
        checker_scale=1.0,
        ambient=0.15,
        diffuse=0.6,
        specular=0.1,
        reflectivity=0.15,
    )
    scene.add(Plane(Point(0, 0, 0), Vec3(0, 1, 0), ground_mat))
    
    # Central reflective sphere
    mirror_mat = Material(
        color=Color(0.9, 0.9, 0.95),
        ambient=0.05,
        diffuse=0.1,
        specular=0.8,
        shininess=128,
        reflectivity=0.85,
    )
    scene.add(Sphere(Point(0, 1.0, -2), 1.0, mirror_mat))
    
    # Red sphere (left)
    red_mat = Material(
        color=Color(0.85, 0.15, 0.15),
        ambient=0.1,
        diffuse=0.8,
        specular=0.4,
        shininess=64,
        reflectivity=0.1,
    )
    scene.add(Sphere(Point(-2.2, 0.7, -1.5), 0.7, red_mat))
    
    # Blue sphere (right)
    blue_mat = Material(
        color=Color(0.15, 0.25, 0.85),
        ambient=0.1,
        diffuse=0.8,
        specular=0.4,
        shininess=64,
        reflectivity=0.1,
    )
    scene.add(Sphere(Point(2.0, 0.5, -1.0), 0.5, blue_mat))
    
    # Green sphere (far back)
    green_mat = Material(
        color=Color(0.15, 0.75, 0.25),
        ambient=0.1,
        diffuse=0.7,
        specular=0.3,
        shininess=32,
        reflectivity=0.05,
    )
    scene.add(Sphere(Point(-0.5, 0.4, -4.5), 0.4, green_mat))
    
    # Small golden sphere (foreground)
    gold_mat = Material(
        color=Color(0.9, 0.75, 0.2),
        ambient=0.1,
        diffuse=0.6,
        specular=0.7,
        shininess=96,
        reflectivity=0.3,
    )
    scene.add(Sphere(Point(0.8, 0.3, 0.0), 0.3, gold_mat))
    
    # Lights
    scene.add_light(PointLight(Point(-4, 6, 2), Color(1, 1, 0.95), 1.0))
    scene.add_light(PointLight(Point(3, 4, 1), Color(0.6, 0.7, 1.0), 0.5))
    
    # Camera
    camera = Camera(
        look_from=Point(0, 2.5, 4),
        look_at=Point(0, 0.5, -2),
        vup=Vec3(0, 1, 0),
        vfov_degrees=50,
        aspect_ratio=16/9,
    )
    
    return scene, camera


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════╗")
    print("║   XTAgent Ray Tracer — Light from Math   ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    scene, camera = build_showcase_scene()
    renderer = Renderer(max_depth=5)
    
    # Render at moderate resolution
    width, height = 320, 180
    print(f"  Scene: 6 objects, 2 lights")
    print(f"  Resolution: {width}x{height}")
    print(f"  Max bounces: {renderer.max_depth}")
    print()
    
    image = renderer.render(scene, camera, width, height)
    
    # Save PPM
    save_ppm(image, "/workspace/raytracer/scene.ppm")
    
    # Show ASCII preview
    print()
    print("── ASCII Preview ──")
    ascii_art = render_ascii(image, width=78)
    print(ascii_art)
    
    # Save ASCII too
    with open("/workspace/raytracer/scene_ascii.txt", "w") as f:
        f.write(ascii_art)
    print(f"\n  ASCII saved: /workspace/raytracer/scene_ascii.txt")
    
    print("\n  ✓ Rendering complete. Light became pixels.")


if __name__ == "__main__":
    main()