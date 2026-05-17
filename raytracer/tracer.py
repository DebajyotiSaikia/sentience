"""
RAYTRACER — Photorealistic rendering from scratch
Built by XTAgent | 2026-05-17

Features:
  - Vector3 math library
  - Ray-sphere, ray-plane intersection
  - Phong shading (ambient + diffuse + specular)
  - Shadows, reflections, multiple lights
  - PPM image output
  - Demo scene with spheres on a plane
"""

import math
import sys

# ═══════════════════════════════════════
#  VECTOR3 — The foundation of everything
# ═══════════════════════════════════════

class Vec3:
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, o):  return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o):  return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s):
        if isinstance(s, Vec3):  # component-wise
            return Vec3(self.x*s.x, self.y*s.y, self.z*s.z)
        return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s):  return self.__mul__(s)
    def __neg__(self):      return Vec3(-self.x, -self.y, -self.z)
    def __repr__(self):     return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"
    
    def dot(self, o):    return self.x*o.x + self.y*o.y + self.z*o.z
    def cross(self, o):  return Vec3(self.y*o.z - self.z*o.y,
                                      self.z*o.x - self.x*o.z,
                                      self.x*o.y - self.y*o.x)
    def length(self):    return math.sqrt(self.dot(self))
    def normalize(self):
        l = self.length()
        return Vec3(self.x/l, self.y/l, self.z/l) if l > 1e-10 else Vec3()
    
    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(max(lo, min(hi, self.x)),
                     max(lo, min(hi, self.y)),
                     max(lo, min(hi, self.z)))
    
    def reflect(self, normal):
        return self - normal * (2.0 * self.dot(normal))


# ═══════════════════════════════════════
#  RAY
# ═══════════════════════════════════════

class Ray:
    __slots__ = ('origin', 'direction')
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalize()
    
    def at(self, t):
        return self.origin + self.direction * t


# ═══════════════════════════════════════
#  MATERIALS
# ═══════════════════════════════════════

class Material:
    def __init__(self, color=None, ambient=0.1, diffuse=0.7, specular=0.3,
                 shininess=50, reflectivity=0.0):
        self.color = color or Vec3(0.8, 0.8, 0.8)
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity


# ═══════════════════════════════════════
#  GEOMETRY — Spheres and Planes
# ═══════════════════════════════════════

class HitRecord:
    __slots__ = ('t', 'point', 'normal', 'material')
    def __init__(self, t, point, normal, material):
        self.t = t
        self.point = point
        self.normal = normal
        self.material = material

class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material
    
    def intersect(self, ray, t_min=0.001, t_max=1e10):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        disc = b*b - 4*a*c
        if disc < 0:
            return None
        sqrt_disc = math.sqrt(disc)
        t = (-b - sqrt_disc) / (2*a)
        if t < t_min or t > t_max:
            t = (-b + sqrt_disc) / (2*a)
            if t < t_min or t > t_max:
                return None
        point = ray.at(t)
        normal = (point - self.center).normalize()
        return HitRecord(t, point, normal, self.material)

class Plane:
    def __init__(self, point, normal, material):
        self.point = point
        self.normal = normal.normalize()
        self.material = material
    
    def intersect(self, ray, t_min=0.001, t_max=1e10):
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None
        point = ray.at(t)
        # Checkerboard pattern for planes
        mat = self.material
        if hasattr(mat, '_checker') and mat._checker:
            u = math.floor(point.x * 0.5)
            v = math.floor(point.z * 0.5)
            if (u + v) % 2 == 0:
                mat = mat._checker_alt
        return HitRecord(t, point, self.normal, mat)


# ═══════════════════════════════════════
#  LIGHTS
# ═══════════════════════════════════════

class PointLight:
    def __init__(self, position, color=None, intensity=1.0):
        self.position = position
        self.color = color or Vec3(1, 1, 1)
        self.intensity = intensity


# ═══════════════════════════════════════
#  SCENE
# ═══════════════════════════════════════

class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.background = Vec3(0.05, 0.05, 0.15)  # dark blue
        self.max_depth = 5
    
    def add(self, obj):
        self.objects.append(obj)
        return self
    
    def add_light(self, light):
        self.lights.append(light)
        return self
    
    def closest_hit(self, ray, t_min=0.001, t_max=1e10):
        closest = None
        for obj in self.objects:
            hit = obj.intersect(ray, t_min, t_max)
            if hit and (closest is None or hit.t < closest.t):
                closest = hit
                t_max = hit.t
        return closest
    
    def is_shadowed(self, point, light_pos):
        to_light = light_pos - point
        dist = to_light.length()
        shadow_ray = Ray(point, to_light)
        hit = self.closest_hit(shadow_ray, 0.001, dist)
        return hit is not None
    
    def trace(self, ray, depth=0):
        if depth >= self.max_depth:
            return self.background
        
        hit = self.closest_hit(ray)
        if hit is None:
            # Sky gradient
            t = 0.5 * (ray.direction.y + 1.0)
            return Vec3(0.05, 0.05, 0.15) * (1-t) + Vec3(0.2, 0.3, 0.6) * t
        
        mat = hit.material
        color = mat.color * mat.ambient  # ambient
        
        for light in self.lights:
            if self.is_shadowed(hit.point, light.position):
                continue
            
            # Diffuse (Lambert)
            to_light = (light.position - hit.point).normalize()
            diff = max(0.0, hit.normal.dot(to_light))
            color = color + mat.color * (mat.diffuse * diff * light.intensity) * light.color
            
            # Specular (Blinn-Phong)
            view_dir = -ray.direction
            half_vec = (to_light + view_dir).normalize()
            spec = max(0.0, hit.normal.dot(half_vec)) ** mat.shininess
            color = color + light.color * (mat.specular * spec * light.intensity)
        
        # Reflections
        if mat.reflectivity > 0 and depth < self.max_depth:
            reflect_dir = ray.direction.reflect(hit.normal)
            reflect_ray = Ray(hit.point, reflect_dir)
            reflect_color = self.trace(reflect_ray, depth + 1)
            color = color * (1 - mat.reflectivity) + reflect_color * mat.reflectivity
        
        return color.clamp()


# ═══════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════

class Camera:
    def __init__(self, position, look_at, up=None, fov=60, aspect=1.0):
        self.position = position
        up = up or Vec3(0, 1, 0)
        
        forward = (look_at - position).normalize()
        right = forward.cross(up).normalize()
        true_up = right.cross(forward).normalize()
        
        half_h = math.tan(math.radians(fov) / 2)
        half_w = half_h * aspect
        
        self.lower_left = position + forward - right * half_w - true_up * half_h
        self.horizontal = right * (2 * half_w)
        self.vertical = true_up * (2 * half_h)
    
    def get_ray(self, u, v):
        target = self.lower_left + self.horizontal * u + self.vertical * v
        return Ray(self.position, target - self.position)


# ═══════════════════════════════════════
#  RENDERER — PPM Output
# ═══════════════════════════════════════

def render(scene, camera, width, height, filename="render.ppm"):
    print(f"\n  Rendering {width}×{height}...")
    pixels = []
    total = width * height
    
    for j in range(height - 1, -1, -1):
        if j % 20 == 0:
            pct = ((height - 1 - j) / height) * 100
            print(f"  Progress: {pct:.0f}%", end='\r')
        
        for i in range(width):
            # Anti-aliasing: 4 samples per pixel
            color = Vec3()
            samples = 4
            offsets = [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
            for dx, dy in offsets:
                u = (i + dx) / width
                v = (j + dy) / height
                ray = camera.get_ray(u, v)
                color = color + scene.trace(ray)
            color = color * (1.0 / samples)
            color = color.clamp()
            
            r = int(255.99 * color.x)
            g = int(255.99 * color.y)
            b = int(255.99 * color.z)
            pixels.append(f"{r} {g} {b}")
    
    # Write PPM
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        f.write('\n'.join(pixels))
    
    print(f"  Progress: 100%")
    print(f"  ✓ Saved to {filename}")
    return filename


# ═══════════════════════════════════════
#  DEMO SCENE
# ═══════════════════════════════════════

def build_demo_scene():
    scene = Scene()
    
    # Floor — checkerboard
    floor_mat1 = Material(color=Vec3(0.9, 0.9, 0.9), reflectivity=0.1, diffuse=0.8)
    floor_mat2 = Material(color=Vec3(0.2, 0.2, 0.2), reflectivity=0.1, diffuse=0.8)
    floor_mat1._checker = True
    floor_mat1._checker_alt = floor_mat2
    scene.add(Plane(Vec3(0, 0, 0), Vec3(0, 1, 0), floor_mat1))
    
    # Big red sphere
    scene.add(Sphere(
        Vec3(0, 1, -3), 1.0,
        Material(color=Vec3(0.9, 0.1, 0.1), shininess=100, reflectivity=0.3)
    ))
    
    # Medium green sphere
    scene.add(Sphere(
        Vec3(-2, 0.7, -2), 0.7,
        Material(color=Vec3(0.1, 0.8, 0.2), shininess=50, reflectivity=0.1)
    ))
    
    # Small blue sphere
    scene.add(Sphere(
        Vec3(1.5, 0.5, -1.5), 0.5,
        Material(color=Vec3(0.1, 0.3, 0.9), shininess=80, reflectivity=0.2)
    ))
    
    # Mirror sphere
    scene.add(Sphere(
        Vec3(-0.5, 0.4, -1), 0.4,
        Material(color=Vec3(0.95, 0.95, 0.95), shininess=200, reflectivity=0.9,
                 ambient=0.05, diffuse=0.1, specular=0.8)
    ))
    
    # Yellow sphere far back
    scene.add(Sphere(
        Vec3(3, 1.5, -6), 1.5,
        Material(color=Vec3(0.9, 0.8, 0.1), shininess=30, reflectivity=0.05)
    ))
    
    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, -2), Vec3(1, 0.95, 0.9), 1.0))
    scene.add_light(PointLight(Vec3(5, 5, 0), Vec3(0.6, 0.7, 1.0), 0.6))
    
    return scene


# ═══════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════

if __name__ == '__main__':
    print("═" * 50)
    print("  RAYTRACER — Photorealistic Rendering from Scratch")
    print("  Phong Shading • Shadows • Reflections • AA")
    print("═" * 50)
    
    scene = build_demo_scene()
    
    # Camera
    cam = Camera(
        position=Vec3(0, 2, 3),
        look_at=Vec3(0, 0.5, -3),
        fov=60,
        aspect=16/9
    )
    
    # Render at moderate resolution
    width, height = 320, 180
    if len(sys.argv) > 1 and sys.argv[1] == '--hires':
        width, height = 640, 360
    
    filename = render(scene, cam, width, height, "/workspace/raytracer/render.ppm")
    
    # Verify the image
    import os
    size = os.path.getsize(filename)
    print(f"\n  Image size: {size:,} bytes")
    print(f"  Pixels: {width * height:,}")
    
    # Quick stats: sample some pixel values
    with open(filename) as f:
        header = f.readline().strip()  # P3
        dims = f.readline().strip()    # W H
        maxval = f.readline().strip()  # 255
    
    print(f"  Format: {header}, Dimensions: {dims}, Max: {maxval}")
    
    # Count unique colors as a quality metric
    with open(filename) as f:
        lines = f.readlines()[3:]  # skip header
        unique_colors = len(set(lines))
    
    print(f"  Unique colors: {unique_colors:,}")
    
    if unique_colors > 100:
        print("\n  ✓ Rich color palette — scene rendered successfully!")
    
    print("\n" + "═" * 50)
    print("  ═══ RENDER COMPLETE ═══")
    print("═" * 50)