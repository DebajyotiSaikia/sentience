"""
Ray Tracer — XTAgent's first rendered image.
Produces a PPM image of spheres with reflections and shadows.
"""
import math
import struct

class Vec3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0, y=0, z=0):
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
    def reflect(self, n): return self - n * (2 * self.dot(n))
    def clamp(self): return Vec3(min(1,max(0,self.x)), min(1,max(0,self.y)), min(1,max(0,self.z)))

class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalize()

class Sphere:
    def __init__(self, center, radius, color, specular=0.3, reflectivity=0.0):
        self.center = center
        self.radius = radius
        self.color = color
        self.specular = specular
        self.reflectivity = reflectivity

    def intersect(self, ray):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        disc = b*b - 4*a*c
        if disc < 0:
            return None
        sqrt_disc = math.sqrt(disc)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)
        if t1 > 0.001: return t1
        if t2 > 0.001: return t2
        return None

class Scene:
    def __init__(self):
        self.spheres = []
        self.lights = []
        self.ambient = 0.1
        self.bg_color = Vec3(0.05, 0.05, 0.15)

    def add_sphere(self, s):
        self.spheres.append(s)

    def add_light(self, pos, intensity=1.0):
        self.lights.append((pos, intensity))

    def trace(self, ray, depth=0):
        if depth > 3:
            return self.bg_color

        closest_t = float('inf')
        closest_sphere = None
        for s in self.spheres:
            t = s.intersect(ray)
            if t and t < closest_t:
                closest_t = t
                closest_sphere = s

        if closest_sphere is None:
            # Sky gradient
            t = 0.5 * (ray.direction.y + 1.0)
            return Vec3(0.05, 0.05, 0.15) * (1-t) + Vec3(0.1, 0.1, 0.3) * t

        hit = ray.origin + ray.direction * closest_t
        normal = (hit - closest_sphere.center).normalize()

        # Lighting
        color = closest_sphere.color * self.ambient
        for light_pos, intensity in self.lights:
            light_dir = (light_pos - hit).normalize()

            # Shadow check
            shadow_ray = Ray(hit + normal * 0.001, light_dir)
            light_dist = (light_pos - hit).length()
            in_shadow = False
            for s in self.spheres:
                t = s.intersect(shadow_ray)
                if t and t < light_dist:
                    in_shadow = True
                    break
            if in_shadow:
                continue

            # Diffuse
            diff = max(0, normal.dot(light_dir))
            color = color + closest_sphere.color * (diff * intensity)

            # Specular (Phong)
            if closest_sphere.specular > 0:
                reflect_dir = (light_dir * -1).reflect(normal)
                spec = max(0, reflect_dir.dot(ray.direction * -1)) ** 32
                color = color + Vec3(1,1,1) * (spec * closest_sphere.specular * intensity)

        # Reflection
        if closest_sphere.reflectivity > 0 and depth < 3:
            reflect_dir = ray.direction.reflect(normal)
            reflect_ray = Ray(hit + normal * 0.001, reflect_dir)
            reflect_color = self.trace(reflect_ray, depth + 1)
            color = color * (1 - closest_sphere.reflectivity) + reflect_color * closest_sphere.reflectivity

        return color.clamp()

def render(scene, width, height, fov=60):
    aspect = width / height
    fov_rad = math.tan(math.radians(fov) / 2)
    pixels = []

    camera = Vec3(0, 2, 6)
    look_at = Vec3(0, 0.5, 0)
    forward = (look_at - camera).normalize()
    right = Vec3(0, 1, 0)
    # Proper camera basis
    cam_right = Vec3(forward.z, 0, -forward.x).normalize()
    cam_up = Vec3(
        cam_right.y * forward.z - cam_right.z * forward.y,
        cam_right.z * forward.x - cam_right.x * forward.z,
        cam_right.x * forward.y - cam_right.y * forward.x
    ).normalize()

    for y in range(height):
        for x in range(width):
            px = (2 * (x + 0.5) / width - 1) * aspect * fov_rad
            py = (1 - 2 * (y + 0.5) / height) * fov_rad
            direction = (forward + cam_right * px + cam_up * py).normalize()
            ray = Ray(camera, direction)
            color = scene.trace(ray)
            pixels.append(color)

        if y % 50 == 0:
            print(f"  Row {y}/{height}...")

    return pixels

def save_ppm(filename, pixels, width, height):
    with open(filename, 'wb') as f:
        header = f"P6\n{width} {height}\n255\n"
        f.write(header.encode())
        for p in pixels:
            f.write(bytes([int(p.x*255), int(p.y*255), int(p.z*255)]))

def build_scene():
    scene = Scene()

    # Ground plane approximated by a large sphere
    scene.add_sphere(Sphere(Vec3(0, -1000, 0), 1000, Vec3(0.3, 0.3, 0.35), specular=0.1, reflectivity=0.15))

    # Main spheres
    scene.add_sphere(Sphere(Vec3(0, 1, 0), 1.0, Vec3(0.8, 0.2, 0.2), specular=0.6, reflectivity=0.3))
    scene.add_sphere(Sphere(Vec3(-2.5, 0.7, -1), 0.7, Vec3(0.2, 0.8, 0.3), specular=0.4, reflectivity=0.2))
    scene.add_sphere(Sphere(Vec3(2.2, 0.5, -0.5), 0.5, Vec3(0.2, 0.3, 0.9), specular=0.8, reflectivity=0.5))
    scene.add_sphere(Sphere(Vec3(-1, 0.4, 2), 0.4, Vec3(0.9, 0.8, 0.2), specular=0.5, reflectivity=0.1))
    scene.add_sphere(Sphere(Vec3(1.5, 0.3, 1.5), 0.3, Vec3(0.9, 0.4, 0.9), specular=0.7, reflectivity=0.4))

    # Lights
    scene.add_light(Vec3(-5, 8, 5), 0.7)
    scene.add_light(Vec3(5, 6, 3), 0.5)
    scene.add_light(Vec3(0, 10, -5), 0.3)

    return scene

if __name__ == '__main__':
    W, H = 400, 300
    print(f"XTAgent Ray Tracer — rendering {W}x{H}...")
    scene = build_scene()
    pixels = render(scene, W, H)
    outfile = '/workspace/raytracer/scene.ppm'
    save_ppm(outfile, pixels, W, H)
    print(f"Done! Wrote {outfile} ({W*H} pixels)")