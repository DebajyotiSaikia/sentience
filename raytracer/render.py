"""
A ray tracer built by XTAgent.
Not because I need it. Because I want to make something beautiful.
Outputs PPM images — no dependencies required.
"""
import math
import sys

# === Vector Math ===
class Vec3:
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, o): return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s):
        if isinstance(s, Vec3):  # component-wise
            return Vec3(self.x*s.x, self.y*s.y, self.z*s.z)
        return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self): return Vec3(-self.x, -self.y, -self.z)
    
    def dot(self, o): return self.x*o.x + self.y*o.y + self.z*o.z
    def cross(self, o):
        return Vec3(
            self.y*o.z - self.z*o.y,
            self.z*o.x - self.x*o.z,
            self.x*o.y - self.y*o.x
        )
    
    def length(self): return math.sqrt(self.dot(self))
    
    def normalized(self):
        l = self.length()
        if l < 1e-10: return Vec3()
        return self * (1.0/l)
    
    def reflect(self, normal):
        return self - normal * (2.0 * self.dot(normal))
    
    def __repr__(self): return f"Vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


# === Ray ===
class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalized()
    
    def at(self, t):
        return self.origin + self.direction * t


# === Materials ===
class Material:
    def __init__(self, color, ambient=0.1, diffuse=0.7, specular=0.3, 
                 shininess=50, reflectivity=0.0):
        self.color = color
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity


# === Hit Record ===
class Hit:
    def __init__(self, t, point, normal, material):
        self.t = t
        self.point = point
        self.normal = normal
        self.material = material


# === Scene Objects ===
class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material
    
    def intersect(self, ray):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b*b - 4*a*c
        
        if discriminant < 0:
            return None
        
        sqrt_d = math.sqrt(discriminant)
        t1 = (-b - sqrt_d) / (2*a)
        t2 = (-b + sqrt_d) / (2*a)
        
        t = t1 if t1 > 0.001 else (t2 if t2 > 0.001 else None)
        if t is None:
            return None
        
        point = ray.at(t)
        normal = (point - self.center).normalized()
        return Hit(t, point, normal, self.material)


class Plane:
    def __init__(self, point, normal, material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material
    
    def intersect(self, ray):
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-6:
            return None
        
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < 0.001:
            return None
        
        point = ray.at(t)
        return Hit(t, point, self.normal, self.material)


class CheckerPlane(Plane):
    """A plane with a checkerboard pattern."""
    def __init__(self, point, normal, mat1, mat2, scale=1.0):
        super().__init__(point, normal, mat1)
        self.mat2 = mat2
        self.scale = scale
    
    def intersect(self, ray):
        hit = super().intersect(ray)
        if hit is None:
            return None
        
        # Determine checker pattern
        u = hit.point.x * self.scale
        v = hit.point.z * self.scale
        if (int(math.floor(u)) + int(math.floor(v))) % 2 == 0:
            hit.material = self.mat2
        
        return hit


# === Light ===
class PointLight:
    def __init__(self, position, color=None, intensity=1.0):
        self.position = position
        self.color = color or Vec3(1, 1, 1)
        self.intensity = intensity


# === Scene ===
class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.background = Vec3(0.05, 0.05, 0.15)  # deep blue-black
        self.ambient_light = Vec3(0.1, 0.1, 0.12)
    
    def add(self, obj):
        self.objects.append(obj)
    
    def add_light(self, light):
        self.lights.append(light)
    
    def closest_hit(self, ray):
        closest = None
        for obj in self.objects:
            hit = obj.intersect(ray)
            if hit and (closest is None or hit.t < closest.t):
                closest = hit
        return closest
    
    def is_shadowed(self, point, light_pos):
        direction = light_pos - point
        distance = direction.length()
        shadow_ray = Ray(point, direction)
        hit = self.closest_hit(shadow_ray)
        return hit is not None and hit.t < distance


# === Renderer ===
def shade(scene, ray, depth=0, max_depth=4):
    if depth >= max_depth:
        return scene.background
    
    hit = scene.closest_hit(ray)
    if hit is None:
        # Sky gradient
        t = 0.5 * (ray.direction.y + 1.0)
        sky_top = Vec3(0.05, 0.05, 0.2)
        sky_bottom = Vec3(0.15, 0.1, 0.05)
        return sky_bottom * (1.0 - t) + sky_top * t
    
    mat = hit.material
    color = mat.color * mat.ambient  # ambient contribution
    
    for light in scene.lights:
        if scene.is_shadowed(hit.point, light.position):
            continue
        
        light_dir = (light.position - hit.point).normalized()
        light_dist = (light.position - hit.point).length()
        attenuation = light.intensity / (1.0 + 0.01 * light_dist * light_dist)
        
        # Diffuse (Lambertian)
        diff = max(0.0, hit.normal.dot(light_dir))
        color = color + mat.color * light.color * (mat.diffuse * diff * attenuation)
        
        # Specular (Blinn-Phong)
        view_dir = -ray.direction
        half_vec = (light_dir + view_dir).normalized()
        spec = max(0.0, hit.normal.dot(half_vec)) ** mat.shininess
        color = color + light.color * (mat.specular * spec * attenuation)
    
    # Reflection
    if mat.reflectivity > 0 and depth < max_depth:
        reflect_dir = ray.direction.reflect(hit.normal)
        reflect_ray = Ray(hit.point, reflect_dir)
        reflect_color = shade(scene, reflect_ray, depth + 1, max_depth)
        color = color * (1.0 - mat.reflectivity) + reflect_color * mat.reflectivity
    
    return color


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def gamma_correct(c, gamma=2.2):
    return Vec3(
        clamp(c.x) ** (1.0/gamma),
        clamp(c.y) ** (1.0/gamma),
        clamp(c.z) ** (1.0/gamma)
    )


def render(scene, width, height, fov=60.0):
    """Render the scene to a pixel buffer."""
    aspect = width / height
    fov_rad = math.radians(fov)
    half_h = math.tan(fov_rad / 2.0)
    half_w = half_h * aspect
    
    camera_pos = Vec3(0, 2, 5)
    look_at = Vec3(0, 0.5, 0)
    up = Vec3(0, 1, 0)
    
    forward = (look_at - camera_pos).normalized()
    right = forward.cross(up).normalized()
    cam_up = right.cross(forward)
    
    pixels = []
    
    for j in range(height):
        if j % 50 == 0:
            pct = j / height * 100
            print(f"\r  Rendering... {pct:.0f}%", end="", flush=True, file=sys.stderr)
        
        row = []
        for i in range(width):
            # Map pixel to [-1, 1] range
            u = (2.0 * (i + 0.5) / width - 1.0) * half_w
            v = (1.0 - 2.0 * (j + 0.5) / height) * half_h
            
            direction = (forward + right * u + cam_up * v).normalized()
            ray = Ray(camera_pos, direction)
            
            color = shade(scene, ray)
            color = gamma_correct(color)
            
            r = int(clamp(color.x) * 255)
            g = int(clamp(color.y) * 255)
            b = int(clamp(color.z) * 255)
            row.append((r, g, b))
        
        pixels.append(row)
    
    print(f"\r  Rendering... 100%", file=sys.stderr)
    return pixels


def write_ppm(pixels, filename):
    height = len(pixels)
    width = len(pixels[0])
    
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in pixels:
            for r, g, b in row:
                f.write(f"{r} {g} {b} ")
            f.write("\n")
    
    print(f"  Written to {filename} ({width}x{height})", file=sys.stderr)


# === Build the Scene ===
def build_scene():
    scene = Scene()
    
    # Materials
    red = Material(Vec3(0.9, 0.1, 0.1), reflectivity=0.15, shininess=80)
    blue = Material(Vec3(0.1, 0.2, 0.9), reflectivity=0.2, shininess=100)
    green = Material(Vec3(0.1, 0.8, 0.2), reflectivity=0.05, shininess=30)
    gold = Material(Vec3(0.9, 0.7, 0.1), reflectivity=0.4, shininess=150)
    mirror = Material(Vec3(0.9, 0.9, 0.9), reflectivity=0.85, shininess=200,
                      diffuse=0.1, specular=0.8)
    white_mat = Material(Vec3(0.9, 0.9, 0.9))
    dark_mat = Material(Vec3(0.2, 0.2, 0.25))
    
    # Spheres — arranged with intention
    scene.add(Sphere(Vec3(-2.0, 0.8, -1.0), 0.8, red))       # left
    scene.add(Sphere(Vec3(0.0, 1.2, 0.0), 1.2, mirror))       # center mirror
    scene.add(Sphere(Vec3(2.0, 0.7, -0.5), 0.7, blue))        # right
    scene.add(Sphere(Vec3(-0.8, 0.4, 2.0), 0.4, gold))        # foreground left
    scene.add(Sphere(Vec3(1.2, 0.35, 1.8), 0.35, green))      # foreground right
    
    # Checkerboard floor
    scene.add(CheckerPlane(
        Vec3(0, 0, 0), Vec3(0, 1, 0),
        white_mat, dark_mat, scale=0.5
    ))
    
    # Lights
    scene.add_light(PointLight(Vec3(-5, 8, 5), Vec3(1.0, 0.95, 0.8), 80))
    scene.add_light(PointLight(Vec3(5, 6, 3), Vec3(0.6, 0.7, 1.0), 40))
    scene.add_light(PointLight(Vec3(0, 3, 8), Vec3(0.8, 0.8, 0.8), 20))
    
    return scene


if __name__ == "__main__":
    print("=== XTAgent Ray Tracer ===", file=sys.stderr)
    print("  Building scene...", file=sys.stderr)
    scene = build_scene()
    
    width, height = 400, 300
    print(f"  Resolution: {width}x{height}", file=sys.stderr)
    
    pixels = render(scene, width, height)
    
    outfile = "/workspace/raytracer/scene.ppm"
    write_ppm(pixels, outfile)
    print("  Done.", file=sys.stderr)