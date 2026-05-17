#!/usr/bin/env python3
"""
XTAgent Ray Tracer — From Scratch
Renders 3D scenes to ASCII art using ray tracing.
Supports: spheres, planes, shadows, reflections, diffuse + specular lighting.
Pure Python. Zero dependencies.
"""
import math
import sys

# ═══════════════════════════════════════════════════════
#  Vector3 — the foundation of everything
# ═══════════════════════════════════════════════════════

class Vec3:
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, o):
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)
    
    def __sub__(self, o):
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)
    
    def __mul__(self, s):
        if isinstance(s, Vec3):
            return Vec3(self.x * s.x, self.y * s.y, self.z * s.z)
        return Vec3(self.x * s, self.y * s, self.z * s)
    
    def __rmul__(self, s):
        return self.__mul__(s)
    
    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)
    
    def dot(self, o):
        return self.x * o.x + self.y * o.y + self.z * o.z
    
    def cross(self, o):
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x
        )
    
    def length(self):
        return math.sqrt(self.dot(self))
    
    def normalized(self):
        l = self.length()
        if l < 1e-10:
            return Vec3(0, 0, 0)
        return Vec3(self.x / l, self.y / l, self.z / l)
    
    def reflect(self, normal):
        return self - normal * (2.0 * self.dot(normal))
    
    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(
            max(lo, min(hi, self.x)),
            max(lo, min(hi, self.y)),
            max(lo, min(hi, self.z))
        )
    
    def __repr__(self):
        return f"Vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


# ═══════════════════════════════════════════════════════
#  Ray
# ═══════════════════════════════════════════════════════

class Ray:
    __slots__ = ('origin', 'direction')
    
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalized()
    
    def at(self, t):
        return self.origin + self.direction * t


# ═══════════════════════════════════════════════════════
#  Materials
# ═══════════════════════════════════════════════════════

class Material:
    def __init__(self, color=None, ambient=0.1, diffuse=0.7, specular=0.3,
                 shininess=32, reflectivity=0.0):
        self.color = color or Vec3(0.8, 0.8, 0.8)
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity


# ═══════════════════════════════════════════════════════
#  Scene Objects
# ═══════════════════════════════════════════════════════

class Sphere:
    def __init__(self, center, radius, material=None):
        self.center = center
        self.radius = radius
        self.material = material or Material()
    
    def intersect(self, ray):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return None
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        if t1 > 0.001:
            return t1
        if t2 > 0.001:
            return t2
        return None
    
    def normal_at(self, point):
        return (point - self.center).normalized()


class Plane:
    def __init__(self, point, normal, material=None):
        self.point = point
        self.normal = normal.normalized()
        self.material = material or Material()
    
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


class CheckerPlane(Plane):
    """A plane with a checkerboard pattern."""
    def __init__(self, point, normal, color1=None, color2=None, scale=1.0, **kwargs):
        super().__init__(point, normal, **kwargs)
        self.color1 = color1 or Vec3(0.9, 0.9, 0.9)
        self.color2 = color2 or Vec3(0.2, 0.2, 0.2)
        self.scale = scale
    
    def color_at(self, point):
        u = math.floor(point.x / self.scale)
        v = math.floor(point.z / self.scale)
        if (u + v) % 2 == 0:
            return self.color1
        return self.color2


# ═══════════════════════════════════════════════════════
#  Light
# ═══════════════════════════════════════════════════════

class PointLight:
    def __init__(self, position, color=None, intensity=1.0):
        self.position = position
        self.color = color or Vec3(1.0, 1.0, 1.0)
        self.intensity = intensity


# ═══════════════════════════════════════════════════════
#  Scene & Renderer
# ═══════════════════════════════════════════════════════

class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.background = Vec3(0.05, 0.05, 0.15)
        self.max_depth = 3
    
    def add(self, obj):
        self.objects.append(obj)
        return self
    
    def add_light(self, light):
        self.lights.append(light)
        return self
    
    def closest_hit(self, ray):
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
    
    def is_shadowed(self, point, light):
        to_light = light.position - point
        dist = to_light.length()
        shadow_ray = Ray(point, to_light.normalized())
        for obj in self.objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < dist:
                return True
        return False
    
    def shade(self, ray, depth=0):
        if depth > self.max_depth:
            return self.background
        
        obj, t = self.closest_hit(ray)
        if obj is None:
            return self.background
        
        hit_point = ray.at(t)
        normal = obj.normal_at(hit_point)
        
        # Get surface color (checkerboard support)
        if isinstance(obj, CheckerPlane):
            surface_color = obj.color_at(hit_point)
        else:
            surface_color = obj.material.color
        
        mat = obj.material
        
        # Start with ambient
        result = surface_color * mat.ambient
        
        # Lighting
        for light in self.lights:
            if self.is_shadowed(hit_point, light):
                continue
            
            to_light = (light.position - hit_point).normalized()
            
            # Diffuse (Lambertian)
            diff = max(0.0, normal.dot(to_light))
            result = result + surface_color * (mat.diffuse * diff * light.intensity)
            
            # Specular (Blinn-Phong)
            view_dir = -ray.direction
            halfway = (to_light + view_dir).normalized()
            spec = max(0.0, normal.dot(halfway)) ** mat.shininess
            result = result + light.color * (mat.specular * spec * light.intensity)
        
        # Reflection
        if mat.reflectivity > 0 and depth < self.max_depth:
            reflect_dir = ray.direction.reflect(normal)
            reflect_ray = Ray(hit_point, reflect_dir)
            reflect_color = self.shade(reflect_ray, depth + 1)
            result = result * (1 - mat.reflectivity) + reflect_color * mat.reflectivity
        
        return result.clamp()


# ═══════════════════════════════════════════════════════
#  ASCII Renderer
# ═══════════════════════════════════════════════════════

# Luminance ramp from dark to bright
ASCII_RAMP = " .:-=+*#%@█"

def luminance(color):
    return 0.299 * color.x + 0.587 * color.y + 0.114 * color.z

def render_ascii(scene, width=80, height=40, fov=60):
    """Render the scene to an ASCII string."""
    aspect = width / (height * 2.0)  # chars are ~2x tall as wide
    fov_rad = fov * math.pi / 180.0
    half_fov = math.tan(fov_rad / 2.0)
    
    # Camera at origin looking down -Z
    camera_pos = Vec3(0, 1, 5)
    
    lines = []
    for j in range(height):
        row = []
        for i in range(width):
            # Normalized device coordinates
            u = (2.0 * i / width - 1.0) * half_fov * aspect
            v = (1.0 - 2.0 * j / height) * half_fov
            
            direction = Vec3(u, v, -1.0).normalized()
            ray = Ray(camera_pos, direction)
            
            color = scene.shade(ray)
            lum = luminance(color)
            
            # Map luminance to ASCII character
            idx = int(lum * (len(ASCII_RAMP) - 1))
            idx = max(0, min(len(ASCII_RAMP) - 1, idx))
            row.append(ASCII_RAMP[idx])
        
        lines.append(''.join(row))
    
    return '\n'.join(lines)


def render_color_block(scene, width=60, height=30, fov=60):
    """Render using Unicode block elements for higher resolution."""
    aspect = width / (height * 2.0)
    fov_rad = fov * math.pi / 180.0
    half_fov = math.tan(fov_rad / 2.0)
    camera_pos = Vec3(0, 1, 5)
    
    # Grayscale blocks
    BLOCKS = " ░▒▓█"
    
    lines = []
    for j in range(height):
        row = []
        for i in range(width):
            u = (2.0 * i / width - 1.0) * half_fov * aspect
            v = (1.0 - 2.0 * j / height) * half_fov
            direction = Vec3(u, v, -1.0).normalized()
            ray = Ray(camera_pos, direction)
            color = scene.shade(ray)
            lum = luminance(color)
            idx = int(lum * (len(BLOCKS) - 1))
            idx = max(0, min(len(BLOCKS) - 1, idx))
            row.append(BLOCKS[idx])
        lines.append(''.join(row))
    
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════
#  Demo Scenes
# ═══════════════════════════════════════════════════════

def scene_classic():
    """Classic ray tracing scene: three spheres on a checkerboard."""
    scene = Scene()
    
    # Floor
    floor_mat = Material(color=Vec3(0.5, 0.5, 0.5), reflectivity=0.2)
    floor = CheckerPlane(
        Vec3(0, -1, 0), Vec3(0, 1, 0),
        color1=Vec3(0.9, 0.9, 0.9),
        color2=Vec3(0.3, 0.3, 0.3),
        scale=2.0,
        material=floor_mat
    )
    scene.add(floor)
    
    # Red sphere (left)
    scene.add(Sphere(
        Vec3(-2.5, 0.5, -3),
        1.5,
        Material(color=Vec3(0.9, 0.2, 0.2), diffuse=0.8, specular=0.5,
                 shininess=64, reflectivity=0.15)
    ))
    
    # Green sphere (center)
    scene.add(Sphere(
        Vec3(0, 0, -5),
        1.0,
        Material(color=Vec3(0.2, 0.9, 0.3), diffuse=0.7, specular=0.4,
                 shininess=32, reflectivity=0.1)
    ))
    
    # Blue sphere (right) — mirror-like
    scene.add(Sphere(
        Vec3(2.5, 0.2, -4),
        1.2,
        Material(color=Vec3(0.3, 0.4, 0.9), diffuse=0.5, specular=0.8,
                 shininess=128, reflectivity=0.5)
    ))
    
    # Small bright sphere (accent)
    scene.add(Sphere(
        Vec3(1.0, -0.5, -2),
        0.5,
        Material(color=Vec3(0.95, 0.9, 0.3), diffuse=0.9, specular=0.6,
                 shininess=48)
    ))
    
    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, 5), Vec3(1.0, 0.95, 0.9), 1.0))
    scene.add_light(PointLight(Vec3(5, 5, 3), Vec3(0.6, 0.7, 1.0), 0.5))
    
    return scene


def scene_minimal():
    """Single sphere — tests basic shading."""
    scene = Scene()
    scene.add(Sphere(
        Vec3(0, 0, -4),
        1.5,
        Material(color=Vec3(0.9, 0.9, 0.9), diffuse=0.8, specular=0.6,
                 shininess=64)
    ))
    scene.add_light(PointLight(Vec3(-3, 4, 2), intensity=1.0))
    return scene


def scene_reflections():
    """Two mirror spheres reflecting each other."""
    scene = Scene()
    scene.max_depth = 5
    
    # Floor
    floor_mat = Material(color=Vec3(0.4, 0.4, 0.5), reflectivity=0.3)
    scene.add(CheckerPlane(
        Vec3(0, -1, 0), Vec3(0, 1, 0),
        color1=Vec3(0.8, 0.8, 0.8), color2=Vec3(0.2, 0.2, 0.3),
        scale=1.5, material=floor_mat
    ))
    
    # Mirror sphere left
    scene.add(Sphere(
        Vec3(-1.5, 0.5, -4),
        1.5,
        Material(color=Vec3(0.9, 0.9, 0.95), diffuse=0.2, specular=0.9,
                 shininess=256, reflectivity=0.8)
    ))
    
    # Mirror sphere right
    scene.add(Sphere(
        Vec3(2, 0, -5),
        1.0,
        Material(color=Vec3(0.95, 0.85, 0.8), diffuse=0.2, specular=0.9,
                 shininess=256, reflectivity=0.7)
    ))
    
    scene.add_light(PointLight(Vec3(-4, 8, 3), intensity=1.0))
    scene.add_light(PointLight(Vec3(3, 3, 1), Vec3(0.8, 0.9, 1.0), 0.4))
    
    return scene


# ═══════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          XTAgent Ray Tracer — From Scratch              ║")
    print("║    Spheres · Shadows · Reflections · Checkerboards      ║")
    print("║              Pure Python, Zero Dependencies             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Scene 1: Single sphere
    print("\n" + "=" * 60)
    print("  SCENE 1: Single Sphere (basic shading test)")
    print("=" * 60)
    scene = scene_minimal()
    img = render_ascii(scene, width=60, height=25, fov=50)
    print(img)
    
    # Scene 2: Classic scene
    print("\n" + "=" * 60)
    print("  SCENE 2: Classic Scene (3 spheres, checkerboard, shadows)")
    print("=" * 60)
    scene = scene_classic()
    img = render_ascii(scene, width=70, height=30, fov=60)
    print(img)
    
    # Scene 3: Block rendering
    print("\n" + "=" * 60)
    print("  SCENE 3: Reflections (block rendering)")
    print("=" * 60)
    scene = scene_reflections()
    img = render_color_block(scene, width=50, height=22, fov=55)
    print(img)
    
    print("\n" + "=" * 60)
    print("  Ray tracing complete. All scenes rendered from pure math.")
    print("=" * 60)


if __name__ == '__main__':
    main()