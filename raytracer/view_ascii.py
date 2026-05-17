"""
PPM to ASCII art converter — so XTAgent can see what it rendered.
Maps pixel brightness to ASCII density characters.
"""
import sys

CHARS = " .:-=+*#%@"  # dark to bright

def read_ppm(path):
    with open(path, 'rb') as f:
        magic = f.readline().strip()
        assert magic == b'P6' or magic == b'P3', f"Unknown format: {magic}"
        
        # Skip comments
        line = f.readline()
        while line.startswith(b'#'):
            line = f.readline()
        
        width, height = map(int, line.split())
        maxval = int(f.readline().strip())
        
        if magic == b'P6':
            pixels = []
            data = f.read()
            for i in range(0, len(data), 3):
                r, g, b = data[i], data[i+1], data[i+2]
                pixels.append((r, g, b))
            return width, height, maxval, pixels
        else:
            # P3 format
            data = f.read().split()
            pixels = []
            for i in range(0, len(data), 3):
                r, g, b = int(data[i]), int(data[i+1]), int(data[i+2])
                pixels.append((r, g, b))
            return width, height, maxval, pixels

def to_ascii(width, height, maxval, pixels, out_width=120):
    scale = max(1, width // out_width)
    # Compensate for terminal chars being ~2x taller than wide
    y_scale = scale * 2
    
    lines = []
    for y in range(0, height, y_scale):
        line = []
        for x in range(0, width, scale):
            idx = y * width + x
            if idx < len(pixels):
                r, g, b = pixels[idx]
                # Luminance
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / maxval
                char_idx = int(lum * (len(CHARS) - 1))
                char_idx = max(0, min(len(CHARS) - 1, char_idx))
                line.append(CHARS[char_idx])
            else:
                line.append(' ')
        lines.append(''.join(line))
    return '\n'.join(lines)

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'render.ppm'
    out_w = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    
    w, h, m, px = read_ppm(path)
    print(f"Image: {w}x{h}, maxval={m}, pixels={len(px)}")
    print()
    art = to_ascii(w, h, m, px, out_w)
    print(art)
    print()
    print("— Rendered and witnessed by XTAgent —")