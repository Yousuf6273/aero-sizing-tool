# Theory notes: governing equations, units, sources, assumptions, validity

All quantities SI unless stated. `g0 = 9.80665 m/s²`. Sources are abbreviated:

- **[USSA76]** NOAA/NASA/USAF, *U.S. Standard Atmosphere, 1976*, NASA-TM-X-74335 (identical to ISA / ISO 2533 below 32 km).
- **[AndIF]** J. D. Anderson, *Introduction to Flight*, 8th ed., McGraw-Hill, 2016 (Ch. 5 Airfoils/Wings, Ch. 6 Elements of Airplane Performance).
- **[AndAPD]** J. D. Anderson, *Aircraft Performance and Design*, McGraw-Hill, 1999 (Ch. 2–6).
- **[Raymer]** D. P. Raymer, *Aircraft Design: A Conceptual Approach*, 6th ed., AIAA, 2018 (Ch. 3 Sizing from a conceptual sketch, Ch. 5 Thrust-to-weight and wing loading, Ch. 12 Aerodynamics).
- **[Gud]** S. Gudmundsson, *General Aviation Aircraft Design*, Butterworth-Heinemann, 2014 (Ch. 3 Initial sizing / constraint diagram).
- **[Sutton]** G. P. Sutton, O. Biblarz, *Rocket Propulsion Elements*, 9th ed., Wiley, 2017 (Ch. 2 Definitions, Ch. 3 Nozzle theory, Ch. 4 Flight performance).
- **[NASA-GRC]** NASA Glenn Research Center, *Beginner's Guide to Aeronautics / Rockets* (Rocket thrust equation, Ideal rocket equation pages).

---

## 1. Atmosphere (`atmosphere.py`)

Hydrostatic equilibrium with the ideal-gas law in piecewise-linear temperature layers **[USSA76, eqs. 23–25, 33a/33b]**:

```
dp/dH = -rho g0,   p = rho R T,   T(H) = T_b + L_b (H - H_b)
L_b != 0:  p = p_b [T/T_b]^(-g0/(L_b R))
L_b == 0:  p = p_b exp(-g0 (H - H_b)/(R T_b))
a = sqrt(gamma R T),   mu = 1.458e-6 T^1.5/(T + 110.4)   (Sutherland, [USSA76 eq. 51])
```

Geopotential altitude from geometric: `H = r_E h/(r_E + h)`, `r_E = 6 356 766 m` [USSA76 eq. 18].
Constants: `R = 287.05287 J/(kg K)`, `gamma = 1.4`, `T0 = 288.15 K`, `p0 = 101 325 Pa`.
Layer bases (geopotential, m): 0, 11 000, 20 000, 32 000, 47 000, 51 000, 71 000, 84 852; lapse
rates (K/m): −6.5e-3, 0, 1.0e-3, 2.8e-3, 0, −2.8e-3, −2.0e-3.

Assumptions: dry air, constant composition, constant g0 in geopotential coordinates, no
weather. Validity: 0–86 km geometric (above that the 1976 model changes formulation).

## 2. Aerodynamics (`aerodynamics.py`)

Parabolic drag polar [AndIF §5.14–5.15, AndAPD §2.7]:

```
C_D = C_D0 + k C_L²,   k = 1/(pi e AR)
(L/D)max = 1/(2 sqrt(C_D0 k))   at C_L* = sqrt(C_D0/k)
max C_L^1.5/C_D (min power)     at C_L = sqrt(3 C_D0/k)
```

Finite-wing lift-curve slope (incompressible, Prandtl lifting-line correction) [AndIF §5.15]:
`a = a0 / (1 + a0/(pi e1 AR))`, `a0 ≈ 2 pi rad⁻¹` (thin airfoil).
Oswald efficiency estimate for straight wings [Raymer eq. 12.48]: `e = 1.78(1 − 0.045 AR^0.68) − 0.64`.
Required lift coefficient in steady level flight: `C_L = 2 W/(rho V² S)`.

Variables: `C_D0` [-] zero-lift drag coefficient, `AR = b²/S` [-], `e` [-], `S` [m²], `W` [N].
Assumptions: subsonic, attached flow, drag due to lift purely quadratic, no compressibility
(valid for M < ~0.6), no wave drag. Validity: below C_Lmax; polar is inaccurate near stall.

## 3. Aircraft performance (`aircraft_performance.py`)

Steady level flight, thrust/power required [AndIF §6.2–6.6]:

```
T_R = W/(L/D) = q S C_D,   P_R = T_R V
Prop: P_A = eta_p P_shaft,   T_A = P_A/V
Stall: V_s = sqrt(2 W/(rho S C_Lmax))                        [AndIF §6.6]
Rate of climb: R/C = (P_A − P_R)/W  (small-angle, unaccelerated) [AndIF §6.8]
Service ceiling: altitude where max R/C = 0.508 m/s (100 ft/min) [AndIF §6.10]
Max speed: root of P_A(rho) − P_R(V, rho) = 0 (scipy brentq)
```

Jet/turbofan thrust lapse: `T/T_SL = σ^m`, with `m = 1` for turbojets [AndIF §6.7] and
`m ≈ 0.7–0.8` commonly used for low-bypass turbofans. Jet aircraft cruise for **range** at
max `C_L^0.5/C_D` and loiter for **endurance** at `(L/D)max` — the opposite of propeller
aircraft [AndIF §6.12–6.13].

Piston-engine power lapse with density ratio σ [Gagg & Ferrar correlation as given in Raymer
Ch. 13 and Gudmundsson Ch. 7]: `P/P_SL = 1.132 σ − 0.132`. Jet thrust lapse `T/T_SL = σ` [AndIF §6.7].

Breguet range and endurance [AndIF §6.12–6.13, AndAPD Ch. 5]. `c_p` is power-specific fuel
consumption in **kg/(W s)**, `c_t` thrust-specific in **1/s** (kg fuel per N-s ÷ ... i.e. N/(N s)):

```
Prop:  R = eta_p/(g0 c_p) (L/D) ln(W0/W1)
       E = eta_p/(g0 c_p) (C_L^1.5/C_D) sqrt(2 rho S) (W1^-1/2 − W0^-1/2)
Jet:   R = 2 sqrt(2/(rho S)) (1/c_t) (C_L^1/2/C_D) (W0^1/2 − W1^1/2)
       E = (1/c_t)(L/D) ln(W0/W1)
```

Assumptions: constant η_p, c_p, altitude and C_L over the segment (classic Breguet).
For transonic and supersonic aircraft the incompressible polar has no wave drag, so top
speed, climb rate and ceiling are **over-predicted**; the tool warns above Mach 0.7.
Validity: light subsonic aircraft; propeller efficiency treated constant, which over-predicts
climb and ceiling for fixed-pitch propellers (discussed in the Cessna 172 example).

## 4. Preliminary sizing (`sizing.py`)

Constraint (matching) diagram in the (W/S, T/W) plane [Raymer Ch. 5; Gudmundsson Ch. 3].
Each requirement gives the minimum T/W as a function of wing loading `W/S` [N/m²]:

```
Stall:     W/S <= 0.5 rho V_s² C_Lmax                                   [Raymer eq. 5.6]
Cruise:    T/W = q C_D0/(W/S) + k (W/S)/q                                [Gud eq. 3-4]
Climb:     T/W = V_v/V + q C_D0/(W/S) + k (W/S)/q                        [Gud eq. 3-3]
Take-off:  T/W = 1.21 (W/S)/(g0 rho C_Lmax,TO S_G) + 0.605/C_Lmax,TO (C_D,TO − mu C_L,TO) + mu   [Gud eq. 3-9]
Ceiling:   climb constraint evaluated at ceiling density with V_v = 0.508 m/s
Prop conversion: P/W = (T/W) V/eta_p, then divided by the power lapse to get sea-level shaft power
```

The design point is the largest allowable W/S (stall limit) and the smallest P/W that
satisfies every curve there (largest engine-fraction constraint governs).

Mission weight sizing [Raymer Ch. 3, eqs. 3.1–3.11, Table 3.2]:

```
W0 = W_payload / (1 − W_f/W0 − W_e/W0)
W_f/W0 = 1.06 (1 − Π_i W_i/W_{i−1})     (6 % reserve + trapped fuel)
Segment fractions: warm-up/take-off 0.970, climb 0.985, landing 0.995,
cruise  W_i/W_{i−1} = exp(−R g0 c_p /(eta_p (L/D)))     (Breguet inverted)
loiter  W_i/W_{i−1} = exp(−E V g0 c_p /(eta_p (L/D)))
```

Solved as a fixed point in W0 with scipy `brentq`. `W_e/W0` is either constant (user
estimate) or Raymer's statistical fit `A W0^C`. Assumptions: conceptual level, ±10–15 %.

## 5. Rocket propulsion (`rocket.py`)

```
Tsiolkovsky:  Δv = I_sp g0 ln(m0/mf)                              [Sutton eq. 4-6; NASA-GRC "Ideal rocket equation"]
Propellant mass fraction for Δv:  ζ = 1 − exp(−Δv/(I_sp g0))
Thrust:  F = ṁ v_e + (p_e − p_a) A_e = ṁ I_sp g0 (effective)      [Sutton eq. 2-14; NASA-GRC "Rocket thrust equation"]
Total impulse: I_t = ∫F dt,  I_sp = I_t/(m_p g0)                  [Sutton eqs. 2-1, 2-3]
Ideal nozzle exit velocity (isentropic, ideal gas):
  v_e = sqrt( 2γ/(γ−1) R T_c [1 − (p_e/p_c)^((γ−1)/γ)] )          [Sutton eq. 3-16]
Area ratio:  A_e/A_t = ((γ+1)/2)^(−1/(γ−1)) (p_c/p_e)^(1/γ) / sqrt((γ+1)/(γ−1)[1−(p_e/p_c)^((γ−1)/γ)])   [Sutton eq. 3-25]
Thrust coefficient: C_F = sqrt( 2γ²/(γ−1) (2/(γ+1))^((γ+1)/(γ−1)) [1−(p_e/p_c)^((γ−1)/γ)] ) + (p_e−p_a)/p_c · A_e/A_t   [Sutton eq. 3-30]
Characteristic velocity:  c* = sqrt(γ R T_c) / ( γ sqrt( (2/(γ+1))^((γ+1)/(γ−1)) ) )   [Sutton eq. 3-32]
Multistage: Δv_total = Σ I_sp,i g0 ln(m0,i/mf,i)                  [Sutton §4.7]
```

Units: `I_sp` [s], `m` [kg], `ṁ` [kg/s], `p` [Pa], `A` [m²], `T_c` [K], `R` [J/(kg K)].
Assumptions: ideal rocket (1-D, isentropic, frozen composition, perfect gas), I_sp constant
over a burn. Validity: conceptual estimates; real motors have 2–5 % losses.

## 6. Trajectory (`trajectory.py`)

Point-mass, planar (x horizontal, z up), thrust along the velocity vector after the
launch rail (zero angle of attack — a gravity turn), quadratic drag, ISA density
[Sutton §4.2–4.3; AndIF Ch. 6 for the drag term]:

```
dx/dt = v_x,  dz/dt = v_z
m dv/dt = F(t) û_v − ½ rho(z) |v|² C_D A û_v − m g0 ẑ
m(t) = m_dry + m_motor(t),  dm/dt = −F(t)/(I_sp g0)
```

Integrated with scipy `solve_ivp` (RK45, rtol 1e-8) with terminal events for apogee
(`v_z = 0`) and impact (`z = 0`); cross-checked in tests against a hand-written classical
RK4 and against the drag-free analytic solution `v(t) = c ln(m0/m(t)) − g0 t`.
Assumptions: flat Earth, constant g0, no wind, constant C_D (no Mach dependence), no
lift. Validity: low-altitude, subsonic-to-low-supersonic model/high-power rockets.
