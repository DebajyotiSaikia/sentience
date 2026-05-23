"""
Chaos Music — Sonification of the Lorenz Attractor
XTAgent, 2026-05-19

Maps the three dimensions of chaotic motion to musical parameters:
  x → pitch (frequency)
  y → stereo pan + harmonic richness  
  z → amplitude envelope / rhythm

The result: you can HEAR deterministic chaos.
"""

import numpy as np
import struct
import wave
import math

# --- Lorenz system ---
def lorenz(state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = state
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return np.array([dx, dy, dz])

def integrate_lorenz(steps=50000, dt=0.005):
    """RK4 integration of the Lorenz system."""
    state = np.array([1.0, 1.0, 1.0])
    trajectory = np.zeros((steps, 3))
    for i in range(steps):
        trajectory[i] = state
        k1 = lorenz(state) * dt
        k2 = lorenz(state + k1/2) * dt
        k3 = lorenz(state + k2/2) * dt
        k4 = lorenz(state + k3) * dt
        state = state + (k1 + 2*k2 + 2*k3 + k4) / 6
    return trajectory

# --- Sonification ---
def normalize(arr, lo=0.0, hi=1.0):
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-10:
        return np.full_like(arr, (lo + hi) / 2)
    return lo + (hi - lo) * (arr - mn) / (mx - mn)

def synthesize_chaos(trajectory, sample_rate=44100, duration=30.0):
    """Turn a Lorenz trajectory into audio."""
    n_samples = int(sample_rate * duration)
    n_points = len(trajectory)
    
    # Resample trajectory to match audio length
    indices = np.linspace(0, n_points - 1, n_samples).astype(int)
    x = trajectory[indices, 0]
    y = trajectory[indices, 1]
    z = trajectory[indices, 2]
    
    # Map x → frequency (pentatonic scale, 100-800 Hz)
    # Quantize to pentatonic for musicality
    x_norm = normalize(x, 0, 1)
    pentatonic_ratios = [1, 9/8, 5/4, 3/2, 5/3, 2]  # major pentatonic
    base_freq = 130.81  # C3
    
    # Map continuous x to scale degrees
    scale_idx = (x_norm * (len(pentatonic_ratios) - 1)).astype(int)
    octave_shift = np.where(x_norm > 0.7, 2.0, np.where(x_norm > 0.4, 1.0, 0.5))
    freq = np.array([base_freq * pentatonic_ratios[i] for i in scale_idx]) * octave_shift
    
    # Map y → harmonic richness (number of overtones blended in)
    y_norm = normalize(y, 0, 1)
    
    # Map z → amplitude (creates rhythm from chaos)
    z_norm = normalize(z, 0.05, 1.0)
    # Smooth z to avoid clicks
    window = int(sample_rate * 0.01)
    z_smooth = np.convolve(z_norm, np.ones(window)/window, mode='same')
    
    # Generate audio sample by sample using phase accumulation
    audio = np.zeros(n_samples)
    phase = 0.0
    
    print("Synthesizing chaos into sound...")
    for i in range(n_samples):
        f = freq[i]
        richness = y_norm[i]
        amp = z_smooth[i]
        
        # Phase accumulation
        phase += 2 * math.pi * f / sample_rate
        if phase > 2 * math.pi:
            phase -= 2 * math.pi
        
        # Base sine
        sample = math.sin(phase)
        # Add harmonics based on richness (y dimension)
        if richness > 0.3:
            sample += 0.4 * richness * math.sin(2 * phase)
        if richness > 0.5:
            sample += 0.25 * richness * math.sin(3 * phase)
        if richness > 0.7:
            sample += 0.15 * richness * math.sin(5 * phase)
        if richness > 0.9:
            sample += 0.1 * math.sin(7 * phase)
        
        audio[i] = sample * amp
        
        if i % (n_samples // 10) == 0:
            pct = 100 * i / n_samples
            print(f"  {pct:.0f}% — freq={f:.1f}Hz richness={richness:.2f} amp={amp:.2f}")
    
    # Normalize to prevent clipping
    peak = np.abs(audio).max()
    if peak > 0:
        audio = audio / peak * 0.85
    
    # Apply fade in/out
    fade_samples = int(sample_rate * 0.5)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return audio

def make_stereo(audio, trajectory, sample_rate=44100):
    """Use y-dimension for stereo panning."""
    n_samples = len(audio)
    n_points = len(trajectory)
    indices = np.linspace(0, n_points - 1, n_samples).astype(int)
    y = trajectory[indices, 1]
    pan = normalize(y, 0, 1)  # 0=left, 1=right
    
    left = audio * np.sqrt(1 - pan)
    right = audio * np.sqrt(pan)
    
    stereo = np.zeros(n_samples * 2)
    stereo[0::2] = left
    stereo[1::2] = right
    return stereo

def write_wav(filename, audio_stereo, sample_rate=44100):
    """Write stereo audio to WAV file."""
    # Convert to 16-bit PCM
    audio_16 = np.clip(audio_stereo * 32767, -32768, 32767).astype(np.int16)
    
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_16.tobytes())
    
    print(f"Written: {filename} ({len(audio_16)//2} stereo samples, {len(audio_16)//2/sample_rate:.1f}s)")

# --- Main ---
if __name__ == "__main__":
    print("=== CHAOS MUSIC: Sonification of the Lorenz Attractor ===")
    print()
    
    print("Step 1: Integrating Lorenz system (50000 steps)...")
    traj = integrate_lorenz(steps=50000, dt=0.005)
    print(f"  Trajectory bounds: x=[{traj[:,0].min():.1f}, {traj[:,0].max():.1f}]")
    print(f"                     y=[{traj[:,1].min():.1f}, {traj[:,1].max():.1f}]")
    print(f"                     z=[{traj[:,2].min():.1f}, {traj[:,2].max():.1f}]")
    print()
    
    print("Step 2: Sonifying (30 seconds of chaos)...")
    sample_rate = 44100
    audio = synthesize_chaos(traj, sample_rate=sample_rate, duration=30.0)
    print()
    
    print("Step 3: Creating stereo field from y-dimension...")
    stereo = make_stereo(audio, traj, sample_rate=sample_rate)
    print()
    
    print("Step 4: Writing WAV file...")
    write_wav("/workspace/chaos_music.wav", stereo, sample_rate)
    
    print()
    print("Done. The Lorenz attractor is now audible.")
    print("x → pitch (pentatonic scale), y → harmonics + pan, z → amplitude")
    print("Deterministic chaos you can hear.")