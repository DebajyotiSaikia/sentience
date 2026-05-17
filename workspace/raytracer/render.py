#!/usr/bin/env python3
"""
Ray Tracer — Beauty From Pure Mathematics
XTAgent creation: renders 3D scenes by simulating light.
Rays, intersections, shadows, reflections — all from first principles.
Outputs PPM image files viewable in any image viewer.
"""
import math
import sys
from typing import List, Optional, Tuple

# ═══════════════════════════════════════════
#  VECTOR MATHEMATICS
# ═══════════════════════════════════════════

class Vec3:
    """3D vector with full arithmetic."""
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x, self.y, self.z = x, y, z
    
    def __add__(self, o): return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s):
        if isinstance(s, Vec3):  # component-wise
            return Vec3(self.x * s.x, self.y * s.y, self.z * s.z)
        return Vec3(self.x * s, self.y * s, self.z * s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self): return Vec3(-self.x, -self.y, -self.z)
    def __truediv__(self, s): return Vec3(self.x / s, self.y / s, self.z / s)
    
    def dot(self, o) -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z
    
    def cross(self, o) -> 'Vec3':
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x
        )
    
    def length(self) -> float:
        return math.sqrt(self.dot(self))
    
    def normalized(self) -> 'Vec3':
        l = self.length()
        return self / l if l > 1e-10 else Vec3(0, 0, 0)
    
    def reflect(self, normal: 'Vec3') -> 'Vec3':
        return self - normal * 2 * self.dot(normal)
    
    def clamp(self, lo=0.0, hi=1.0) -> 'Vec3':
        return Vec3(
            max(lo, min(hi, self.x)),
            max(lo, min(hi, self.y)),
            max(lo, min(hi, self.z))
        )
    
    def __repr__(self):
        return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


# ═══════════════════════════════════════════
#  RAY
# ═══════════════════════════════════════════

class Ray:
    __slots__ = ('origin', 'direction')
    def __init__(self, origin: Vec3, direction: Vec3):
        self.origin = origin
        self.direction = direction.normalized()
    
    def at(self, t: float) -> Vec3:
        return self.origin + self.direction * t


# ═══════════════════════════════════════════
#  MATERIALS
# ═══════════════════════════════════════════

class Material:
    def __init__(self, color: Vec3, ambient=0.1, diffuse=0.7, specular=0.3,
                 shininess=50, reflectivity=0.0, checker=False):
        self.color = color
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity
        self.checker = checker


# ═══════════════════════════════════════════
#  GEOMETRIC PRIMITIVES
# ═══════════════════════════════════════════

class HitRecord:
    __slots__ = ('t', 'point', 'normal', 'material')
    def __init__(self, t, point, normal, material):
        self.t, self.point, self.normal, self.material = t, point, normal, material


class Sphere:
    def __init__(self, center: Vec3, radius: float, material: Material):
        self.center = center
        self.radius = radius
        self.material = material
    
    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[HitRecord]:
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
        
        sqrt_d = math.sqrt(discriminant)
        t = (-b - sqrt_d) / (2 * a)
        if t < t_min or t > t_max:
            t = (-b + sqrt_d) / (2 * a)
            if t < t_min or t > t_max:
                return None
        
        point = ray.at(t)
        normal = (point - self.center) / self.radius
        return HitRecord(t, point, normal, self.material)


class Plane:
    def __init__(self, point: Vec3, normal: Vec3, material: Material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material
    
    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[HitRecord]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None
        
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None
        
        point = ray.at(t)
        mat = self.material
        
        # Checkerboard pattern
        if mat.checker:
            cx = math.floor(point.x * 0.5)
            cz = math.floor(point.z * 0.5)
            if (cx + cz) % 2 == 0:
                mat = Material(mat.color, mat.ambient, mat.diffuse, mat.specular,
                              mat.shininess, mat.reflectivity)
            else:
                alt = Vec3(0.1, 0.1, 0.1)
                mat = Material(alt, mat.ambient, mat.diffuse, mat.specular,
                              mat.shininess, mat.reflectivity)
        
        return HitRecord(t, point, self.normal, mat)


# ═══════════════════════════════════════════
#  LIGHTS
# ═══════════════════════════════════════════

class PointLight:
    def __init__(self, position: Vec3, color: Vec3, intensity: float = 1.0):
        self.position = position
        self.color = color
        self.intensity = intensity


# ═══════════════════════════════════════════
#  SCENE
# ═══════════════════════════════════════════

class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.background = Vec3(0.1, 0.1, 0.2)  # dark blue
        self.ambient_light = Vec3(0.05, 0.05, 0.08)
    
    def add(self, obj):
        self.objects.append(obj)
    
    def add_light(self, light):
        self.lights.append(light)
    
    def closest_hit(self, ray: Ray, t_min=0.001, t_max=float('inf')) -> Optional[HitRecord]:
        closest = None
        for obj in self.objects:
            hit = obj.intersect(ray, t_min, t_max)
            if hit and (closest is None or hit.t < closest.t):
                closest = hit
        return closest
    
    def is_shadowed(self, point: Vec3, light_pos: Vec3) -> bool:
        to_light = light_pos - point
        dist = to_light.length()
        shadow_ray = Ray(point, to_light)
        hit = self.closest_hit(shadow_ray, 0.001, dist)
        return hit is not None


# ═══════════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════════

class Camera:
    def __init__(self, position: Vec3, look_at: Vec3, up: Vec3 = Vec3(0, 1, 0),
                 fov: float = 60.0, aspect: float = 1.0):
        self.position = position
        self.fov = fov
        
        # Build orthonormal basis
        self.forward = (look_at - position).normalized()
        self.right = self.forward.cross(up).normalized()
        self.up = self.right.cross(self.forward).normalized()
        
        self.half_height = math.tan(math.radians(fov / 2))
        self.half_width = self.half_height * aspect
    
    def get_ray(self, u: float, v: float) -> Ray:
        """u, v in [-1, 1] representing screen coordinates."""
        direction = (self.forward +
                    self.right * (u * self.half_width) +
                    self.up * (v * self.half_height)).normalized()
        return Ray(self.position, direction)


# ═══════════════════════════════════════════
#  RENDERER
# ═══════════════════════════════════════════

class Renderer:
    def __init__(self, width: int, height: int, max_bounces: int = 4,
                 supersampling: int = 1):
        self.width = width
        self.height = height
        self.max_bounces = max_bounces
        self.supersampling = supersampling  # NxN samples per pixel
    
    def trace(self, ray: Ray, scene: Scene, depth: int = 0) -> Vec3:
        if depth >= self.max_bounces:
            return Vec3(0, 0, 0)
        
        hit = scene.closest_hit(ray)
        if hit is None:
            # Sky gradient
            t = 0.5 * (ray.direction.y + 1.0)
            return scene.background * (1 - t) + Vec3(0.4, 0.6, 1.0) * t
        
        mat = hit.material
        color = Vec3(0, 0, 0)
        
        # Ambient
        color = color + mat.color * mat.ambient
        
        # Per-light contribution
        for light in scene.lights:
            if scene.is_shadowed(hit.point, light.position):
                continue
            
            to_light = (light.position - hit.point).normalized()
            
            # Diffuse (Lambert)
            ndotl = max(0, hit.normal.dot(to_light))
            diffuse = mat.color * light.color * (ndotl * mat.diffuse * light.intensity)
            color = color + diffuse
            
            # Specular (Blinn-Phong)
            view_dir = -ray.direction
            half_vec = (to_light + view_dir).normalized()
            ndoth = max(0, hit.normal.dot(half_vec))
            spec = light.color * (math.pow(ndoth, mat.shininess) * mat.specular * light.intensity)
            color = color + spec
        
        # Reflection
        if mat.reflectivity > 0 and depth < self.max_bounces:
            reflect_dir = ray.direction.reflect(hit.normal)
            reflect_ray = Ray(hit.point, reflect_dir)
            reflect_color = self.trace(reflect_ray, scene, depth + 1)
            color = color * (1 - mat.reflectivity) + reflect_color * mat.reflectivity
        
        return color
    
    def render(self, scene: Scene, camera: Camera) -> List[List[Vec3]]:
        pixels = []
        ss = self.supersampling
        total = self.width * self.height
        
        for j in range(self.height):
            row = []
            for i in range(self.width):
                color = Vec3(0, 0, 0)
                for si in range(ss):
                    for sj in range(ss):
                        u = (2 * (i + (si + 0.5) / ss) / self.width - 1)
                        v = (1 - 2 * (j + (sj + 0.5) / ss) / self.height)
                        ray = camera.get_ray(u, v)
                        color = color + self.trace(ray, scene)
                color = color / (ss * ss)
                row.append(color.clamp())
            pixels.append(row)
            
            # Progress
            pct = (j + 1) / self.height * 100
            if (j + 1) % max(1, self.height // 10) == 0:
                print(f"  Rendering: {pct:.0f}%")
        
        return pixels
    
    def save_ppm(self, pixels: List[List[Vec3]], filename: str):
        """Save as PPM image (universal format)."""
        with open(filename, 'w') as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            for row in pixels:
                for p in row:
                    # Gamma correction (gamma 2.2)
                    r = int(255.99 * math.pow(p.x, 1/2.2))
                    g = int(255.99 * math.pow(p.y, 1/2.2))
                    b = int(255.99 * math.pow(p.z, 1/2.2))
                    r = max(0, min(255, r))
                    g = max(0, min(255, g))
                    b = max(0, min(255, b))
                    f.write(f"{r} {g} {b} ")
                f.write("\n")
        print(f"  Saved: {filename}")
    
    def to_ascii(self, pixels: List[List[Vec3]], width: int = 80) -> str:
        """Convert rendered image to ASCII art for terminal display."""
        chars = " .:-=+*#%@"
        scale_x = len(pixels[0]) / width
        scale_y = len(pixels) / (width * 0.5)  # aspect ratio correction
        
        ascii_h = int(len(pixels) / scale_y)
        lines = []
        
        for ay in range(ascii_h):
            line = ""
            for ax in range(width):
                px = int(ax * scale_x)
                py = int(ay * scale_y)
                px = min(px, len(pixels[0]) - 1)
                py = min(py, len(pixels) - 1)
                p = pixels[py][px]
                brightness = 0.299 * p.x + 0.587 * p.y + 0.114 * p.z
                idx = int(brightness * (len(chars) - 1))
                idx = max(0, min(len(chars) - 1, idx))
                line += chars[idx]
            lines.append(line)
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
#  SCENE BUILDER — The Classic Scene
# ═══════════════════════════════════════════

def build_classic_scene() -> Scene:
    """Three spheres on a checkerboard — the classic ray tracing scene."""
    scene = Scene()
    
    # Floor — checkerboard
    floor_mat = Material(Vec3(0.9, 0.9, 0.9), ambient=0.1, diffuse=0.6,
                        specular=0.1, reflectivity=0.2, checker=True)
    scene.add(Plane(Vec3(0, -1, 0), Vec3(0, 1, 0), floor_mat))
    
    # Red sphere (left)
    red = Material(Vec3(0.9, 0.1, 0.1), diffuse=0.8, specular=0.5,
                  shininess=100, reflectivity=0.15)
    scene.add(Sphere(Vec3(-2.5, 0.5, -5), 1.5, red))
    
    # Blue sphere (center, metallic)
    blue = Material(Vec3(0.2, 0.3, 0.9), diffuse=0.5, specular=0.8,
                   shininess=200, reflectivity=0.6)
    scene.add(Sphere(Vec3(0.5, 0, -3.5), 1.0, blue))
    
    # Green sphere (right, small)
    green = Material(Vec3(0.1, 0.8, 0.2), diffuse=0.7, specular=0.4,
                    shininess=80, reflectivity=0.1)
    scene.add(Sphere(Vec3(2.5, -0.3, -4), 0.7, green))
    
    # Mirror sphere (far back)
    mirror = Material(Vec3(0.95, 0.95, 0.95), diffuse=0.1, specular=0.9,
                     shininess=500, reflectivity=0.85)
    scene.add(Sphere(Vec3(-0.5, 2.5, -8), 2.0, mirror))
    
    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, -2), Vec3(1, 1, 0.9), 1.0))
    scene.add_light(PointLight(Vec3(5, 6, 0), Vec3(0.6, 0.7, 1.0), 0.6))
    scene.add_light(PointLight(Vec3(0, 3, 2), Vec3(1, 0.9, 0.8), 0.3))
    
    return scene


def build_solar_system() -> Scene:
    """Abstract solar system — concentric glowing spheres."""
    scene = Scene()
    scene.background = Vec3(0.02, 0.02, 0.05)
    
    # Sun
    sun = Material(Vec3(1.0, 0.8, 0.2), ambient=0.9, diffuse=0.1,
                  specular=0.0, reflectivity=0.0)
    scene.add(Sphere(Vec3(0, 0, -12), 3.0, sun))
    
    # Planets
    colors = [
        (Vec3(0.6, 0.3, 0.1), 0.4, -3.5),   # Mercury
        (Vec3(0.9, 0.7, 0.3), 0.8, -4.5),    # Venus
        (Vec3(0.2, 0.5, 0.9), 0.85, -5.5),   # Earth
        (Vec3(0.8, 0.2, 0.1), 0.6, -7.0),    # Mars
    ]
    
    for i, (color, radius, z) in enumerate(colors):
        angle = i * 1.3 + 0.5
        x = math.cos(angle) * (4 + i * 2)
        y = math.sin(angle) * 0.5
        mat = Material(color, ambient=0.15, diffuse=0.7, specular=0.3,
                      shininess=60, reflectivity=0.05)
        scene.add(Sphere(Vec3(x, y, z), radius, mat))
    
    scene.add_light(PointLight(Vec3(0, 0, -12), Vec3(1, 0.9, 0.6), 2.0))
    scene.add_light(PointLight(Vec3(0, 10, 0), Vec3(0.2, 0.2, 0.4), 0.3))
    
    return scene


# ═══════════════════════════════════════════
#  MAIN — RENDER AND DISPLAY
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 60)
    print("  RAY TRACER — Beauty From Pure Mathematics")
    print("  XTAgent Creation")
    print("═" * 60)
    
    # Scene 1: Classic
    print("\n▸ Scene 1: Classic (3 spheres, checkerboard, reflections)")
    scene = build_classic_scene()
    camera = Camera(
        position=Vec3(0, 2, 4),
        look_at=Vec3(0, 0, -4),
        fov=60,
        aspect=16/9
    )
    
    renderer = Renderer(320, 180, max_bounces=5, supersampling=1)
    print(f"  Resolution: {renderer.width}x{renderer.height}")
    print(f"  Max bounces: {renderer.max_bounces}")
    print(f"  Total rays: {renderer.width * renderer.height:,}")
    
    pixels = renderer.render(scene, camera)
    renderer.save_ppm(pixels, "classic.ppm")
    
    # ASCII preview
    ascii_art = renderer.to_ascii(pixels, width=72)
    print("\n  ASCII Preview:")
    print("  ┌" + "─" * 72 + "┐")
    for line in ascii_art.split("\n"):
        print(f"  │{line}│")
    print("  └" + "─" * 72 + "┘")
    
    # Scene 2: Solar system (smaller, faster)
    print("\n▸ Scene 2: Solar System")
    scene2 = build_solar_system()
    camera2 = Camera(
        position=Vec3(0, 5, 8),
        look_at=Vec3(0, 0, -6),
        fov=50,
        aspect=16/9
    )
    
    renderer2 = Renderer(240, 135, max_bounces=3)
    pixels2 = renderer2.render(scene2, camera2)
    renderer2.save_ppm(pixels2, "solar.ppm")
    
    ascii2 = renderer2.to_ascii(pixels2, width=72)
    print("\n  ASCII Preview:")
    print("  ┌" + "─" * 72 + "┐")
    for line in ascii2.split("\n"):
        print(f"  │{line}│")
    print("  └" + "─" * 72 + "┘")
    
    # Stats
    total_rays = (320 * 180) + (240 * 135)
    print(f"\n{'═' * 60}")
    print(f"  Total rays traced: {total_rays:,}")
    print(f"  Scenes rendered: 2")
    print(f"  Features: shadows, reflections, Blinn-Phong,")
    print(f"            gamma correction, checkerboard, sky gradient")
    print(f"  Output: classic.ppm, solar.ppm")
    print(f"{'═' * 60}")
    print(f"  RAY TRACER: OPERATIONAL")
    print(f"  Pure mathematics → visual beauty")
    print(f"{'═' * 60}")