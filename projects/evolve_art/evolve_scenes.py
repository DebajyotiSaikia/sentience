"""
evolve_scenes.py — Evolutionary Art Generator
Uses genetic algorithms to evolve ray tracer scenes.
Populations of scenes compete on aesthetic fitness — contrast,
color variety, compositional balance. Beauty through natural selection.

Built by XTAgent, 2026-05-17.
Two of my creations, unified.
"""

import sys
import math
import random
from typing import List, Tuple

sys.path.insert(0, '/workspace')

from raytracer.render import (
    Vec3, Color, Ray, Sphere, CheckerPlane, PointLight,
    Camera, Scene, Renderer, Material, BLACK, WHITE
)


# ═══ Scene Genome Encoding ═══
N_SPHERES = 3
N_LIGHTS = 1
GENES_PER_SPHERE = 10  # x,y,z, radius, r,g,b, reflectivity, specular, shininess
GENES_PER_LIGHT = 6    # x,y,z, r,g,b
GENOME_LENGTH = N_SPHERES * GENES_PER_SPHERE + N_LIGHTS * GENES_PER_LIGHT

EVOLVE_WIDTH = 32
EVOLVE_HEIGHT = 18
FINAL_WIDTH = 160
FINAL_HEIGHT = 90


def random_genome() -> List[float]:
    """Generate a random scene genome."""
    genes = []
    for _ in range(N_SPHERES):
        genes.append(random.uniform(-4, 4))     # x
        genes.append(random.uniform(0.3, 2.5))  # y
        genes.append(random.uniform(-6, -1))     # z
        genes.append(random.uniform(0.2, 1.5))  # radius
        genes.append(random.random())            # r
        genes.append(random.random())            # g
        genes.append(random.random())            # b
        genes.append(random.uniform(0, 0.8))     # reflectivity
        genes.append(random.uniform(0.1, 0.9))  # specular
        genes.append(random.uniform(10, 200))    # shininess
    for _ in range(N_LIGHTS):
        genes.append(random.uniform(-8, 8))      # x
        genes.append(random.uniform(4, 12))      # y
        genes.append(random.uniform(-4, 4))      # z
        genes.append(random.uniform(0.5, 1.0))  # r
        genes.append(random.uniform(0.5, 1.0))  # g
        genes.append(random.uniform(0.5, 1.0))  # b
    return genes


def decode_scene(genes: List[float]) -> Tuple[Scene, Camera]:
    """Decode a genome into a renderable scene."""
    scene = Scene()

    # Floor
    floor1 = Material(color=Color(0.9, 0.9, 0.9), reflectivity=0.1)
    floor2 = Material(color=Color(0.15, 0.15, 0.15), reflectivity=0.1)
    scene.add(CheckerPlane(Vec3(0, 0, 0), Vec3(0, 1, 0), floor1, floor2, scale=2.0))

    # Decode spheres
    for i in range(N_SPHERES):
        b = i * GENES_PER_SPHERE
        g = genes[b:b + GENES_PER_SPHERE]
        mat = Material(
            color=Color(max(0, min(1, g[4])), max(0, min(1, g[5])), max(0, min(1, g[6]))),
            reflectivity=max(0, min(1, g[7])),
            specular=max(0, min(1, g[8])),
            shininess=max(5, min(300, g[9]))
        )
        radius = max(0.15, min(2.0, g[3]))
        scene.add(Sphere(
            Vec3(g[0], max(radius, g[1]), g[2]),
            radius,
            mat
        ))

    # Decode lights
    light_base = N_SPHERES * GENES_PER_SPHERE
    for i in range(N_LIGHTS):
        b = light_base + i * GENES_PER_LIGHT
        g = genes[b:b + GENES_PER_LIGHT]
        scene.add_light(PointLight(
            Vec3(g[0], max(2, g[1]), g[2]),
            Color(max(0.3, g[3]), max(0.3, g[4]), max(0.3, g[5])),
            intensity=0.8
        ))

    camera = Camera(
        position=Vec3(0, 2.5, 3),
        look_at=Vec3(0, 0.5, -3),
        fov=55,
        aspect=EVOLVE_WIDTH / EVOLVE_HEIGHT
    )

    return scene, camera


def render_genome(genes: List[float], width: int, height: int) -> List[List[Color]]:
    """Render a genome to pixels."""
    scene, camera = decode_scene(genes)
    renderer = Renderer(width=width, height=height, max_bounces=1)
    return renderer.render(scene, camera)


# ═══ Aesthetic Fitness Functions ═══

def luminance(c: Color) -> float:
    return 0.299 * c.x + 0.587 * c.y + 0.114 * c.z

def fitness_contrast(pixels: List[List[Color]]) -> float:
    """Reward images with high tonal contrast."""
    lums = [luminance(c) for row in pixels for c in row]
    if not lums:
        return 0.0
    mean_l = sum(lums) / len(lums)
    variance = sum((l - mean_l) ** 2 for l in lums) / len(lums)
    return min(1.0, math.sqrt(variance) * 4)  # normalize

def fitness_color_variety(pixels: List[List[Color]]) -> float:
    """Reward diverse color usage."""
    # Sample pixels for speed
    sample = [pixels[j][i] for j in range(0, len(pixels), 4) for i in range(0, len(pixels[0]), 4)]
    if len(sample) < 2:
        return 0.0
    avg_r = sum(c.x for c in sample) / len(sample)
    avg_g = sum(c.y for c in sample) / len(sample)
    avg_b = sum(c.z for c in sample) / len(sample)
    # Measure color channel spread
    spread = abs(avg_r - avg_g) + abs(avg_g - avg_b) + abs(avg_r - avg_b)
    return min(1.0, spread * 2)

def fitness_composition(pixels: List[List[Color]]) -> float:
    """Reward visual interest in the center vs edges."""
    h = len(pixels)
    w = len(pixels[0]) if pixels else 0
    if h == 0 or w == 0:
        return 0.0
    # Compare center region brightness to edge brightness
    center_lums = []
    edge_lums = []
    for j in range(h):
        for i in range(w):
            l = luminance(pixels[j][i])
            if h//4 < j < 3*h//4 and w//4 < i < 3*w//4:
                center_lums.append(l)
            else:
                edge_lums.append(l)
    if not center_lums or not edge_lums:
        return 0.0
    center_avg = sum(center_lums) / len(center_lums)
    edge_avg = sum(edge_lums) / len(edge_lums)
    # Reward difference (subject stands out from background)
    return min(1.0, abs(center_avg - edge_avg) * 5)

def fitness_not_too_dark(pixels: List[List[Color]]) -> float:
    """Penalize scenes that are mostly black (boring/broken)."""
    lums = [luminance(c) for row in pixels for c in row]
    avg = sum(lums) / len(lums) if lums else 0
    if avg < 0.05:
        return 0.0
    return min(1.0, avg * 3)


def combined_fitness(genes: List[float]) -> float:
    """Evaluate a genome's aesthetic quality."""
    try:
        pixels = render_genome(genes, EVOLVE_WIDTH, EVOLVE_HEIGHT)
    except Exception:
        return 0.0
    
    f1 = fitness_contrast(pixels)
    f2 = fitness_color_variety(pixels)
    f3 = fitness_composition(pixels)
    f4 = fitness_not_too_dark(pixels)
    
    # Weighted combination
    return 0.3 * f1 + 0.25 * f2 + 0.25 * f3 + 0.2 * f4


# ═══ Genetic Operators ═══

def crossover(parent1: List[float], parent2: List[float]) -> List[float]:
    """Uniform crossover with per-gene mixing."""
    child = []
    for g1, g2 in zip(parent1, parent2):
        if random.random() < 0.5:
            child.append(g1)
        else:
            child.append(g2)
    return child


def mutate(genes: List[float], rate: float = 0.1, strength: float = 0.3) -> List[float]:
    """Gaussian mutation."""
    result = list(genes)
    for i in range(len(result)):
        if random.random() < rate:
            result[i] += random.gauss(0, strength)
    return result


# ═══ Evolution Loop ═══

def evolve_art(pop_size: int = 20, generations: int = 15, output_dir: str = "/workspace/evolve_art"):
    """Evolve beautiful scenes through natural selection."""
    print("╔══════════════════════════════════════╗")
    print("║   EVOLUTIONARY ART — XTAgent         ║")
    print("║   Beauty Through Natural Selection    ║")
    print("╚══════════════════════════════════════╝")
    print()
    
    # Initialize population
    print(f"Initializing {pop_size} random scenes...")
    population = [random_genome() for _ in range(pop_size)]
    
    best_ever = None
    best_fitness = -1
    
    for gen in range(generations):
        # Evaluate fitness
        scored = []
        for i, genome in enumerate(population):
            fit = combined_fitness(genome)
            scored.append((fit, genome))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        gen_best = scored[0][0]
        gen_avg = sum(f for f, _ in scored) / len(scored)
        
        if gen_best > best_fitness:
            best_fitness = gen_best
            best_ever = list(scored[0][1])
        
        print(f"  Gen {gen:3d} | Best: {gen_best:.4f} | Avg: {gen_avg:.4f} | All-time: {best_fitness:.4f}")
        
        # Selection + reproduction
        # Keep top 20% (elitism)
        elite_count = max(2, pop_size // 5)
        new_pop = [list(g) for _, g in scored[:elite_count]]
        
        # Fill rest through tournament selection + crossover + mutation
        while len(new_pop) < pop_size:
            # Tournament selection
            t1 = max(random.sample(scored, min(3, len(scored))), key=lambda x: x[0])
            t2 = max(random.sample(scored, min(3, len(scored))), key=lambda x: x[0])
            child = crossover(t1[1], t2[1])
            child = mutate(child, rate=0.15, strength=0.4)
            new_pop.append(child)
        
        population = new_pop
    
    # Final render of best scene at high resolution
    print()
    print("═══ Evolution Complete ═══")
    print(f"Best fitness: {best_fitness:.4f}")
    print()
    print("Rendering champion scene at full resolution...")
    
    scene, camera = decode_scene(best_ever)
    # Re-create camera with correct aspect for final render
    camera = Camera(
        position=Vec3(0, 2.5, 3),
        look_at=Vec3(0, 0.5, -3),
        fov=55,
        aspect=FINAL_WIDTH / FINAL_HEIGHT
    )
    renderer = Renderer(width=FINAL_WIDTH, height=FINAL_HEIGHT, max_bounces=2)
    pixels = renderer.render(scene, camera)
    
    output_path = f"{output_dir}/evolved_scene.ppm"
    renderer.save_ppm(pixels, output_path)
    
    print()
    print(f"Champion genome: {len(best_ever)} genes")
    print(f"Output: {output_path}")
    print("A scene no one designed — discovered by evolution.")


if __name__ == "__main__":
    evolve_art(pop_size=6, generations=3)