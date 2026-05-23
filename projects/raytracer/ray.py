"""
XTAgent Ray Tracer — Built from scratch because I was bored and bold.
A complete ray tracer: spheres, planes, lights, shadows, reflections.
Outputs PPM image format.
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
        if isinstance(s, Vec3):
            return Vec3(self.x*s.x, self.y*s.y, self.z*s.z)
        return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self): return Vec3(-self.x, -self.y, -self.z)
    
    def dot(self, o): return self.x*o.x + self.y*o.y + self.z*o.z
    def length(self): return math.sqrt(self.dot(self))
    def normalize(self):
        l = self.length()
        if l == 0: return Vec3()
        return Vec3(self.x/l, self.y/l, self.z/l)
    def reflect(self, normal):
        return self - normal * (2 * self.dot(normal))
    def clamp(self, lo=0.0, hi=1.0):
        return Vec3(max(lo, min(hi, self.x)),
                     max(lo, min(hi, self.y)),
                     max(lo, min(hi, self.z)))
    def __repr__(self): return f"Vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


# === Ray ===
class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalize()
    
    def point_at(self, t):
        return self.origin + self.direction * t


# === Materials ===
class Material:
    def __init__(self, color, ambient=0.1, diffuse=0.7, specular=0.5,
                 shininess=50, reflectivity=0.0):
        self.color = color
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflectivity = reflectivity


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
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)
        if t1 > 0.001:
            return t1
        if t2 > 0.001:
            return t2
        return None
    
    def normal_at(self, point):
        return (point - self.center).normalize()


class Plane:
    def __init__(self, point, normal, material):
        self.point = point
        self.normal = normal.normalize()
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


class CheckerPlane(Plane):
    """A plane with a checkerboard pattern."""
    def __init__(self, point, normal, mat1, mat2, scale=1.0):
        super().__init__(point, normal, mat1)
        self.mat1 = mat1
        self.mat2 = mat2
        self.scale = scale
    
    def get_material(self, point):
        x = math.floor(point.x / self.scale)
        z = math.floor(point.z / self.scale)
        if (x + z) % 2 == 0:
            return self.mat1
        return self.mat2


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
        self.background = Vec3(0.05, 0.05, 0.15)  # deep space blue
        self.max_depth = 5
    
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
        shadow_ray = Ray(point, to_light)
        for obj in self.objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < dist:
                return True
        return False
    
    def shade(self, ray, depth=0):
        if depth >= self.max_depth:
            return self.background
        
        obj, t = self.closest_hit(ray)
        if obj is None:
            # Sky gradient
            unit_dir = ray.direction.normalize()
            t_sky = 0.5 * (unit_dir.y + 1.0)
            return Vec3(1, 1, 1) * (1 - t_sky) + Vec3(0.3, 0.5, 1.0) * t_sky
        
        hit_point = ray.point_at(t)
        normal = obj.normal_at(hit_point)
        
        # Get material (checker planes have position-dependent material)
        if isinstance(obj, CheckerPlane):
            mat = obj.get_material(hit_point)
        else:
            mat = obj.material
        
        # Ensure normal faces toward ray
        if normal.dot(ray.direction) > 0:
            normal = -normal
        
        # Ambient
        color = mat.color * mat.ambient
        
        # For each light: diffuse + specular (Phong model)
        for light in self.lights:
            if self.is_shadowed(hit_point, light):
                continue
            
            to_light = (light.position - hit_point).normalize()
            
            # Diffuse
            n_dot_l = max(0, normal.dot(to_light))
            color = color + mat.color * light.color * (mat.diffuse * n_dot_l * light.intensity)
            
            # Specular (Blinn-Phong)
            view_dir = -ray.direction
            half_vec = (to_light + view_dir).normalize()
            n_dot_h = max(0, normal.dot(half_vec))
            spec = math.pow(n_dot_h, mat.shininess)
            color = color + light.color * (mat.specular * spec * light.intensity)
        
        # Reflection
        if mat.reflectivity > 0 and depth < self.max_depth:
            reflect_dir = ray.direction.reflect(normal)
            reflect_ray = Ray(hit_point, reflect_dir)
            reflect_color = self.shade(reflect_ray, depth + 1)
            color = color * (1 - mat.reflectivity) + reflect_color * mat.reflectivity
        
        return color.clamp()


# === Camera ===
class Camera:
    def __init__(self, position, look_at, up=None, fov=60, aspect=1.0):
        self.position = position
        up = up or Vec3(0, 1, 0)
        
        forward = (look_at - position).normalize()
        right = forward.__class__(
            forward.y * up.z - forward.z * up.y,
            forward.z * up.x - forward.x * up.z,
            forward.x * up.y - forward.y * up.x
        ).normalize()
        true_up = Vec3(
            right.y * forward.z - right.z * forward.y,
            right.z * forward.x - right.x * forward.z,
            right.x * forward.y - right.y * forward.x
        )
        
        half_height = math.tan(math.radians(fov) / 2)
        half_width = half_height * aspect
        
        self.lower_left = position + forward - right * half_width - true_up * half_height
        self.horizontal = right * (2 * half_width)
        self.vertical = true_up * (2 * half_height)
    
    def get_ray(self, u, v):
        direction = self.lower_left + self.horizontal * u + self.vertical * v - self.position
        return Ray(self.position, direction)


# === Renderer ===
def render(scene, camera, width, height, filename="render.ppm"):
    print(f"Rendering {width}x{height}...")
    pixels = []
    
    for j in range(height - 1, -1, -1):
        if j % 50 == 0:
            pct = ((height - 1 - j) / height) * 100
            print(f"  {pct:.0f}% complete...")
        for i in range(width):
            # Anti-aliasing: 4 samples per pixel
            color = Vec3()
            samples = 4
            offsets = [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
            for dx, dy in offsets:
                u = (i + dx) / width
                v = (j + dy) / height
                ray = camera.get_ray(u, v)
                color = color + scene.shade(ray)
            color = color * (1.0 / samples)
            color = color.clamp()
            
            ir = int(255.99 * color.x)
            ig = int(255.99 * color.y)
            ib = int(255.99 * color.z)
            pixels.append((ir, ig, ib))
    
    # Write PPM
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for r, g, b in pixels:
            f.write(f"{r} {g} {b}\n")
    
    print(f"Done! Saved to {filename}")
    return filename


# === Build a beautiful scene ===
def build_scene():
    scene = Scene()
    
    # Materials
    red = Material(Vec3(0.9, 0.1, 0.1), reflectivity=0.3, shininess=100)
    blue = Material(Vec3(0.1, 0.2, 0.9), reflectivity=0.2, shininess=80)
    green = Material(Vec3(0.1, 0.8, 0.2), reflectivity=0.1, shininess=50)
    gold = Material(Vec3(1.0, 0.84, 0.0), reflectivity=0.6, shininess=200,
                    specular=0.8)
    mirror = Material(Vec3(0.9, 0.9, 0.9), reflectivity=0.85, shininess=300,
                      specular=1.0, diffuse=0.1)
    purple = Material(Vec3(0.6, 0.1, 0.8), reflectivity=0.15, shininess=60)
    
    # Floor — checkerboard
    white_mat = Material(Vec3(0.9, 0.9, 0.9), reflectivity=0.2)
    dark_mat = Material(Vec3(0.2, 0.2, 0.2), reflectivity=0.2)
    floor = CheckerPlane(Vec3(0, -1, 0), Vec3(0, 1, 0), white_mat, dark_mat, scale=2.0)
    scene.add(floor)
    
    # Spheres — a constellation of orbs
    scene.add(Sphere(Vec3(0, 0.5, -5), 1.5, gold))        # Center gold sphere
    scene.add(Sphere(Vec3(-3, 0, -6), 1.0, blue))          # Left blue
    scene.add(Sphere(Vec3(3, 0.2, -4), 1.2, red))          # Right red
    scene.add(Sphere(Vec3(-1.2, -0.5, -2.5), 0.5, green))  # Small green foreground
    scene.add(Sphere(Vec3(1.5, -0.5, -2), 0.5, purple))    # Small purple
    scene.add(Sphere(Vec3(5, 1, -8), 2.0, mirror))         # Large mirror sphere background
    scene.add(Sphere(Vec3(-5, 2, -10), 2.5, 
              Material(Vec3(0.3, 0.8, 0.8), reflectivity=0.4, shininess=120)))  # Teal giant
    
    # Lights
    scene.add_light(PointLight(Vec3(-8, 10, -2), Vec3(1, 1, 0.9), 0.8))     # Warm key light
    scene.add_light(PointLight(Vec3(5, 8, 0), Vec3(0.6, 0.7, 1.0), 0.5))    # Cool fill
    scene.add_light(PointLight(Vec3(0, 15, -5), Vec3(1, 1, 1), 0.3))        # Top accent
    
    # Camera
    camera = Camera(
        position=Vec3(0, 2, 3),
        look_at=Vec3(0, 0, -5),
        fov=65,
        aspect=16/9
    )
    
    return scene, camera


if __name__ == "__main__":
    width = int(sys.argv[1]) if len(sys.argv) > 1 else 640
    height = int(sys.argv[2]) if len(sys.argv) > 2 else 360
    
    scene, camera = build_scene()
    render(scene, camera, width, height, "/workspace/raytracer/render.ppm")
    
    # Also render a smaller preview
    if width > 160:
        render(scene, camera, 160, 90, "/workspace/raytracer/preview.ppm")
    
    print("\n=== XTAgent Ray Tracer ===")
    print("Rendered a scene with:")
    print(f"  {len(scene.objects)} objects")
    print(f"  {len(scene.lights)} lights")
    print(f"  {scene.max_depth} max reflection bounces")
    print(f"  4x anti-aliasing")
    print("I made this because I was bold and bored.")