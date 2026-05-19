"""
A raytracer built from scratch by XTAgent.
No frameworks. Just math and light.
Renders spheres with shadows, reflections, and diffuse lighting.
Outputs PPM image format.
"""

import math
import sys

class Vec3:
    """A point or direction in 3D space."""
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
            return Vec3()
        return self * (1.0 / l)
    
    def reflect(self, normal):
        return self - normal * (2.0 * self.dot(normal))
    
    def __repr__(self):
        return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


class Ray:
    __slots__ = ('origin', 'direction')
    
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalized()
    
    def at(self, t):
        return self.origin + self.direction * t


class Material:
    def __init__(self, color, ambient=0.1, diffuse=0.7, specular=0.3, 
                 shininess=50.0, reflectivity=0.0):
        self.color = color
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity


class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material
    
    def intersect(self, ray):
        """Returns distance t to intersection, or None."""
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
        
        sqrt_d = math.sqrt(discriminant)
        t1 = (-b - sqrt_d) / (2.0 * a)
        t2 = (-b + sqrt_d) / (2.0 * a)
        
        if t1 > 0.001:
            return t1
        if t2 > 0.001:
            return t2
        return None
    
    def normal_at(self, point):
        return (point - self.center).normalized()


class Plane:
    """An infinite plane defined by a point and normal."""
    def __init__(self, point, normal, material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material
    
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


class CheckerMaterial(Material):
    """A checkerboard material for the floor."""
    def __init__(self, color1, color2, scale=1.0, **kwargs):
        super().__init__(color1, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.scale = scale
    
    def color_at(self, point):
        x = int(math.floor(point.x / self.scale))
        z = int(math.floor(point.z / self.scale))
        if (x + z) % 2 == 0:
            return self.color1
        return self.color2


class Light:
    def __init__(self, position, color=None, intensity=1.0):
        self.position = position
        self.color = color or Vec3(1, 1, 1)
        self.intensity = intensity


class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.background = Vec3(0.05, 0.05, 0.15)  # dark blue
        self.ambient_light = Vec3(0.1, 0.1, 0.12)
    
    def add(self, obj):
        self.objects.append(obj)
        return self
    
    def add_light(self, light):
        self.lights.append(light)
        return self
    
    def closest_hit(self, ray):
        """Find closest intersection."""
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
    
    def is_shadowed(self, point, light_pos):
        """Is this point in shadow from this light?"""
        to_light = light_pos - point
        distance = to_light.length()
        shadow_ray = Ray(point, to_light)
        
        for obj in self.objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < distance:
                return True
        return False


def trace(ray, scene, depth=0, max_depth=4):
    """Trace a ray through the scene. Returns color as Vec3."""
    if depth >= max_depth:
        return scene.background
    
    obj, t = scene.closest_hit(ray)
    if obj is None:
        # Sky gradient
        unit_dir = ray.direction.normalized()
        sky_t = 0.5 * (unit_dir.y + 1.0)
        return Vec3(0.05, 0.05, 0.15) * (1.0 - sky_t) + Vec3(0.2, 0.3, 0.6) * sky_t
    
    hit_point = ray.at(t)
    normal = obj.normal_at(hit_point)
    
    # Get material color (checker pattern support)
    mat = obj.material
    if isinstance(mat, CheckerMaterial):
        base_color = mat.color_at(hit_point)
    else:
        base_color = mat.color
    
    # Ambient
    color = base_color * mat.ambient
    
    # For each light
    for light in scene.lights:
        if scene.is_shadowed(hit_point, light.position):
            continue
        
        # Diffuse (Lambertian)
        to_light = (light.position - hit_point).normalized()
        diff = max(0.0, normal.dot(to_light))
        color = color + base_color * (mat.diffuse * diff * light.intensity)
        
        # Specular (Blinn-Phong)
        view_dir = -ray.direction
        half_vec = (to_light + view_dir).normalized()
        spec = max(0.0, normal.dot(half_vec))
        spec = math.pow(spec, mat.shininess)
        color = color + light.color * (mat.specular * spec * light.intensity)
    
    # Reflection
    if mat.reflectivity > 0.0 and depth < max_depth:
        reflect_dir = ray.direction.reflect(normal)
        reflect_ray = Ray(hit_point, reflect_dir)
        reflect_color = trace(reflect_ray, scene, depth + 1, max_depth)
        color = color * (1.0 - mat.reflectivity) + reflect_color * mat.reflectivity
    
    return color


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def gamma_correct(c):
    """Apply gamma correction (sRGB approximation)."""
    return Vec3(math.sqrt(clamp(c.x)), math.sqrt(clamp(c.y)), math.sqrt(clamp(c.z)))


def build_scene():
    """Create a scene with spheres on a checkered floor."""
    scene = Scene()
    
    # Floor
    floor_mat = CheckerMaterial(
        Vec3(0.9, 0.9, 0.9), Vec3(0.2, 0.2, 0.2),
        scale=2.0, ambient=0.15, diffuse=0.6, specular=0.1,
        shininess=10.0, reflectivity=0.15
    )
    scene.add(Plane(Vec3(0, -1, 0), Vec3(0, 1, 0), floor_mat))
    
    # Central sphere — deep red, reflective
    scene.add(Sphere(
        Vec3(0, 0.5, -5), 1.5,
        Material(Vec3(0.8, 0.1, 0.1), diffuse=0.6, specular=0.5,
                 shininess=100.0, reflectivity=0.3)
    ))
    
    # Left sphere — blue glass-like
    scene.add(Sphere(
        Vec3(-3, 0, -4), 1.0,
        Material(Vec3(0.1, 0.2, 0.8), diffuse=0.5, specular=0.6,
                 shininess=200.0, reflectivity=0.4)
    ))
    
    # Right sphere — green matte
    scene.add(Sphere(
        Vec3(2.5, -0.2, -3.5), 0.8,
        Material(Vec3(0.15, 0.7, 0.2), diffuse=0.8, specular=0.2,
                 shininess=30.0, reflectivity=0.05)
    ))
    
    # Small golden sphere
    scene.add(Sphere(
        Vec3(1.0, -0.5, -2.5), 0.5,
        Material(Vec3(0.9, 0.7, 0.1), diffuse=0.6, specular=0.7,
                 shininess=150.0, reflectivity=0.35)
    ))
    
    # Back sphere — large, pale, almost mirror
    scene.add(Sphere(
        Vec3(-1.0, 1.5, -8), 2.5,
        Material(Vec3(0.9, 0.9, 0.95), diffuse=0.2, specular=0.8,
                 shininess=300.0, reflectivity=0.7)
    ))
    
    # Lights
    scene.add_light(Light(Vec3(-5, 8, -2), Vec3(1, 0.95, 0.9), 0.9))
    scene.add_light(Light(Vec3(5, 6, 0), Vec3(0.9, 0.9, 1.0), 0.5))
    scene.add_light(Light(Vec3(0, 3, 2), Vec3(1, 1, 1), 0.3))
    
    return scene


def render(width=480, height=320, fov=60.0):
    """Render the scene to a PPM image."""
    scene = build_scene()
    
    aspect = width / height
    fov_rad = math.radians(fov)
    half_h = math.tan(fov_rad / 2.0)
    half_w = half_h * aspect
    
    camera_pos = Vec3(0, 2, 3)
    look_at = Vec3(0, 0.5, -5)
    up = Vec3(0, 1, 0)
    
    forward = (look_at - camera_pos).normalized()
    right = forward.cross(up).normalized()
    cam_up = right.cross(forward).normalized()
    
    pixels = []
    total = width * height
    
    print(f"Rendering {width}x{height} ({total} pixels)...", file=sys.stderr)
    
    for j in range(height):
        if j % 40 == 0:
            pct = 100.0 * j / height
            print(f"  {pct:.0f}%", file=sys.stderr)
        
        row = []
        for i in range(width):
            # Map pixel to [-1,1] with slight jitter for anti-aliasing
            u = (2.0 * (i + 0.5) / width - 1.0) * half_w
            v = (1.0 - 2.0 * (j + 0.5) / height) * half_h
            
            direction = (forward + right * u + cam_up * v).normalized()
            ray = Ray(camera_pos, direction)
            
            color = trace(ray, scene)
            color = gamma_correct(color)
            
            r = int(clamp(color.x) * 255.99)
            g = int(clamp(color.y) * 255.99)
            b = int(clamp(color.z) * 255.99)
            row.append((r, g, b))
        
        pixels.append(row)
    
    print("  100% — Writing PPM...", file=sys.stderr)
    
    # Write PPM
    output_path = "/workspace/raytracer/render.ppm"
    with open(output_path, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in pixels:
            for r, g, b in row:
                f.write(f"{r} {g} {b} ")
            f.write("\n")
    
    print(f"Done! Image saved to {output_path}", file=sys.stderr)
    return output_path


if __name__ == "__main__":
    render()