# Curriculum mapping (Phase 0 research)

Purpose: decide which competencies from the two target programmes a computational
sizing/performance tool can credibly demonstrate. This note guided the design
decisions in the tool; it is context, not the deliverable.

## Sources actually consulted

| Programme | Document | Access |
|---|---|---|
| TUM Aerospace B.Sc. | *Module Catalog B.Sc. Aerospace* (English, generated 23 Aug 2021, TUM Dept. of Aerospace and Geodesy) | PDF downloaded and text-extracted |
| TUM Aerospace B.Sc. | *Modulhandbuch B.Sc. Aerospace SPO 2025-01*, WiSe 2025/26 (generated 15 Dec 2025) | PDF downloaded; used to confirm that the required-module list (LRG codes) is unchanged and to pick up newer electives (e.g. MW1907 *Introduction to Flight Mechanics and Control*) |
| TUM Aerospace B.Sc. | Programme page, TUM School of Engineering and Design | Web page |
| TU Delft BSc Werktuigbouwkunde | *Modulekaart BSc-Wb 2025-2026* (official one-page course card, ME faculty) | PDF downloaded and text-extracted |
| TU Delft BSc Werktuigbouwkunde | "Wat leer je bij Werktuigbouwkunde?" programme page (Dutch) and TU Delft OpenCourseWare course list | Web pages |

Limitations, stated honestly: the TU Delft study guide (studiegids.tudelft.nl) is a
dynamic site whose per-course pages could not be fetched in this session, so the Delft
mapping uses course codes/names from the official Modulekaart plus the programme
description page, not the full course descriptions. The TUM learning outcomes quoted
below are from the 2021 English catalogue; the 2025/26 German handbook lists the same
required modules with the same codes.

## TUM Aerospace B.Sc. — required modules relevant to this tool

Required modules (semesters 1–4) include: LRG0010/0011/0012 Engineering Mechanics I–III
(Statics, Structural Mechanics Modeling, Dynamics); LRG0030/0031 Thermodynamics I/II;
LRG0070/0071 Fluid Mechanics I/II; LRG0060/0061 Computational Foundations I/II;
MA9801–MA9803 Mathematics incl. *Modeling and Simulation with ODEs*; LRG0050 Aerospace
Structures and Elements; LRG0090 Test, Analysis, and Simulation; LRG0202 Engineering
Project. System electives (semester 4): LRG0100 Aircraft Design Basics, LRG0102 Basics of
Propulsion Systems, LRG0103 Basics in Space Technology. Lab courses: LRG0120 Design/Build/Fly.

## TU Delft BSc Mechanical Engineering — courses relevant to this tool

Year 1: WBMT1050 Wiskunde 1 (Analyse 1/2), WBMT1051 Wiskunde 2 (Lineaire Algebra 1/2),
WB1631 Statica, WB1641 Sterkteleer, WB1135 Introductory Dynamics, WB1530 Thermofluids,
WB1642/1643 Werktuigkundig Ontwerpproject 1–3 (design projects incl. Python programming).
Year 2: WBMT2048 Wiskunde 3 (Analyse / Differentiaalvergelijkingen), WBMT2049 Wiskunde 4
(Kansrekening & Statistiek / Numerieke Wiskunde), WB2630 Rigid-Body Dynamics / Continuum
Mechanics, WB2542 Stromingsleer / Warmte-overdracht, WB2543 Process Engineering &
Thermodynamics, WB2330 Materiaalkunde, WB2632 Project Mechanica (AED & FEM).
Year 3: WB3240 Systeem- en Regeltechniek, WB3135 Integrated Mechanical Systems, BEP.

## Mapping: tool component → competency → why

| Tool component | TUM module (code) | TU Delft course (code) | Why it is relevant |
|---|---|---|---|
| `atmosphere.py` — ISA layered model, hydrostatic + ideal-gas integration | Thermodynamics I (LRG0030): state variables, ideal gas; Fluid Mechanics I (LRG0070): hydrostatics, gas dynamics (speed of sound) | Thermofluids (WB1530), Thermodynamics (WB2543) | Hydrostatic equation + ideal gas law integrated layer-by-layer is a direct application of first-semester thermofluids. |
| `aerodynamics.py` — drag polar, lift-curve slope, L/D | Fluid Mechanics I/II (LRG0070/71): conservation laws, viscous and "technical flows"; Aircraft Design Basics (LRG0100): lift, drag, drag reduction | Stromingsleer (WB2542 T1) | Parasite + induced drag decomposition and finite-wing corrections are the standard bridge from fluid mechanics to aircraft performance. |
| `aircraft_performance.py` — thrust/power required vs available, climb, ceiling, Breguet | Engineering Mechanics III – Dynamics (LRG0012): kinetics of point masses; Aircraft Design Basics (LRG0100) | Introductory Dynamics (WB1135), Rigid-Body Dynamics (WB2630) | Steady-flight force balance and energy-rate (excess power) arguments are point-mass dynamics applied to a vehicle. |
| `sizing.py` — constraint diagram (W/S vs P/W), mission fuel-fraction weight sizing | Aircraft Design Basics (LRG0100): "mass estimation", "design process"; Engineering Project (LRG0202); Design/Build/Fly (LRG0120) | Werktuigkundig Ontwerpproject 1–3 (WB1642/1643): requirements → design → evaluate; Integrated Mechanical Systems (WB3135) | A real conceptual-design methodology (Raymer/Gudmundsson matching plot) shows requirement-driven design, not just analysis. |
| `rocket.py` — Tsiolkovsky, Isp, thrust, nozzle relations, staging | Basics in Space Technology (LRG0103): "basic rocket equation; specific impulse; staging"; Basics of Propulsion Systems (LRG0102): isentropic relations, engine cycle | Thermodynamics (WB2543): isentropic expansion, 1st law | The catalogue lists the rocket equation and Isp explicitly as LRG0103 content; nozzle exhaust velocity is an isentropic-flow calculation. |
| `trajectory.py` — 2-D point-mass rocket ODE, RK45 (scipy) and hand-written RK4 cross-check, event detection | Modeling and Simulation with ODEs (MA9803): "Runge-Kutta methods … numerical simulation"; Computational Foundations I/II (LRG0060/61) | Wiskunde 3 Differentiaalvergelijkingen (WBMT2048 T2), Wiskunde 4 Numerieke Wiskunde (WBMT2049 T2), Python in WOP | Formulating an IVP for a variable-mass vehicle and solving it numerically is exactly the stated MA9803 outcome. |
| `tests/` — limiting-case tests vs. standard tables / analytic solutions | Test, Analysis, and Simulation (LRG0090): "mathematical modelling … degree of abstraction", error sources | Onderzoeksmethodologie (WB1630) | Verification against known answers is the modelling discipline both programmes teach. |
| Trade studies (AR vs range; propellant fraction vs Δv) | Aircraft Design Basics (LRG0100) "trade-offs"; LRG0103 "trade offs structure vs. payload" | Ontwerpproject (WB1643), WB3135 | Design is choosing between alternatives with quantified consequences. |
