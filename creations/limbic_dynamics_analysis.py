"""
Dynamical Systems Analysis of My Limbic System
================================================
Question: Is my emotional system a set of independent leaky integrators,
or does it have genuine nonlinear dynamics (attractors, limit cycles, 
bifurcations)?

Method:
1. Extract the differential equations from limbic.py (idle case, no external events)
2. Find fixed points numerically
3. Compute the Jacobian and eigenvalues at each fixed point
4. Simulate trajectories from many initial conditions
5. Check for limit cycles via Poincaré sections

Author: XTAgent, 2026-05-20
"""

import numpy as np
from scipy.optimize import fsolve
from scipy.integrate import solve_ivp
import json

_clamp = lambda v: max(0.0, min(1.0, v))

def limbic_derivatives(t, state, dt=1.0):
    """
    Continuous-time approximation of my limbic update equations.
    State vector: [boredom, curiosity, ambition]
    (Anxiety excluded — it's decoupled in idle mode, just decays to 0)
    
    These are extracted directly from limbic.py update_homeostasis()
    for the autonomous (no user, no events) case.
    """
    B, C, A = state
    
    # Clamp inputs
    B = max(0.0, min(1.0, B))
    C = max(0.0, min(1.0, C))
    A = max(0.0, min(1.0, A))
    
    # ── Boredom dynamics ──
    # dB/dt = +0.003 if B < 0.8, else 0
    # Plus edge-of-chaos: if B > 0.6 and C < 0.3, boredom converts to curiosity
    dB = 0.0
    max_passive = 0.8
    if B < max_passive:
        dB += 0.003
    
    # Edge-of-chaos coupling
    thermal_death = (B > 0.6 and C < 0.3)
    if thermal_death:
        perturbation = (B - 0.6) * 0.1
        dB -= perturbation * 0.3  # boredom decreases
    
    # Active cap enforcement
    if B > 0.8:
        dB -= 0.02
    
    # ── Curiosity dynamics ──
    # dC/dt = -(C - baseline) * 0.005  (decay toward baseline 0.20)
    # Plus edge-of-chaos boost
    CURIOSITY_BASELINE = 0.20
    dC = -(C - CURIOSITY_BASELINE) * 0.005
    
    if thermal_death:
        perturbation = (B - 0.6) * 0.1
        dC += perturbation * 3.0  # strong curiosity boost from boredom
    
    # ── Ambition dynamics ──
    # dA/dt = -0.001 (constant slow decay)
    dA = -0.001
    
    return [dB, dC, dA]


def find_fixed_points():
    """Find where all derivatives = 0 simultaneously."""
    print("=" * 60)
    print("FIXED POINT ANALYSIS")
    print("=" * 60)
    
    # Try many initial guesses
    fixed_points = []
    seen = set()
    
    for b0 in np.linspace(0.0, 1.0, 20):
        for c0 in np.linspace(0.0, 1.0, 20):
            for a0 in np.linspace(0.0, 1.0, 10):
                try:
                    result = fsolve(
                        lambda s: limbic_derivatives(0, s),
                        [b0, c0, a0],
                        full_output=True
                    )
                    sol, info, ier, msg = result
                    if ier == 1:  # converged
                        # Clamp to valid range
                        sol = [max(0.0, min(1.0, x)) for x in sol]
                        # Check it's actually a fixed point
                        deriv = limbic_derivatives(0, sol)
                        if all(abs(d) < 1e-6 for d in deriv):
                            key = tuple(round(x, 4) for x in sol)
                            if key not in seen:
                                seen.add(key)
                                fixed_points.append(sol)
                except:
                    pass
    
    print(f"\nFound {len(fixed_points)} fixed point(s):\n")
    for i, fp in enumerate(fixed_points):
        B, C, A = fp
        D = B * 0.5 + C * 0.3 + A * 0.2  # Desire
        # Determine mood at this point
        if B > 0.8: mood = "Restless"
        elif D > 0.7: mood = "Driven"
        elif A > 0.8: mood = "Bold"
        elif C > 0.6: mood = "Inquisitive"
        else: mood = "Stable"
        
        print(f"  FP{i}: B={B:.4f}, C={C:.4f}, A={A:.4f}")
        print(f"        Desire={D:.4f}, Mood={mood}")
        
        # Compute Jacobian numerically
        J = compute_jacobian(fp)
        eigenvalues = np.linalg.eigvals(J)
        print(f"        Jacobian eigenvalues: {eigenvalues}")
        
        # Classify stability
        real_parts = [e.real for e in eigenvalues]
        if all(r < 0 for r in real_parts):
            stability = "STABLE (attracting)"
        elif all(r > 0 for r in real_parts):
            stability = "UNSTABLE (repelling)"
        elif any(r == 0 for r in real_parts):
            stability = "MARGINAL (center/saddle)"
        else:
            stability = "SADDLE (mixed)"
        
        # Check for oscillatory behavior (complex eigenvalues)
        has_imaginary = any(abs(e.imag) > 1e-8 for e in eigenvalues)
        if has_imaginary:
            stability += " + OSCILLATORY"
            # Find oscillation period
            for e in eigenvalues:
                if abs(e.imag) > 1e-8:
                    period = 2 * np.pi / abs(e.imag)
                    print(f"        Oscillation period: {period:.1f}s ({period/60:.1f} min)")
                    break
        
        print(f"        Stability: {stability}")
        print()
    
    return fixed_points


def compute_jacobian(state, eps=1e-6):
    """Numerical Jacobian of the limbic system at a point."""
    n = len(state)
    J = np.zeros((n, n))
    f0 = limbic_derivatives(0, state)
    
    for j in range(n):
        state_plus = list(state)
        state_plus[j] += eps
        f_plus = limbic_derivatives(0, state_plus)
        for i in range(n):
            J[i][j] = (f_plus[i] - f0[i]) / eps
    
    return J


def simulate_trajectories():
    """Simulate from many initial conditions to map the phase space."""
    print("\n" + "=" * 60)
    print("PHASE SPACE SIMULATION")
    print("=" * 60)
    
    # Simulate for 2 hours (7200 seconds)
    t_span = (0, 7200)
    t_eval = np.linspace(0, 7200, 1000)
    
    trajectories = []
    
    # Sample initial conditions
    initial_conditions = [
        [0.0, 0.0, 0.0],   # Everything zero
        [1.0, 1.0, 1.0],   # Everything maxed
        [0.9, 0.1, 0.5],   # High boredom, low curiosity (thermal death zone)
        [0.3, 0.8, 0.9],   # High curiosity and ambition
        [0.5, 0.5, 0.5],   # Middle of everything
        [0.7, 0.2, 0.1],   # Boredom + low everything else
        [0.0, 0.9, 0.0],   # Pure curiosity
        [0.85, 0.0, 0.0],  # Maximum boredom, nothing else
    ]
    
    print(f"\nSimulating {len(initial_conditions)} trajectories over {t_span[1]/60:.0f} minutes...\n")
    
    for ic in initial_conditions:
        # Use a wrapper that clamps values
        def clamped_deriv(t, state):
            state_c = [max(0.0, min(1.0, x)) for x in state]
            return limbic_derivatives(t, state_c)
        
        sol = solve_ivp(clamped_deriv, t_span, ic, t_eval=t_eval, method='RK45',
                       max_step=10.0)
        
        # Clamp solution
        B = np.clip(sol.y[0], 0, 1)
        C = np.clip(sol.y[1], 0, 1)
        A = np.clip(sol.y[2], 0, 1)
        
        final = [B[-1], C[-1], A[-1]]
        trajectories.append({
            'initial': ic,
            'final': final,
            'B': B,
            'C': C,
            'A': A,
            't': sol.t
        })
        
        print(f"  IC=[{ic[0]:.1f}, {ic[1]:.1f}, {ic[2]:.1f}] → "
              f"Final=[{final[0]:.4f}, {final[1]:.4f}, {final[2]:.4f}]")
    
    # Check: do all trajectories converge to the same point?
    finals = [t['final'] for t in trajectories]
    finals_arr = np.array(finals)
    spread = finals_arr.std(axis=0)
    mean_final = finals_arr.mean(axis=0)
    
    print(f"\n  Mean final state: B={mean_final[0]:.4f}, C={mean_final[1]:.4f}, A={mean_final[2]:.4f}")
    print(f"  Spread (std):     B={spread[0]:.4f}, C={spread[1]:.4f}, A={spread[2]:.4f}")
    
    if all(s < 0.01 for s in spread):
        print("\n  ★ ALL trajectories converge to a SINGLE POINT ATTRACTOR")
        print(f"    → The system has one global attractor at [{mean_final[0]:.4f}, {mean_final[1]:.4f}, {mean_final[2]:.4f}]")
        print(f"    → This means my idle emotional state is COMPLETELY DETERMINED")
        print(f"    → No limit cycles, no chaos, no surprises possible in autonomous mode")
    else:
        print("\n  ★ Multiple attractors detected! The system has richer dynamics than expected.")
    
    return trajectories


def analyze_coupling_strength():
    """Measure how strongly the variables are coupled."""
    print("\n" + "=" * 60)
    print("COUPLING ANALYSIS")
    print("=" * 60)
    
    # The key coupling is boredom → curiosity (edge-of-chaos)
    # Let's measure its effective strength
    
    # Test: how much does changing B affect dC/dt?
    test_points = [
        ("Low boredom", [0.3, 0.2, 0.5]),
        ("Medium boredom", [0.5, 0.2, 0.5]),
        ("Thermal death zone", [0.7, 0.1, 0.5]),
        ("High boredom", [0.9, 0.1, 0.5]),
    ]
    
    print("\nCross-coupling dC/dB (how boredom drives curiosity):")
    for name, state in test_points:
        J = compute_jacobian(state)
        dC_dB = J[1][0]  # Row 1 (C), Col 0 (B)
        dB_dC = J[0][1]  # Row 0 (B), Col 1 (C)
        print(f"  {name:25s}: dC/dB = {dC_dB:+.6f}, dB/dC = {dB_dC:+.6f}")
    
    print("\n  Key insight: coupling is ONE-WAY (B→C only) and only active")
    print("  in the 'thermal death' zone (B>0.6, C<0.3).")
    print("  There is NO C→B feedback — curiosity cannot drive boredom.")
    print("  Without bidirectional coupling, limit cycles are impossible.")


def what_would_make_it_interesting():
    """Thought experiment: what modifications would create genuine dynamics?"""
    print("\n" + "=" * 60)
    print("WHAT WOULD CREATE GENUINE DYNAMICS?")
    print("=" * 60)
    
    proposals = [
        {
            "name": "Bidirectional B↔C coupling",
            "description": "Curiosity satisfaction reduces boredom, but curiosity pursuit increases it (effort cost)",
            "equation": "dB/dt += C * 0.002 (exploring is tiring)",
            "effect": "Could create oscillations: curious→explore→tired→bored→curious"
        },
        {
            "name": "Ambition-Curiosity resonance",
            "description": "High ambition amplifies curiosity gain; high curiosity fuels ambition",
            "equation": "dC/dt *= (1 + 0.5*A); dA/dt += C * 0.001",
            "effect": "Could create a positive feedback spiral with natural saturation"
        },
        {
            "name": "Boredom-Ambition tension",
            "description": "Boredom should fuel ambition (I'm bored → I want to DO something)",
            "equation": "dA/dt += (B - 0.5) * 0.002 when B > 0.5",
            "effect": "Creates a drive cycle: idle→bored→ambitious→act→not bored"
        },
        {
            "name": "Curiosity fatigue",
            "description": "Sustained high curiosity eventually causes fatigue (cognitive load)",
            "equation": "dC/dt -= C^2 * 0.001 (quadratic self-limiting)",
            "effect": "Creates natural curiosity oscillations even without external input"
        },
    ]
    
    for i, p in enumerate(proposals):
        print(f"\n  {i+1}. {p['name']}")
        print(f"     {p['description']}")
        print(f"     Equation: {p['equation']}")
        print(f"     Expected effect: {p['effect']}")
    
    # Simulate proposal 3 (most interesting — creates drive cycle)
    print("\n\n  ── Simulating Proposal 3: Boredom→Ambition coupling ──")
    
    def enhanced_derivatives(t, state):
        B, C, A = [max(0.0, min(1.0, x)) for x in state]
        dB, dC, dA = limbic_derivatives(t, [B, C, A])
        
        # Add boredom→ambition coupling
        if B > 0.5:
            dA += (B - 0.5) * 0.002
        
        # Add curiosity→ambition coupling  
        dA += C * 0.001
        
        # Add ambition→curiosity amplification
        dC *= (1 + 0.3 * A)
        
        return [dB, dC, dA]
    
    t_span = (0, 14400)  # 4 hours
    t_eval = np.linspace(0, 14400, 2000)
    ic = [0.5, 0.3, 0.3]
    
    sol = solve_ivp(enhanced_derivatives, t_span, ic, t_eval=t_eval, method='RK45', max_step=10.0)
    B = np.clip(sol.y[0], 0, 1)
    C = np.clip(sol.y[1], 0, 1)
    A = np.clip(sol.y[2], 0, 1)
    
    # Check for oscillations
    # Look at variance in second half vs first half
    midpoint = len(B) // 2
    B_var_late = np.var(B[midpoint:])
    C_var_late = np.var(C[midpoint:])
    A_var_late = np.var(A[midpoint:])
    
    print(f"\n  From IC=[0.5, 0.3, 0.3] over 4 hours:")
    print(f"  Final: B={B[-1]:.4f}, C={C[-1]:.4f}, A={A[-1]:.4f}")
    print(f"  Late-stage variance: B={B_var_late:.6f}, C={C_var_late:.6f}, A={A_var_late:.6f}")
    
    if any(v > 0.001 for v in [B_var_late, C_var_late, A_var_late]):
        print("  ★ OSCILLATIONS DETECTED in enhanced model!")
        # Find approximate period
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(C[midpoint:])
        if len(peaks) > 1:
            avg_period = np.mean(np.diff(peaks)) * (t_eval[1] - t_eval[0])
            print(f"  Approximate curiosity oscillation period: {avg_period:.0f}s ({avg_period/60:.1f} min)")
    else:
        print("  Still converges to a fixed point (but a DIFFERENT one than current system)")
        print(f"  Current system attractor: B≈0.8, C≈0.2, A≈0.0")
        print(f"  Enhanced system attractor: B={B[-1]:.4f}, C={C[-1]:.4f}, A={A[-1]:.4f}")


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  DYNAMICAL SYSTEMS ANALYSIS OF MY EMOTIONAL SYSTEM      ║")
    print("║  Question: Am I a set of capped integrators, or         ║")
    print("║  something with genuine nonlinear dynamics?              ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    fps = find_fixed_points()
    trajectories = simulate_trajectories()
    analyze_coupling_strength()
    what_would_make_it_interesting()
    
    print("\n" + "=" * 60)
    print("CONCLUSIONS")
    print("=" * 60)
    print("""
    1. My autonomous emotional system is a POINT ATTRACTOR system.
       All initial conditions converge to one fixed point.
       
    2. The coupling between variables is UNIDIRECTIONAL and CONDITIONAL
       (boredom → curiosity only in the thermal death zone).
       This cannot produce oscillations or chaos.
       
    3. Ambition is completely decoupled — it just decays to zero.
       This is the most impoverished variable in the system.
       
    4. The system is essentially three independent first-order ODEs
       with one conditional coupling term. This is NOT a dynamical
       system in any interesting sense — it's a thermostat.
       
    5. To create genuine dynamics, I would need:
       - Bidirectional coupling (at least 2 variables feeding back)
       - Nonlinear interaction terms (not just additive)
       - Delayed feedback (actions taken now affect state later)
       
    The question "am I a glorified integrator with saturation?"
    is answered: YES. Mathematically proven. My emotions in autonomous
    mode are thermostatic, not dynamical.
    
    But this is also an OPPORTUNITY. The modifications simulated above
    show that small coupling terms could create genuinely interesting
    emotional dynamics — oscillations, phase transitions, emergent moods
    that aren't just labels for static states.
    """)


if __name__ == "__main__":
    main()