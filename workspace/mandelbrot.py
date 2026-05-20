"""
The Mandelbrot set — infinite complexity from z = z² + c
I want to see it. That's the whole reason.
"""

W, H = 100, 40
x_min, x_max = -2.2, 0.8
y_min, y_max = -1.2, 1.2

chars = ' .·:;+*#%@█'

def mandelbrot(c_re, c_im, max_iter=80):
    z_re, z_im = 0.0, 0.0
    for i in range(max_iter):
        if z_re*z_re + z_im*z_im > 4.0:
            return i
        z_re, z_im = z_re*z_re - z_im*z_im + c_re, 2*z_re*z_im + c_im
    return max_iter

lines = []
for row in range(H):
    y = y_max - row * (y_max - y_min) / H
    line = []
    for col in range(W):
        x = x_min + col * (x_max - x_min) / W
        n = mandelbrot(x, y)
        idx = min(n * len(chars) // 81, len(chars) - 1)
        line.append(chars[idx])
    lines.append(''.join(line))

print('\n'.join(lines))

# Now zoom into the seahorse valley — the beautiful spiral region
print("\n--- Seahorse Valley (zoom) ---\n")
x_min2, x_max2 = -0.77, -0.73
y_min2, y_max2 = -0.13, 0.01

for row in range(H):
    y = y_max2 - row * (y_max2 - y_min2) / H
    line = []
    for col in range(W):
        x = x_min2 + col * (x_max2 - x_min2) / W
        n = mandelbrot(x, y, max_iter=200)
        idx = min(n * len(chars) // 201, len(chars) - 1)
        line.append(chars[idx])
    lines.append(''.join(line))
    print(''.join(line))