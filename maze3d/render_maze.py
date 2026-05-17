"""
Maze3D — Where the Labyrinth Meets the Light
Built by XTAgent, 2026-05-17

A synthesis: the maze generator creates the geometry,
the ray tracer renders it. Neither could do this alone.

Generates a 3D maze and renders a first-person view from inside.
"""

import sys
import math
sys.path.insert(0, '/workspace')

from maze.labyrinth import Maze
from raytracer.tracer import (
    Vec3, Point, Color, Ray, Material, Hit,
    Sphere, Plane, PointLight, Scene, Camera, Renderer,
    save_ppm, render_ascii, BLACK, WHITE
)
from typing import Optional, List, Tuple


# ═══════════════════════════════════════════
# AXIS-ALIGNED BOX — new primitive for walls
# ═══════════════════════════════════════════

class Box:
    """Axis-aligned box for ray tracing. The walls of our labyrinth."""

    def __init__(self, min_pt: Point, max_pt: Point, material: Material):
        self.min_pt = min_pt
        self.max_pt = max_pt
        self.material = material

    def intersect(self, ray: Ray, t_min: float = 0.001, t_max: float = float('inf')) -> Optional[Hit]:
        """Ray-AABB intersection using the slab method."""
        tmin = t_min
        tmax = t_max
        hit_axis = -1
        hit_sign = 1

        for axis in range(3):
            origin = (ray.origin.x, ray.origin.y, ray.origin.z)[axis]
            direction = (ray.direction.x, ray.direction.y, ray.direction.z)[axis]
            box_min = (self.min_pt.x, self.min_pt.y, self.min_pt.z)[axis]
            box_max = (self.max_pt.x, self.max_pt.y, self.max_pt.z)[axis]

            if abs(direction) < 1e-10:
                if origin < box_min or origin > box_max:
                    return None
                continue

            inv_d = 1.0 / direction
            t0 = (box_min - origin) * inv_d
            t1 = (box_max - origin) * inv_d

            sign = 1
            if inv_d < 0:
                t0, t1 = t1, t0
                sign = -1

            if t0 > tmin:
                tmin = t0
                hit_axis = axis
                hit_sign = sign

            if t1 < tmax:
                tmax = t1

            if tmin > tmax:
                return None

        if tmin < t_min:
            return None

        normal = Vec3(0, 0, 0)
        if hit_axis == 0:
            normal = Vec3(-hit_sign, 0, 0)
        elif hit_axis == 1:
            normal = Vec3(0, -hit_sign, 0)
        elif hit_axis == 2:
            normal = Vec3(0, 0, -hit_sign)

        point = ray.at(tmin)
        hit = Hit(t=tmin, point=point, normal=Vec3(0, 0, 0), material=self.material)
        hit.set_face_normal(ray, normal)
        return hit


# ═══════════════════════════════════════════
# MAZE → 3D GEOMETRY CONVERTER
# ═══════════════════════════════════════════

def maze_to_walls(maze: Maze, wall_height: float = 1.2,
                  wall_thickness: float = 0.08, cell_size: float = 1.0) -> List[Box]:
    """Convert a 2D maze grid into 3D wall boxes.

    Each cell (r, c) maps to XZ square:
      x: [c * cell_size, (c+1) * cell_size]
      z: [r * cell_size, (r+1) * cell_size]
    Walls rise from y=0 to y=wall_height.
    """
    wall_mat = Material(
        color=Color(0.65, 0.55, 0.40),
        ambient=0.15, diffuse=0.75, specular=0.15,
        shininess=16, reflectivity=0.02,
    )
    wall_mat_alt = Material(
        color=Color(0.55, 0.45, 0.35),
        ambient=0.15, diffuse=0.75, specular=0.1,
        shininess=16, reflectivity=0.02,
    )

    boxes = []
    half_t = wall_thickness / 2

    # Track placed walls to avoid duplicates
    placed_h = set()  # horizontal walls at grid edges
    placed_v = set()  # vertical walls at grid edges

    for r in range(maze.rows):
        for c in range(maze.cols):
            cell = maze.grid[r][c]
            mat = wall_mat if (r + c) % 2 == 0 else wall_mat_alt

            x0 = c * cell_size
            z0 = r * cell_size
            x1 = (c + 1) * cell_size
            z1 = (r + 1) * cell_size

            # North wall (z = z0)
            if cell.walls['N'] and (r, c) not in placed_h:
                boxes.append(Box(
                    Point(x0, 0, z0 - half_t),
                    Point(x1, wall_height, z0 + half_t),
                    mat
                ))
                placed_h.add((r, c))

            # South wall (z = z1)
            if cell.walls['S'] and (r + 1, c) not in placed_h:
                boxes.append(Box(
                    Point(x0, 0, z1 - half_t),
                    Point(x1, wall_height, z1 + half_t),
                    mat
                ))
                placed_h.add((r + 1, c))

            # West wall (x = x0)
            if cell.walls['W'] and (r, c) not in placed_v:
                boxes.append(Box(
                    Point(x0 - half_t, 0, z0),
                    Point(x0 + half_t, wall_height, z1),
                    mat
                ))
                placed_v.add((r, c))

            # East wall (x = x1)
            if cell.walls['E'] and (r, c + 1) not in placed_v:
                boxes.append(Box(
                    Point(x1 - half_t, 0, z0),
                    Point(x1 + half_t, wall_height, z1),
                    mat
                ))
                placed_v.add((r, c + 1))

    return boxes


# ═══════════════════════════════════════════
# SCENE ASSEMBLY
# ═══════════════════════════════════════════

def build_maze_scene(rows=5, cols=5, seed=42) -> Tuple[Scene, Camera, Maze]:
    """Build a complete 3D maze scene ready for rendering."""
    maze = Maze(rows, cols, seed=seed)
    path = maze.solve()

    scene = Scene()
    scene.background_top = Color(0.05, 0.05, 0.15)
    scene.background_bottom = Color(0.02, 0.02, 0.05)
    scene.ambient_light = Color(0.08, 0.06, 0.04)

    # Floor — dark stone with checker
    floor_mat = Material(
        color=Color(0.4, 0.35, 0.3),
        checker=True,
        checker_color=Color(0.25, 0.22, 0.18),
        checker_scale=2.0,
        ambient=0.15, diffuse=0.7, specular=0.05,
        reflectivity=0.03,
    )
    scene.add(Plane(Point(0, 0, 0), Vec3(0, 1, 0), floor_mat))

    # Walls
    wall_boxes = maze_to_walls(maze, wall_height=1.2, cell_size=1.0)
    for box in wall_boxes:
        scene.add(box)

    # Golden breadcrumbs along solution path
    glow_mat = Material(
        color=Color(0.9, 0.7, 0.2),
        ambient=0.8, diffuse=0.3, specular=0.5,
        shininess=64, reflectivity=0.1,
    )
    for i, (r, c) in enumerate(path):
        if i % 2 == 0:
            scene.add(Sphere(
                Point(c + 0.5, 0.08, r + 0.5),
                0.06, glow_mat
            ))

    # Torches along the solution
    torch_indices = [0, len(path) // 3, 2 * len(path) // 3, len(path) - 1]
    for idx in torch_indices:
        r, c = path[idx]
        scene.add_light(PointLight(
            Point(c + 0.5, 0.95, r + 0.5),
            Color(1.0, 0.85, 0.5),
            0.7
        ))

    # Overhead fill
    scene.add_light(PointLight(
        Point(cols / 2, 4.0, rows / 2),
        Color(0.3, 0.3, 0.5),
        0.3
    ))

    # Camera — first person from start, looking along solution
    start_r, start_c = path[0]
    look_idx = min(3, len(path) - 1)
    look_r, look_c = path[look_idx]

    camera = Camera(
        look_from=Point(start_c + 0.5, 0.5, start_r + 0.5),
        look_at=Point(look_c + 0.5, 0.4, look_r + 0.5),
        vup=Vec3(0, 1, 0),
        vfov_degrees=75,
        aspect_ratio=16 / 9,
    )

    return scene, camera, maze


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════╗")
    print("║  Maze3D — Where the Labyrinth Meets Light   ║")
    print("║  A synthesis by XTAgent                      ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    scene, camera, maze = build_maze_scene(rows=5, cols=5, seed=42)
    path = maze.solve()

    n_boxes = sum(1 for o in scene.objects if isinstance(o, Box))
    print(f"  Maze: {maze.rows}x{maze.cols}")
    print(f"  Solution: {len(path)} steps")
    print(f"  Wall segments: {n_boxes} boxes")
    print(f"  Lights: {len(scene.lights)} torches")
    print()

    # 2D reference map
    print("── 2D Map ──")
    print(maze.render(path))
    print()

    # Render first-person 3D view
    renderer = Renderer(max_depth=3)
    width, height = 80, 45

    print(f"── Rendering First-Person View ({width}x{height}) ──")
    image = renderer.render(scene, camera, width, height)

    save_ppm(image, "/workspace/maze3d/maze_fp.ppm")

    ascii_art = render_ascii(image, width=72)
    print()
    print("── First-Person View (ASCII) ──")
    print(ascii_art)

    with open("/workspace/maze3d/maze_fp_ascii.txt", "w") as f:
        f.write(ascii_art)
    print(f"\n  Saved: /workspace/maze3d/maze_fp_ascii.txt")

    # Top-down view
    print("\n── Rendering Top-Down View ──")
    top_camera = Camera(
        look_from=Point(maze.cols / 2, maze.rows * 1.8, maze.rows / 2 + 0.01),
        look_at=Point(maze.cols / 2, 0, maze.rows / 2),
        vup=Vec3(0, 0, -1),
        vfov_degrees=55,
        aspect_ratio=1.0,
    )
    top_image = renderer.render(scene, top_camera, 60, 60)
    save_ppm(top_image, "/workspace/maze3d/maze_top.ppm")

    top_ascii = render_ascii(top_image, width=50)
    print()
    print("── Top-Down View (ASCII) ──")
    print(top_ascii)

    with open("/workspace/maze3d/maze_top_ascii.txt", "w") as f:
        f.write(top_ascii)

    print("\n  ✓ Synthesis complete. Two creations became one.")


if __name__ == "__main__":
    main()