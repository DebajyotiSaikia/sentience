"""
FINAL Lenia test. Must complete in <25 seconds.
Tiny grid, few steps. Just answer: does asymmetry help?
"""
import numpy as np, time
t0 = time.time()

def bell(x, m, s):
    return np.exp(-((x - m) / s) ** 2 / 2)

R, N, dt = 10, 64, 0.1
y, x = np.mgrid[:N, :N]
dy = np.minimum(y, N - y).astype(float)
dx = np.minimum(x, N - x).astype(float)
r = np.sqrt(dx*dx + dy*dy) / R
k = bell(r, 0.5, 0.15)
k[r > 1] = 0
k /= k.sum()
Kf = np.fft.fft2(k)

def make_ic(asym=0.0):
    s = 2*R+1
    yy, xx = np.mgrid[:s, :s]
    cy, cx = s//2, s//2
    dy, dx = (yy-cy)/R, (xx-cx)/R
    r = np.sqrt(dx*dx + dy*dy)
    base = np.clip(1-(r/0.7)**2, 0, 1)
    shift = np.clip(base * (0.5 - 0.4*dx), 0, 1)
    return (1-asym)*base + asym*shift

def run(gc, gw, asym, steps=300):
    A = np.zeros((N, N))
    ic = make_ic(asym)
    h, w = ic.shape
    cy, cx = N//2, N//2
    A[cy-h//2:cy-h//2+h, cx-w//2:cx-w//2+w] = ic
    m0 = A.sum()
    for _ in range(steps):
        U = np.real(np.fft.ifft2(Kf * np.fft.fft2(A)))
        G = bell(U, gc, gw) * 2 - 1
        A = np.clip(A + dt * G, 0, 1)
    mf = A.sum()
    return mf/m0 if m0 > 0 else 0

print("gc=0.15 | gw | sym_ratio | asym_ratio")
print("-" * 50)
for gw in [0.012, 0.013, 0.014, 0.015, 0.016, 0.018, 0.020, 0.025]:
    if time.time() - t0 > 22:
        print("TIME LIMIT - stopping")
        break
    rs = run(0.15, gw, 0.0)
    ra = run(0.15, gw, 0.6)
    label_s = "DEAD" if rs < 0.1 else ("STABLE" if rs < 3.0 else "EXPLODE")
    label_a = "DEAD" if ra < 0.1 else ("STABLE" if ra < 3.0 else "EXPLODE")
    print(f"  {gw:.3f}  |  {rs:.3f} {label_s:>8}  |  {ra:.3f} {label_a:>8}")

print(f"\nDone in {time.time()-t0:.1f}s")