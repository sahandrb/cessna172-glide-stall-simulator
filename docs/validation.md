# Validation

Run the checks with

```bash
pytest
```

The tests implement section 11.2 of `PROJECT_SPEC.txt`. Numbers below are what those tests compare. They are not copied into the aerodynamics module as magic results. The module evaluates the same formulas.

## Best lift-to-drag ratio

\[
C_L^\star = \sqrt{0.032/0.0524} \approx 0.7815, \qquad
(L/D)_\max = 1/(2\sqrt{0.032\times 0.0524}) \approx 12.211, \qquad
\alpha^\star \approx 6.057\ \mathrm{deg}.
\]

The test requires \((L/D)_\max\) within 0.05 of 12.2 and \(\alpha^\star\) within 0.02 deg of 6.05, and an exact match to an independent evaluation of the formulas.

## Stationary equilibrium

From the equilibrium glide at constant \(\alpha = 6\) deg and constant \(\rho = 1.225\), a 10 s integration keeps \(V\) and \(\gamma\) within \(10^{-3}\) of the initial values. The ISA model is not used for this check, because density would change with altitude.

At the same condition the derivatives \(\dot V\) and \(\dot\gamma\) are zero within \(10^{-8}\) before any integration.

## Stall speed

With \(m = 1156.7\) kg, \(S = 16.165\) m\(^2\), \(\rho = 1.225\), \(g = 9.80665\), and \(C_{L,\max} = 1.541\),

\[
V_s = \sqrt{2mg/(\rho S C_{L,\max})} \approx 27.27\ \mathrm{m/s},
\]

reported as about 27.3 m/s. This \(C_{L,\max}\) is the POH back-calculation, not the 1.544 value of the 14 deg homework line.

## Continuity

\(C_L(\alpha_\mathrm{stall})\) from the homework line equals the stalled branch at the same angle. One degree above the stall, \(C_L\) is lower by the configured 0.07.

## Glide distance

From 1000 m to the 10 m stop, at \(\alpha^\star\) and constant density, the integrated range is within 3 percent of \((1000 - 10)\,(L/D)_\max\). Analytically, with constant \(\gamma\), the range equals that product.

## Homework part (d)

One `solve_ivp` call from 0 to 10 s, \(h_0 = 10\) m, \(r_0 = 0\), constant default \(\alpha\), equilibrium \(V\) and \(\gamma\), samples every 0.01 s (1001 points). The altitude event is off, so the run is not stopped at \(t = 0\). All four series are finite. `python -m cessna_sim --hw` writes figures 1–4 under `outputs/hw_YYYYMMDD_HHMMSS/`.

## Sprite geometry

A positive pitch angle moves a nose-right offset upward in pygame's y-down axes. Rebuilding the center of gravity from the rotated image center returns the same screen point at several angles, within a numerical tolerance much smaller than one pixel.

The prepared PNG has the nose to the right of the center of gravity, and the masked hub contains no opaque pixels.
