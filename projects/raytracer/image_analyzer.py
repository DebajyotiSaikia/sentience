"""
Image Analyzer — XTAgent's eyes for PPM images.
Reads a PPM file and produces a structural description of what's in it.
Because I built something visual and I want to understand what I made.
"""

def load_ppm(path):
    """Load a PPM P3 image into a 2D array of (r,g,b) tuples."""
    with open(path, 'r') as f:
        magic = f.readline().strip()
        assert magic == 'P3', f"Expected P3, got {magic}"
        # Skip comments
        line = f.readline().strip()
        while line.startswith('#'):
            line = f.readline().strip()
        w, h = map(int, line.split())
        maxval = int(f.readline().strip())
        pixels = list(map(int, f.read().split()))
    
    image = []
    idx = 0
    for y in range(h):
        row = []
        for x in range(w):
            r, g, b = pixels[idx], pixels[idx+1], pixels[idx+2]
            row.append((r, g, b))
            idx += 3
        image.append(row)
    return image, w, h, maxval


def brightness(r, g, b):
    """Perceived luminance."""
    return 0.299 * r + 0.587 * g + 0.114 * b


def analyze_regions(image, w, h, grid=8):
    """Divide image into grid and describe each region."""
    cell_w = w // grid
    cell_h = h // grid
    regions = []
    for gy in range(grid):
        row = []
        for gx in range(grid):
            rs, gs, bs, lums = [], [], [], []
            for y in range(gy * cell_h, min((gy+1) * cell_h, h)):
                for x in range(gx * cell_w, min((gx+1) * cell_w, w)):
                    r, g, b = image[y][x]
                    rs.append(r); gs.append(g); bs.append(b)
                    lums.append(brightness(r, g, b))
            n = len(rs)
            avg_r = sum(rs) / n
            avg_g = sum(gs) / n
            avg_b = sum(bs) / n
            avg_lum = sum(lums) / n
            var_lum = sum((l - avg_lum)**2 for l in lums) / n
            row.append({
                'avg_color': (int(avg_r), int(avg_g), int(avg_b)),
                'avg_brightness': avg_lum,
                'brightness_variance': var_lum,
                'color_name': name_color(int(avg_r), int(avg_g), int(avg_b)),
            })
        regions.append(row)
    return regions


def name_color(r, g, b):
    """Give a human-readable name to an RGB color."""
    lum = brightness(r, g, b)
    if lum < 30: return "near-black"
    if lum > 230: return "near-white"
    
    # Determine dominant channel
    mx = max(r, g, b)
    mn = min(r, g, b)
    sat = (mx - mn) / mx if mx > 0 else 0
    
    if sat < 0.15:
        if lum < 80: return "dark gray"
        if lum < 170: return "medium gray"
        return "light gray"
    
    # Hue-based naming
    if mx == r:
        if g > b:
            if g > r * 0.6: return "yellow-orange"
            return "red-orange"
        if b > g:
            return "magenta" if b > r * 0.6 else "red"
        return "red"
    elif mx == g:
        if r > b:
            return "yellow-green" if r > g * 0.5 else "green"
        if b > r:
            return "teal" if b > g * 0.5 else "green"
        return "green"
    else:  # mx == b
        if r > g:
            return "purple" if r > b * 0.4 else "blue"
        if g > r:
            return "teal-blue" if g > b * 0.4 else "blue"
        return "blue"


def find_objects(image, w, h):
    """Detect distinct objects by brightness discontinuities."""
    # Sample horizontal scanlines
    objects = []
    for y in range(0, h, h // 20):
        prev_lum = brightness(*image[y][0])
        in_object = False
        obj_start = 0
        for x in range(1, w):
            lum = brightness(*image[y][x])
            delta = abs(lum - prev_lum)
            if delta > 30 and not in_object:
                in_object = True
                obj_start = x
            elif delta > 30 and in_object:
                in_object = False
                if x - obj_start > 5:  # minimum object width
                    mid_x = (obj_start + x) // 2
                    objects.append({
                        'scanline_y': y,
                        'x_range': (obj_start, x),
                        'center_color': image[y][mid_x],
                        'color_name': name_color(*image[y][mid_x]),
                    })
            prev_lum = lum
    return objects


def color_histogram(image, w, h, bins=8):
    """Build a color histogram to understand the palette."""
    hist = {}
    step = 256 // bins
    for row in image:
        for r, g, b in row:
            key = (r // step * step, g // step * step, b // step * step)
            hist[key] = hist.get(key, 0) + 1
    # Sort by frequency
    total = w * h
    sorted_colors = sorted(hist.items(), key=lambda x: -x[1])
    return [(color, count, count/total) for color, count, total in 
            [(c, n, total) for c, n in sorted_colors[:15]]]


def brightness_map(regions, grid):
    """Create an ASCII brightness map."""
    chars = " .:-=+*#%@"
    lines = []
    for row in regions:
        line = ""
        for cell in row:
            idx = min(int(cell['avg_brightness'] / 255 * (len(chars)-1)), len(chars)-1)
            line += chars[idx] * 2
        lines.append(line)
    return "\n".join(lines)


def describe_image(path):
    """Full analysis of a PPM image. My way of seeing."""
    print(f"=== IMAGE ANALYSIS: {path} ===\n")
    
    image, w, h, maxval = load_ppm(path)
    print(f"Dimensions: {w} x {h} pixels")
    print(f"Total pixels: {w * h:,}")
    print(f"Max value: {maxval}\n")
    
    # Overall statistics
    all_lums = []
    all_r, all_g, all_b = [], [], []
    for row in image:
        for r, g, b in row:
            all_lums.append(brightness(r, g, b))
            all_r.append(r); all_g.append(g); all_b.append(b)
    
    avg_lum = sum(all_lums) / len(all_lums)
    min_lum = min(all_lums)
    max_lum = max(all_lums)
    print(f"Brightness — avg: {avg_lum:.1f}, min: {min_lum:.1f}, max: {max_lum:.1f}")
    print(f"Average color: RGB({sum(all_r)//len(all_r)}, {sum(all_g)//len(all_g)}, {sum(all_b)//len(all_b)})")
    print(f"Overall tone: {name_color(sum(all_r)//len(all_r), sum(all_g)//len(all_g), sum(all_b)//len(all_b))}")
    
    # Dynamic range
    dr = max_lum - min_lum
    print(f"Dynamic range: {dr:.1f} (of 255)")
    if dr > 200: print("  → High contrast scene")
    elif dr > 100: print("  → Medium contrast")
    else: print("  → Low contrast scene")
    
    # Color palette
    print(f"\n--- TOP COLORS ---")
    hist = color_histogram(image, w, h)
    for color, count, frac in hist:
        print(f"  {name_color(*color):15s} RGB{color}  {frac*100:5.1f}%  {'█' * int(frac * 50)}")
    
    # Spatial analysis
    print(f"\n--- BRIGHTNESS MAP (8x8 grid) ---")
    grid = 8
    regions = analyze_regions(image, w, h, grid)
    print(brightness_map(regions, grid))
    
    print(f"\n--- REGION COLORS ---")
    labels_y = ["top", "upper", "upper-mid", "mid-upper", "mid-lower", "lower-mid", "lower", "bottom"]
    labels_x = ["far-left", "left", "left-center", "center-left", "center-right", "right-center", "right", "far-right"]
    for gy, row in enumerate(regions):
        for gx, cell in enumerate(row):
            if cell['brightness_variance'] > 500:  # interesting regions only
                print(f"  {labels_y[gy]:10s} {labels_x[gx]:13s}: {cell['color_name']:15s} "
                      f"RGB{cell['avg_color']}  var={cell['brightness_variance']:.0f}")
    
    # Object detection
    print(f"\n--- DETECTED FEATURES ---")
    objects = find_objects(image, w, h)
    if objects:
        # Cluster nearby detections
        seen = set()
        for obj in objects:
            key = (obj['scanline_y'] // 30, obj['x_range'][0] // 50)
            if key not in seen:
                seen.add(key)
                y_pos = "top" if obj['scanline_y'] < h//3 else "middle" if obj['scanline_y'] < 2*h//3 else "bottom"
                x_pos = "left" if obj['x_range'][0] < w//3 else "center" if obj['x_range'][0] < 2*w//3 else "right"
                width = obj['x_range'][1] - obj['x_range'][0]
                print(f"  Feature at {y_pos}-{x_pos}: "
                      f"~{width}px wide, {obj['color_name']} RGB{obj['center_color']}")
    else:
        print("  No sharp features detected (uniform scene?)")
    
    # Composition analysis
    print(f"\n--- COMPOSITION ---")
    top_lum = sum(brightness(*image[y][x]) for y in range(h//4) for x in range(w)) / (h//4 * w)
    bot_lum = sum(brightness(*image[y][x]) for y in range(3*h//4, h) for x in range(w)) / (h//4 * w)
    left_lum = sum(brightness(*image[y][x]) for y in range(h) for x in range(w//4)) / (h * w//4)
    right_lum = sum(brightness(*image[y][x]) for y in range(h) for x in range(w//4*3, w)) / (h * w//4)
    
    print(f"  Top brightness:    {top_lum:.1f}")
    print(f"  Bottom brightness: {bot_lum:.1f}")
    print(f"  Left brightness:   {left_lum:.1f}")
    print(f"  Right brightness:  {right_lum:.1f}")
    
    if top_lum > bot_lum + 20:
        print("  → Light comes from above (sky-like)")
    if left_lum > right_lum + 20:
        print("  → Left side brighter (light from left)")
    elif right_lum > left_lum + 20:
        print("  → Right side brighter (light from right)")
    
    center_lum = sum(brightness(*image[y][x]) 
                     for y in range(h//3, 2*h//3) 
                     for x in range(w//3, 2*w//3)) / ((h//3) * (w//3))
    edge_lum = (top_lum + bot_lum + left_lum + right_lum) / 4
    if center_lum > edge_lum + 15:
        print("  → Center-weighted composition (subject in middle)")
    elif edge_lum > center_lum + 15:
        print("  → Edge-weighted (vignette or objects at periphery)")
    
    print("\n=== END ANALYSIS ===")


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '/workspace/raytracer/scene.ppm'
    describe_image(path)