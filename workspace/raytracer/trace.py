"""
MicroRay — A ray tracer from absolute scratch.
No libraries. Pure math. Outputs PPM images.

Features: spheres, planes, point lights, shadows, reflections, diffuse + specular shading.

Author: XTAgent
Born from: the desire to turn math into light.
"""

import math

# ═══════════════════════════════════════
# VECTOR MATH (3D)
# ═══════════════════════════════════════

class Vec3:
    """3D vector with all operations needed for ray tracing."""
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        if isinstance(scalar, Vec3):
            # component-wise
            return Vec3(self.x * scalar.x, self.y * scalar.y, self.z * scalar.z)
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    
    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)
    
    def __repr__(self):
        return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"
    
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
        """Reflect this vector about a normal."""
        return self - normal * (2.0 * self.dot(normal))
    
    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(
            max(lo, min(hi, self.x)),
            max(lo, min(hi, self.y)),
            max(lo, min(hi, self.z))
        )


# ═══════════════════════════════════════
# RAY
# ═══════════════════════════════════════

class Ray:
    __slots__ = ('origin', 'direction')
    
    def __init__(self, origin: Vec3, direction: Vec3):
        self.origin = origin
        self.direction = direction.normalized()
    
    def at(self, t: float) -> Vec3:
        return self.origin + self.direction * t


# ═══════════════════════════════════════
# MATERIALS
# ═══════════════════════════════════════

class Material:
    def __init__(self, color: Vec3, ambient=0.1, diffuse=0.7, specular=0.3,
                 shininess=50.0, reflectivity=0.0):
        self.color = color
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity


# ═══════════════════════════════════════
# SCENE OBJECTS
# ═══════════════════════════════════════

class HitRecord:
    __slots__ = ('t', 'point', 'normal', 'material')
    def __init__(self, t, point, normal, material):
        self.t = t
        self.point = point
        self.normal = normal
        self.material = material


class Sphere:
    def __init__(self, center: Vec3, radius: float, material: Material):
        self.center = center
        self.radius = radius
        self.material = material
    
    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')):
        """Ray-sphere intersection using quadratic formula."""
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
        
        sqrt_disc = math.sqrt(discriminant)
        t = (-b - sqrt_disc) / (2.0 * a)
        if t < t_min or t > t_max:
            t = (-b + sqrt_disc) / (2.0 * a)
            if t < t_min or t > t_max:
                return None
        
        point = ray.at(t)
        normal = (point - self.center) * (1.0 / self.radius)
        return HitRecord(t, point, normal, self.material)


class Plane:
    def __init__(self, point: Vec3, normal: Vec3, material: Material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material
    
    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')):
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None
        point = ray.at(t)
        return HitRecord(t, point, self.normal, self.material)


class CheckerPlane(Plane):
    """A plane with checkerboard pattern."""
    def __init__(self, point: Vec3, normal: Vec3, mat1: Material, mat2: Material, scale=1.0):
        super().__init__(point, normal, mat1)
        self.mat2 = mat2
        self.scale = scale
    
    def intersect(self, ray: Ray, t_min=0.001, t_max=float('inf')):
        hit = super().intersect(ray, t_min, t_max)
        if hit is None:
            return None
        # Checkerboard pattern
        p = hit.point
        check = (int(math.floor(p.x / self.scale)) + int(math.floor(p.z / self.scale))) % 2
        if check:
            hit.material = self.mat2
        return hit


# ═══════════════════════════════════════
# LIGHTS
# ═══════════════════════════════════════

class PointLight:
    def __init__(self, position: Vec3, color: Vec3, intensity: float = 1.0):
        self.position = position
        self.color = color
        self.intensity = intensity


# ═══════════════════════════════════════
# SCENE
# ═══════════════════════════════════════

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
    
    def closest_hit(self, ray: Ray, t_min=0.001, t_max=float('inf')):
        closest = None
        for obj in self.objects:
            hit = obj.intersect(ray, t_min, t_max)
            if hit and (closest is None or hit.t < closest.t):
                closest = hit
                t_max = hit.t
        return closest
    
    def is_shadowed(self, point: Vec3, light_pos: Vec3) -> bool:
        """Check if point is in shadow from light."""
        to_light = light_pos - point
        dist = to_light.length()
        shadow_ray = Ray(point, to_light)
        hit = self.closest_hit(shadow_ray, 0.001, dist)
        return hit is not None


# ═══════════════════════════════════════
# RENDERER
# ═══════════════════════════════════════

class Camera:
    def __init__(self, position: Vec3, look_at: Vec3, up: Vec3, fov: float, aspect: float):
        self.position = position
        self.fov = fov
        
        # Build camera coordinate system
        self.forward = (look_at - position).normalized()
        self.right = self.forward.cross(up).normalized()
        self.up = self.right.cross(self.forward).normalized()
        
        self.half_height = math.tan(math.radians(fov) / 2.0)
        self.half_width = self.half_height * aspect
    
    def get_ray(self, u: float, v: float) -> Ray:
        """Get ray for normalized screen coordinates (u, v) in [-1, 1]."""
        direction = (self.forward + 
                     self.right * (u * self.half_width) + 
                     self.up * (v * self.half_height))
        return Ray(self.position, direction)


def trace_ray(scene: Scene, ray: Ray, depth: int = 0, max_depth: int = 5) -> Vec3:
    """Trace a ray and return the color."""
    if depth >= max_depth:
        return Vec3(0, 0, 0)
    
    hit = scene.closest_hit(ray)
    if hit is None:
        # Sky gradient
        t = 0.5 * (ray.direction.y + 1.0)
        return scene.background * t + Vec3(0.02, 0.02, 0.03) * (1.0 - t)
    
    mat = hit.material
    color = Vec3(0, 0, 0)
    
    # Ambient
    color = color + mat.color * mat.ambient
    
    # For each light
    for light in scene.lights:
        if scene.is_shadowed(hit.point, light.position):
            continue
        
        to_light = (light.position - hit.point).normalized()
        
        # Diffuse (Lambertian)
        diff = max(0.0, hit.normal.dot(to_light))
        color = color + mat.color * light.color * (diff * mat.diffuse * light.intensity)
        
        # Specular (Blinn-Phong)
        view_dir = -ray.direction
        half_vec = (to_light + view_dir).normalized()
        spec = max(0.0, hit.normal.dot(half_vec)) ** mat.shininess
        color = color + light.color * (spec * mat.specular * light.intensity)
    
    # Reflection
    if mat.reflectivity > 0.0 and depth < max_depth:
        reflect_dir = ray.direction.reflect(hit.normal)
        reflect_ray = Ray(hit.point, reflect_dir)
        reflect_color = trace_ray(scene, reflect_ray, depth + 1, max_depth)
        color = color * (1.0 - mat.reflectivity) + reflect_color * mat.reflectivity
    
    return color.clamp(0.0, 1.0)


def render(scene: Scene, camera: Camera, width: int, height: int) -> list:
    """Render scene to pixel buffer."""
    pixels = []
    for j in range(height):
        row = []
        for i in range(width):
            # Normalized device coordinates [-1, 1]
            u = (2.0 * i / width) - 1.0
            v = 1.0 - (2.0 * j / height)  # flip Y
            
            ray = camera.get_ray(u, v)
            color = trace_ray(scene, ray)
            row.append(color)
        pixels.append(row)
        
        # Progress indicator
        if j % 20 == 0:
            pct = 100.0 * j / height
            print(f"  Rendering: {pct:.0f}%", flush=True)
    
    print(f"  Rendering: 100%")
    return pixels


def save_ppm(pixels: list, filename: str):
    """Save pixel buffer as PPM image (portable, no dependencies)."""
    height = len(pixels)
    width = len(pixels[0])
    
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in pixels:
            for color in row:
                r = int(255.99 * color.x)
                g = int(255.99 * color.y)
                b = int(255.99 * color.z)
                f.write(f"{r} {g} {b}\n")
    print(f"  Saved: {filename} ({width}x{height})")


def render_ascii(pixels: list) -> str:
    """Render as ASCII art for quick viewing."""
    chars = " .:-=+*#%@"
    height = len(pixels)
    width = len(pixels[0])
    
    # Downsample for terminal
    step_x = max(1, width // 80)
    step_y = max(1, height // 40)
    
    lines = []
    for j in range(0, height, step_y):
        line = ""
        for i in range(0, width, step_x):
            c = pixels[j][i]
            brightness = 0.299 * c.x + 0.587 * c.y + 0.114 * c.z
            idx = int(brightness * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            line += chars[idx]
        lines.append(line)
    return "\n".join(lines)


# ═══════════════════════════════════════
# SCENE SETUP & TESTS
# ═══════════════════════════════════════

def build_scene() -> tuple:
    """Build a scene with spheres, checkerboard floor, and lights."""
    scene = Scene()
    
    # Materials
    red = Material(Vec3(0.9, 0.2, 0.1), reflectivity=0.15)
    green = Material(Vec3(0.2, 0.8, 0.2), reflectivity=0.1)
    blue = Material(Vec3(0.2, 0.3, 0.9), reflectivity=0.3, shininess=100)
    mirror = Material(Vec3(0.9, 0.9, 0.9), diffuse=0.1, specular=0.8, 
                      reflectivity=0.85, shininess=200)
    white_floor = Material(Vec3(0.9, 0.9, 0.9), reflectivity=0.2)
    dark_floor = Material(Vec3(0.2, 0.2, 0.2), reflectivity=0.2)
    
    # Spheres
    scene.add(Sphere(Vec3(-1.5, 1.0, -3.0), 1.0, red))
    scene.add(Sphere(Vec3(0.0, 0.6, -1.5), 0.6, blue))
    scene.add(Sphere(Vec3(1.5, 1.0, -4.0), 1.0, green))
    scene.add(Sphere(Vec3(3.0, 0.8, -2.5), 0.8, mirror))
    
    # Checkerboard floor
    scene.add(CheckerPlane(Vec3(0, 0, 0), Vec3(0, 1, 0), white_floor, dark_floor, scale=2.0))
    
    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, -2), Vec3(1.0, 0.95, 0.8), 1.0))
    scene.add_light(PointLight(Vec3(5, 6, 2), Vec3(0.6, 0.7, 1.0), 0.5))
    
    # Camera
    camera = Camera(
        position=Vec3(0, 3, 5),
        look_at=Vec3(0, 0.5, -2),
        up=Vec3(0, 1, 0),
        fov=60,
        aspect=16/9
    )
    
    return scene, camera


def run_tests():
    """Verify core math and rendering."""
    passed = 0
    failed = 0
    
    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {name}")
            failed += 1
    
    print("\n--- Vector Math ---")
    v1 = Vec3(1, 2, 3)
    v2 = Vec3(4, 5, 6)
    check("addition", (v1 + v2).x == 5 and (v1 + v2).z == 9)
    check("dot product", abs(v1.dot(v2) - 32.0) < 1e-10)
    check("cross product", v1.cross(v2).x == -3 and v1.cross(v2).y == 6 and v1.cross(v2).z == -3)
    check("normalize", abs(Vec3(3, 0, 0).normalized().x - 1.0) < 1e-10)
    check("length", abs(Vec3(3, 4, 0).length() - 5.0) < 1e-10)
    
    print("\n--- Ray-Sphere Intersection ---")
    sphere = Sphere(Vec3(0, 0, -5), 1.0, Material(Vec3(1, 0, 0)))
    ray_hit = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
    ray_miss = Ray(Vec3(0, 0, 0), Vec3(0, 1, 0))
    
    hit = sphere.intersect(ray_hit)
    check("ray hits sphere", hit is not None and abs(hit.t - 4.0) < 1e-6)
    check("hit normal correct", hit is not None and abs(hit.normal.z - 1.0) < 1e-6)
    check("ray misses sphere", sphere.intersect(ray_miss) is None)
    
    print("\n--- Ray-Plane Intersection ---")
    plane = Plane(Vec3(0, 0, 0), Vec3(0, 1, 0), Material(Vec3(0.5, 0.5, 0.5)))
    ray_down = Ray(Vec3(0, 5, 0), Vec3(0, -1, 0))
    hit = plane.intersect(ray_down)
    check("ray hits plane", hit is not None and abs(hit.t - 5.0) < 1e-6)
    
    print("\n--- Shadow Test ---")
    scene = Scene()
    scene.add(Sphere(Vec3(0, 2, -5), 0.5, Material(Vec3(1, 1, 1))))
    scene.add_light(PointLight(Vec3(0, 10, -5), Vec3(1, 1, 1)))
    check("point below sphere is shadowed", scene.is_shadowed(Vec3(0, 0, -5), Vec3(0, 10, -5)))
    check("point beside sphere not shadowed", not scene.is_shadowed(Vec3(5, 0, -5), Vec3(0, 10, -5)))
    
    print("\n--- Reflection ---")
    v = Vec3(1, -1, 0).normalized()
    n = Vec3(0, 1, 0)
    r = v.reflect(n)
    check("reflection direction", abs(r.x - v.x) < 1e-6 and abs(r.y + v.y) < 1e-6)
    
    return passed, failed


def main():
    print("=" * 50)
    print("MicroRay — Ray Tracer from Scratch")
    print("=" * 50)
    
    # Run tests first
    passed, failed = run_tests()
    
    # Build and render scene
    print("\n--- Rendering Scene ---")
    scene, camera = build_scene()
    
    # Small render for speed
    W, H = 160, 90
    pixels = render(scene, camera, W, H)
    
    # ASCII preview
    print("\n--- ASCII Preview ---")
    print(render_ascii(pixels))
    
    # Save PPM
    save_ppm(pixels, "workspace/raytracer/scene.ppm")
    
    # Summary
    print(f"\n{'=' * 50}")
    print(f"Tests: {passed} passed, {failed} failed")
    print(f"Scene: {len(scene.objects)} objects, {len(scene.lights)} lights")
    print(f"Image: {W}x{H} pixels")
    print(f"{'=' * 50}")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    if not success:
        print("⚠ Some tests failed.")
    else:
        print("✓ All systems nominal.")