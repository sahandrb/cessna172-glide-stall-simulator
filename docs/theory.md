# Theory

This note records the equations used by the simulator. Internal angles are radians. The aerodynamic formulas take angle of attack in degrees. The model is the point-mass longitudinal glide from the flight-dynamics homework, plus one labeled stall extension.

## Coefficients

With \(\alpha\) in degrees,

\[
C_L(\alpha) = 0.20 + 0.096\,\alpha
\]

on and below the stall angle. Above it the stall extension replaces that line. Drag and pitching moment are

\[
C_D(C_L) = 0.032 + 0.0524\,C_L^2, \qquad
C_m(\alpha) = -0.01449\,(\alpha - 2.25).
\]

\(C_m\) uses a trim angle of 2.25 deg from the homework statement. It is computed, displayed, and plotted only. It does not enter the equations of motion.

## Forces and equations

Dynamic pressure, lift, and drag are \(q = \tfrac12\rho V^2\), \(L = q S C_L\), and \(D = q S C_D\). Weight is \(W = mg\). With thrust equal to zero,

\[
\begin{aligned}
\dot V &= -D/m - g\sin\gamma, \\
\dot\gamma &= (L - W\cos\gamma)/(m V), \\
\dot h &= V\sin\gamma, \\
\dot r &= V\cos\gamma.
\end{aligned}
\]

The state is \([V, \gamma, h, r]\). The only input is \(\alpha(t)\). Pitch for the drawing is

\[
\theta = \alpha + \gamma
\]

with both angles in the same unit. Positive \(\gamma\) climbs. Positive \(\theta\) raises the nose.

## Equilibrium glide

Set \(\dot V = 0\) and \(\dot\gamma = 0\):

\[
D = -W\sin\gamma, \qquad L = W\cos\gamma.
\]

Dividing these gives \(\tan\gamma = -D/L = -C_D/C_L\), so

\[
\gamma_\mathrm{eq} = -\arctan(C_D/C_L)
\]

provided \(C_L > 0\). Substituting lift into \(q\) gives

\[
V_\mathrm{eq} = \sqrt{\frac{2 W \cos\gamma_\mathrm{eq}}{\rho(h)\, S\, C_L}}.
\]

\(\gamma_\mathrm{eq}\) does not depend on density. \(V_\mathrm{eq}\) does. Every run starts on this equilibrium at the chosen altitude and angle of attack, with \(r = 0\). If \(C_L \le 0\) the run is refused.

At constant \(\alpha\) and constant density the equilibrium is an exact stationary solution: \(V\) and \(\gamma\) stay constant, and the horizontal distance between two altitudes is

\[
r = (h_0 - h)\,\frac{C_L}{C_D} = (h_0 - h)\,\frac{L}{D}.
\]

## Best lift-to-drag ratio

For \(C_D = C_{D0} + K C_L^2\),

\[
C_L^\star = \sqrt{C_{D0}/K}, \qquad
(L/D)_\max = 1\big/\big(2\sqrt{C_{D0} K}\big), \qquad
\alpha^\star = (C_L^\star - 0.20)/0.096.
\]

With the homework numbers these are about \(C_L^\star = 0.781\), \((L/D)_\max = 12.21\), and \(\alpha^\star = 6.06\) deg. The code evaluates the formulas. It does not store the rounded results. The still-air distance from a height change \(\Delta h\) is about \(\Delta h\,(L/D)\), and the best case is \(\Delta h\,(L/D)_\max\).

## Density

The default model is the specification's troposphere formula

\[
\rho(h) = 1.225\,(1 - 2.2558\times 10^{-5}\, h)^{4.2559}.
\]

`density_model = "constant"` holds \(\rho = 1.225\). The stationary-glide and best-distance checks use the constant model, because in the ISA model density changes as the airplane descends and the initial equilibrium is no longer exact.

## Integration

`scipy.integrate.solve_ivp`, method `RK23`, relative tolerance \(10^{-6}\), absolute tolerance \(10^{-8}\), `float64`. Homework part (d) is one call from 0 to 10 s with constant \(\alpha\), \(h_0 = 10\) m, and samples every 0.01 s. That run does not stop at \(h = 10\) m, because that is the initial altitude. The interactive glide does stop at \(h = 10\) m, or at the time limit, or if \(V \le 0.5\) m/s.

In the interactive view, each physics step of 0.02 s holds \(\alpha\) constant. The keyboard or the slider changes \(\alpha\) after the step.

## Stall extension

This extension is not part of the homework. The interface labels it as an assumption.

Default \(\alpha_\mathrm{stall} = 14\) deg and the post-stall slope is 0.07 per degree:

\[
C_L =
\begin{cases}
0.20 + 0.096\,\alpha & \alpha \le \alpha_\mathrm{stall}, \\
C_{L,\max} - 0.07\,(\alpha - \alpha_\mathrm{stall}) & \alpha > \alpha_\mathrm{stall}.
\end{cases}
\]

\(C_{L,\max}\) is the homework line at \(\alpha_\mathrm{stall}\), so \(C_L\) is continuous there. At 14 deg, \(C_{L,\max} = 1.544\).

Why 14 deg:

- The Cessna 172S POH stall speed, flaps up, power off, at 2550 lb, is 48 KIAS = 53 KCAS = 27.27 m/s. Calibrated airspeed is the right speed for this back-calculation, not indicated airspeed.
- \(C_{L,\max} = 2W /(\rho S V_s^2) = 1.541\) at sea level with \(\rho = 1.225\) and \(S = 16.165\) m\(^2\).
- The homework line reaches about 1.54 at 13.96 deg, so the break is placed at 14 deg.
- At 16 deg the homework line gives \(C_L = 1.736\) and \(V_s \approx 25.7\) m/s, about 3 kt under the POH and about 13 percent high on \(C_L\).
- POH banked stall speeds follow \(V_s\sqrt{n}\): 57, 63, and 75 KCAS at 30, 45, and 60 deg of bank.
- JSBSim's c172p model, a whole-airplane body-axis curve, peaks at \(C_L = 1.47\) at 16 deg and then falls through 1.43, 1.38, 1.30, and 1.15. That fall is the source of the 0.07 per degree slope.
- A NACA 2412 section at \(Re = 10^6\) reaches a higher section \(c_{l,\max}\) (about 1.58 at 16.5 deg). A section maximum sits above the airplane maximum because of the finite wing and tail download.

The 1-g stall speed shown in the dashboard is

\[
V_s(h) = \sqrt{2W / (\rho(h)\, S\, C_{L,\max})}.
\]

It is a true airspeed, so it rises as density falls. The optional load-factor value is \(V_{s,n} = V_s\sqrt{n}\) with \(n = L/W\).

A stall is \(\alpha > \alpha_\mathrm{stall}\). Onset and recovery are logged with time, altitude, speed, and angle of attack.

Default drag after the break still uses the homework polar. When \(C_L\) falls, that polar makes drag fall with it. That is not physical. The config option `assumed_rise` adds \(0.02\) per degree above the stall. That rise has no source. It is an illustration, and it is off by default.

## Drawing assumption

The point-mass model has no pitch dynamics, so \(\alpha\) changes in a step. Only the sprite rotation is eased, with a time constant `display_pitch_smoothing_s` of 0.15 s. The integrator, the log, the dashboard, and the plots all use the true angle.

Positive pitch raises the nose. pygame's \(y\) axis points down, so the rotation that implements a positive angle moves a nose-right vector toward smaller screen \(y\). The sprite is rotated about the center of gravity, not about the image center.

## Default mass and area

\(m = 1156.7\) kg is the 172S maximum gross weight of 2550 lb. \(S = 16.165\) m\(^2\) is 174 ft\(^2\). \(g = 9.80665\) m/s\(^2\). If the homework statement gives different mass, area, or density, those values replace these defaults in `config.py`. The program prints the values it is using when it starts.
