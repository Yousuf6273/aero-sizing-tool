# aerosizing — aircraft performance/sizing and rocket trajectory tool

A small, tested Python package for **fixed-wing aircraft performance and preliminary sizing** and
**rocket performance and trajectory**, sharing one standard-atmosphere and numerics layer.
Built as an engineering portfolio project: every equation is the standard textbook formulation
with a citation, every subsystem has a worked example with real numbers, and limiting cases are
covered by `pytest`.

## Problem statement

Given a mission (range, payload, cruise and stall speeds, climb, take-off distance, ceiling), what
wing loading, power loading, wing area and take-off mass does a light aircraft need, and how does
an existing aircraft perform? Given a motor and airframe, how high and fast does a rocket fly, and
how does propellant mass trade against altitude? The tool answers both with transparent,
verifiable models rather than black-box CFD or optimisation.

## What is implemented

| Module | Content | Primary sources |
|---|---|---|
| `atmosphere.py` | ISA / U.S. Standard Atmosphere 1976, 0–86 km: T, p, ρ, a, μ; geometric↔geopotential | NASA-TM-X-74335 eqs. 18, 23–25, 33a/b, 51 |
| `aerodynamics.py` | Parabolic drag polar, (L/D)max, min-power C_L, lifting-line lift-curve slope, Oswald estimate, L/D vs airspeed | Anderson *Intro. to Flight* §5.14–5.15; Raymer eq. 12.48 |
| `aircraft_performance.py` | Thrust/power required vs available (piston-prop with Gagg–Ferrar lapse, electric, turbojet), stall speed, max speed (brentq), rate of climb, service/absolute ceiling, Breguet range & endurance (prop and jet) | Anderson *Intro. to Flight* Ch. 6; *Aircraft Performance & Design* Ch. 5 |
| `sizing.py` | Constraint (matching) diagram: stall, cruise, climb, take-off ground roll, ceiling → design W/S and P/W; Raymer mission-fraction fuel sizing and take-off-mass fixed point | Raymer Ch. 3 (eqs. 3.4, 3.11, Table 3.2), Ch. 5; Gudmundsson Ch. 3 (eqs. 3-3, 3-4, 3-9) |
| `rocket.py` | Tsiolkovsky Δv, mass ratio / propellant fraction / propellant for Δv, serial staging, thrust (momentum + pressure), ideal nozzle exit velocity, area ratio, C_F, c*, thrust-curve `Motor` model with consistent mass flow | Sutton & Biblarz 9th ed. eqs. 2-1, 2-3, 2-14, 3-16, 3-25, 3-30, 3-32, 4-6; NASA Glenn |
| `trajectory.py` | 2-D point-mass launch (rail → zero-lift gravity turn), thrust + drag + gravity + variable mass, `solve_ivp` RK45 with apogee/impact events; fixed-step RK4 for cross-checks; analytic drag-free solution | Sutton §4.2–4.3 |
| `plots.py` | Matplotlib figures for all of the above | — |

Full equation list with units, assumptions and validity ranges: [`docs/theory.md`](docs/theory.md).
Curriculum research (TUM Aerospace B.Sc., TU Delft BSc Mechanical Engineering) and the mapping
of tool components to specific modules: [`docs/curriculum_mapping.md`](docs/curriculum_mapping.md).

## Worked examples (real numbers)

| Case | Script | Headline result |
|---|---|---|
| Cessna 172S-like performance | `examples/cessna172_performance.py` | Vs 52 kt (POH ≈ 53), Vmax 128 kt (≈ 126), R/C 1225 ft/min (730), ceiling 19 000 ft (14 000); with η_p = 0.60 in climb: 806 ft/min and 14 300 ft. The climb/ceiling gap is traced to the constant-η_p assumption and discussed in the notebook. |
| Survey UAV sizing | `examples/uav_sizing.py` | 4 kg payload, 150 km + 30 min loiter → W/S 168 N/m², P/W 7.5 W/N (climb governs), W0 ≈ 13 kg, S 0.77 m², b 2.6 m, ~1 kW engine |
| Mid-power rocket (AeroTech G80-class, 725 g pad mass) | `examples/model_rocket_trajectory.py` | Isp 223 s, ideal Δv 197 m/s, burnout 162 m/s (M 0.48, 16 g), apogee 830 m at 12.2 s; drag removes 54 % of the drag-free apogee |
| Trade studies | `examples/trade_studies.py` | AR 7→13 raises Breguet range ≈ 23 % with diminishing returns; propellant fraction vs Δv for Isp 250–450 s; apogee vs propellant mass shows falling marginal altitude per gram |

The notebook [`notebooks/walkthrough.ipynb`](notebooks/walkthrough.ipynb) walks through all cases
with plots and commentary written for a reviewer (committed with outputs).

## How to run

```bash
git clone https://github.com/Yousuf6273/aero-sizing-tool.git
cd aero-sizing-tool
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q                                              # 43 tests, ~3 s
python examples/run_all.py                             # prints results, writes figures/*.png
jupyter notebook notebooks/walkthrough.ipynb           # optional
```

Minimal API use:

```python
from aerosizing import aircraft_performance as ap, rocket as rk, trajectory as tj
ac = ap.Aircraft("C172", mass=1157, S=16.17, AR=7.32, e=0.75, CD0=0.033, CL_max=1.6,
                 propulsion=ap.PistonProp(134e3, 0.78), c_p=7.6e-8, fuel_mass=144)
ap.performance_summary(ac, h_cruise=2438)
m = rk.Motor.trapezoid("G80", total_impulse=136.6, burn_time=1.7, peak_thrust=116, propellant_mass=0.0625, casing_mass=0.0625)
tj.simulate(tj.RocketVehicle("rocket", 0.6, m, Cd=0.45, ref_area=2.29e-3), launch_angle_deg=5).apogee
```

## Verification

`tests/` (pytest) check limiting and hand-calculated cases:
ISA against the USSA-1976 table at eight altitudes (< 0.03 %); (L/D)max and min-power C_L against
numerical maxima; max speed as the exact P_A = P_R root; service ceiling at 0.508 m/s; Breguet
range against a hand calculation; constraint-curve minima (cruise T/W minimum = 1/(L/D)max);
take-off constraint hand calculation; fixed-point take-off mass in closed form; Tsiolkovsky
hand case; Isp = c*·C_F/g0 = v_e/g0 identity for optimum expansion; motor impulse/mass
bookkeeping; drag-free trajectory vs analytic speed and ballistic apogee; RK4 vs RK45 agreement.
A GitHub Actions workflow that runs the tests and all examples on Python 3.10 and 3.12 is
provided in `ci/github-actions-tests.yml`; enable it by moving it to `.github/workflows/tests.yml`
(this needs a token with the `workflow` scope, e.g. `gh auth refresh -s workflow`).

## Assumptions and limits (short)

Incompressible drag polar (M < ~0.6); constant propeller efficiency and SFC; Gagg–Ferrar lapse
for normally-aspirated pistons; conceptual-level sizing (±10–15 %); ideal-rocket nozzle
relations; constant C_D, flat Earth, no wind, no lift in the trajectory. See `docs/theory.md`.

## Future work (deliberately not built yet)

- Propeller efficiency map η_p(J, C_P) for fixed-pitch props (largest error found in the C172 case).
- Mach-dependent C_D(M) tables and wind for the rocket trajectory; parachute descent phase.
- Wing structural mass model to close the aspect-ratio trade (span² penalty).
- Electric-aircraft range/endurance (battery specific energy) in the sizing module.
- Optimisation over the constraint diagram, Monte-Carlo uncertainty on Isp/C_D, multi-objective
  (range vs mass) Pareto fronts — only once the above core models are validated.

## Layout

```
aerosizing/        package (atmosphere, aerodynamics, aircraft_performance, sizing, rocket, trajectory, numerics, plots)
examples/          worked cases + trade studies (run_all.py runs everything)
notebooks/         walkthrough.ipynb (+ build_notebook.py that generates it)
tests/             pytest suite
docs/              theory.md (equations & sources), curriculum_mapping.md (Phase 0 research)
ci/                GitHub Actions workflow (move to .github/workflows/ to enable)
figures/           generated by the examples (git-ignored)
```

## References

- NOAA/NASA/USAF, *U.S. Standard Atmosphere, 1976*, NASA-TM-X-74335.
- J. D. Anderson, *Introduction to Flight*, 8th ed., McGraw-Hill, 2016.
- J. D. Anderson, *Aircraft Performance and Design*, McGraw-Hill, 1999.
- D. P. Raymer, *Aircraft Design: A Conceptual Approach*, 6th ed., AIAA, 2018.
- S. Gudmundsson, *General Aviation Aircraft Design*, Butterworth-Heinemann, 2014.
- G. P. Sutton, O. Biblarz, *Rocket Propulsion Elements*, 9th ed., Wiley, 2017.
- NASA Glenn Research Center, *Beginner's Guide to Rockets* (rocket thrust and ideal rocket equation pages).
- Motor data: thrustcurve.org catalogue values for the AeroTech G80 (curve shape idealised).

License: MIT.
