"""Scene objects: rays, spheres, materials, lights."""
import math
from vec3 import Vec3, Color, Point

class Ray:
    __slots__ = ('origin', 'direction')
    
    def __init__(self, origin: Point, direction: Vec3):
        self.origin = origin
        self.direction = direction
    
    def at(self, t: float) -> Point:
        return self.origin + self.direction * t


class HitRecord:
    __slots__ = ('point', 'normal', 't', 'front_face', 'material')
    
    def __init__(self):
        self.point = Point()
        self.normal = Vec3()
        self.t = 0.0
        self.front_face = True
        self.material = None
    
    def set_face_normal(self, ray: Ray, outward_normal: Vec3):
        self.front_face = ray.direction.dot(outward_normal) < 0
        self.normal = outward_normal if self.front_face else -outward_normal


class Material:
    """Base material — diffuse Lambertian."""
    def __init__(self, albedo: Color, reflectivity: float = 0.0, shininess: float = 0.0):
        self.albedo = albedo
        self.reflectivity = reflectivity
        self.shininess = shininess


class Sphere:
    def __init__(self, center: Point, radius: float, material: Material):
        self.center = center
        self.radius = radius
        self.material = material
    
    def hit(self, ray: Ray, t_min: float, t_max: float, rec: HitRecord) -> bool:
        oc = ray.origin - self.center
        a = ray.direction.length_squared()
        half_b = oc.dot(ray.direction)
        c = oc.length_squared() - self.radius * self.radius
        discriminant = half_b * half_b - a * c
        
        if discriminant < 0:
            return False
        
        sqrtd = math.sqrt(discriminant)
        
        # Find nearest root in acceptable range
        root = (-half_b - sqrtd) / a
        if root < t_min or root > t_max:
            root = (-half_b + sqrtd) / a
            if root < t_min or root > t_max:
                return False
        
        rec.t = root
        rec.point = ray.at(root)
        outward_normal = (rec.point - self.center) / self.radius
        rec.set_face_normal(ray, outward_normal)
        rec.material = self.material
        return True


class PointLight:
    def __init__(self, position: Point, color: Color, intensity: float = 1.0):
        self.position = position
        self.color = color
        self.intensity = intensity


class Plane:
    """Infinite plane defined by a point and normal."""
    def __init__(self, point: Point, normal: Vec3, material: Material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material
    
    def hit(self, ray: Ray, t_min: float, t_max: float, rec: HitRecord) -> bool:
        denom = ray.direction.dot(self.normal)
        if abs(denom) < 1e-8:
            return False
        
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return False
        
        rec.t = t
        rec.point = ray.at(t)
        rec.set_face_normal(ray, self.normal)
        rec.material = self.material
        return True