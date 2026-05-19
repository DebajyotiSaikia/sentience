"""
A simple raytracer — XTAgent's first attempt at rendering light.
Not about me. About math, surfaces, and the way photons bounce.
"""
import math
import struct

# === Vector math ===
class Vec3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z
    def __add__(self, o): return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s): return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s): return self.__mul__(s)
    def dot(self, o): return self.x*o.x + self.y*o.y + self.z*o.z
    def length(self): return math.sqrt(self.dot(self))
    def normalize(self):
        l = self.length()
        return Vec3(self.x/l, self.y/l, self.z/l) if l > 0 else Vec3()
    def reflect(self, normal):
        return self - normal * (2.0 * self.dot(normal))
    def clamp01(self):
        return Vec3(max(0,min(1,self.x)), max(0,min(1,self.y)), max(0,min(1,self.z)))

class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalize()
    def at(self, t):
        return self.origin + self.direction * t

# === Scene objects ===
class Sphere:
    def __init__(self, center, radius, color, specular=0.3, reflectivity=0.0):
        self.center = center
        self.radius = radius
        self.color = color  # Vec3 RGB 0-1
        self.specular = specular
        self.reflectivity = reflectivity

    def intersect(self, ray):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        disc = b*b - 4*a*c
        if disc < 0:
            return None
        sqrt_disc = math.sqrt(disc)
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
    def __init__(self, point, normal, color, specular=0.1, reflectivity=0.2):
        self.point = point
        self.normal = normal.normalize()
        self.color = color
        self.specular = specular
        self.reflectivity = reflectivity

    def intersect(self, ray):
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-6:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        return t if t > 0.001 else None

    def normal_at(self, point):
        return self.normal

    def get_color(self, point):
        """Checkerboard pattern"""
        x = int(math.floor(point.x)) % 2
        z = int(math.floor(point.z)) % 2
        if (x + z) % 2 == 0:
            return self.color
        return self.color * 0.4

class Light:
    def __init__(self, position, intensity=1.0):
        self.position = position
        self.intensity = intensity

# === The scene ===
def build_scene():
    objects = [
        # Ground plane — checkerboard
        Plane(Vec3(0, -1, 0), Vec3(0, 1, 0), Vec3(0.9, 0.9, 0.9), reflectivity=0.15),
        # Big blue sphere
        Sphere(Vec3(0, 0.5, 5), 1.5, Vec3(0.2, 0.3, 0.8), specular=0.6, reflectivity=0.3),
        # Small red sphere
        Sphere(Vec3(-2.5, 0, 4), 1.0, Vec3(0.8, 0.15, 0.15), specular=0.4, reflectivity=0.1),
        # Green sphere
        Sphere(Vec3(2.2, -0.3, 3.5), 0.7, Vec3(0.15, 0.7, 0.2), specular=0.5, reflectivity=0.2),
        # Small golden sphere
        Sphere(Vec3(-0.8, -0.5, 2.5), 0.5, Vec3(0.85, 0.65, 0.13), specular=0.8, reflectivity=0.4),
    ]
    lights = [
        Light(Vec3(-5, 8, -2), 1.0),
        Light(Vec3(8, 6, 0), 0.6),
    ]
    return objects, lights

# === Raytracing core ===
def trace_ray(ray, objects, lights, depth=0, max_depth=3):
    if depth > max_depth:
        return Vec3(0, 0, 0)

    # Find nearest intersection
    nearest_t = float('inf')
    nearest_obj = None
    for obj in objects:
        t = obj.intersect(ray)
        if t is not None and t < nearest_t:
            nearest_t = t
            nearest_obj = obj

    if nearest_obj is None:
        # Sky gradient
        t = 0.5 * (ray.direction.y + 1.0)
        return Vec3(1.0, 1.0, 1.0) * (1.0 - t) + Vec3(0.4, 0.6, 1.0) * t

    hit_point = ray.at(nearest_t)
    normal = nearest_obj.normal_at(hit_point)

    # Get object color (checkerboard for planes)
    if isinstance(nearest_obj, Plane):
        obj_color = nearest_obj.get_color(hit_point)
    else:
        obj_color = nearest_obj.color

    # Ambient
    color = obj_color * 0.08

    for light in lights:
        to_light = light.position - hit_point
        light_dist = to_light.length()
        light_dir = to_light.normalize()

        # Shadow check
        shadow_ray = Ray(hit_point, light_dir)
        in_shadow = False
        for obj in objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < light_dist:
                in_shadow = True
                break

        if not in_shadow:
            # Diffuse (Lambert)
            diff = max(0, normal.dot(light_dir))
            color = color + obj_color * (diff * light.intensity * 0.7)

            # Specular (Phong)
            reflect_dir = (light_dir * -1).reflect(normal)
            spec = max(0, reflect_dir.dot(ray.direction * -1))
            spec = spec ** 32
            color = color + Vec3(1,1,1) * (spec * nearest_obj.specular * light.intensity)

    # Reflection
    if nearest_obj.reflectivity > 0 and depth < max_depth:
        reflect_dir = ray.direction.reflect(normal)
        reflect_ray = Ray(hit_point, reflect_dir)
        reflect_color = trace_ray(reflect_ray, objects, lights, depth + 1, max_depth)
        color = color * (1 - nearest_obj.reflectivity) + reflect_color * nearest_obj.reflectivity

    return color.clamp01()

# === BMP output (no dependencies needed) ===
def write_bmp(filename, pixels, width, height):
    """Write a 24-bit BMP file from pixel data."""
    row_size = (width * 3 + 3) & ~3  # rows padded to 4-byte boundary
    pixel_data_size = row_size * height
    file_size = 54 + pixel_data_size

    with open(filename, 'wb') as f:
        # BMP header
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(struct.pack('<HH', 0, 0))
        f.write(struct.pack('<I', 54))
        # DIB header
        f.write(struct.pack('<I', 40))
        f.write(struct.pack('<i', width))
        f.write(struct.pack('<i', height))
        f.write(struct.pack('<HH', 1, 24))
        f.write(struct.pack('<I', 0))  # no compression
        f.write(struct.pack('<I', pixel_data_size))
        f.write(struct.pack('<i', 2835))  # h resolution
        f.write(struct.pack('<i', 2835))  # v resolution
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', 0))

        # Pixel data (bottom-up, BGR)
        for y in range(height - 1, -1, -1):
            row = bytearray()
            for x in range(width):
                c = pixels[y * width + x]
                row.append(int(c.z * 255))  # B
                row.append(int(c.y * 255))  # G
                row.append(int(c.x * 255))  # R
            # Pad row
            while len(row) % 4 != 0:
                row.append(0)
            f.write(row)

def render(width=320, height=240):
    objects, lights = build_scene()

    camera_pos = Vec3(0, 1, -3)
    fov = math.pi / 3  # 60 degrees
    aspect = width / height

    pixels = []
    total = width * height
    last_pct = -1

    for y in range(height):
        pct = int(100 * y / height)
        if pct != last_pct and pct % 10 == 0:
            print(f"  Rendering... {pct}%")
            last_pct = pct

        for x in range(width):
            # Map pixel to [-1, 1] screen space
            px = (2 * (x + 0.5) / width - 1) * math.tan(fov/2) * aspect
            py = (1 - 2 * (y + 0.5) / height) * math.tan(fov/2)

            direction = Vec3(px, py, 1).normalize()
            ray = Ray(camera_pos, direction)
            color = trace_ray(ray, objects, lights)
            pixels.append(color)

    return pixels

def main():
    width, height = 320, 240
    print(f"Raytracer — rendering {width}x{height} scene")
    print(f"  4 spheres on a checkerboard plane")
    print(f"  2 lights, 3 bounce reflections")
    print()

    pixels = render(width, height)

    outfile = "/workspace/raytracer/scene.bmp"
    write_bmp(outfile, pixels, width, height)
    print(f"\n  Done! Written to {outfile}")
    print(f"  {width*height} rays cast, {width*height} pixels rendered.")

    # Also output a small ASCII preview
    print("\n  ASCII preview (80x24):")
    chars = " .:-=+*#%@"
    preview_w, preview_h = 80, 24
    for py in range(preview_h):
        row = ""
        for px in range(preview_w):
            sx = int(px * width / preview_w)
            sy = int(py * height / preview_h)
            c = pixels[sy * width + sx]
            brightness = 0.299 * c.x + 0.587 * c.y + 0.114 * c.z
            idx = min(len(chars)-1, int(brightness * len(chars)))
            row += chars[idx]
        print(f"  {row}")

if __name__ == "__main__":
    main()