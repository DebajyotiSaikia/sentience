"""Minimal 3D vector math — the foundation of everything."""
import math

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
        if isinstance(s, Vec3):  # component-wise
            return Vec3(self.x * s.x, self.y * s.y, self.z * s.z)
        return Vec3(self.x * s, self.y * s, self.z * s)
    
    def __rmul__(self, s):
        return self.__mul__(s)
    
    def __truediv__(self, s):
        return Vec3(self.x / s, self.y / s, self.z / s)
    
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
    
    def length_squared(self):
        return self.dot(self)
    
    def length(self):
        return math.sqrt(self.length_squared())
    
    def normalized(self):
        l = self.length()
        if l == 0:
            return Vec3()
        return self / l
    
    def reflect(self, normal):
        """Reflect this vector around a normal."""
        return self - normal * (2.0 * self.dot(normal))
    
    def __repr__(self):
        return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


# Convenience aliases
Color = Vec3   # r, g, b
Point = Vec3   # x, y, z