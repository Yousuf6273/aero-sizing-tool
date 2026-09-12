"""Preliminary sizing: constraint (matching) diagram and mission weight sizing.

Sources
-------
- Raymer, *Aircraft Design: A Conceptual Approach*, 6th ed.: Ch. 3 (eqs. 3.1-3.11,
  Table 3.2 mission segment fractions, Table 3.1 empty-weight fits), Ch. 5 (W/S, T/W).
- Gudmundsson, *General Aviation Aircraft Design*, Ch. 3, eqs. 3-3 (climb), 3-4 (cruise),
  3-9 (take-off ground roll).

The constraint diagram gives, for each wing loading W/S [N/m^2], the minimum
thrust-to-weight T/W [-] (or power-to-weight P/W [W/N]) that meets each requirement.
The design point is the highest W/S allowed by the stall constraint and the highest
P/W demanded by any other constraint there.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.optimize import brentq

from .aerodynamics import DragPolar, dynamic_pressure, velocity_for_CL
from .aircraft_performance import piston_power_lapse
from .atmosphere import G0, RHO0, density

# Raymer Table 3.2 historical mission-segment weight fractions
SEGMENT_FRACTIONS = {"warmup_takeoff": 0.970, "climb": 0.985, "landing": 0.995}
RESERVE_FACTOR = 1.06    # Raymer eq. 3.11: 6 % for reserves + trapped fuel


@dataclass(frozen=True)
class MissionRequirements:
    range_m: float                 # cruise range [m]
    payload_mass: float            # [kg]
    cruise_speed: float            # true airspeed [m/s]
    cruise_altitude: float         # [m]
    stall_speed: float             # sea-level, clean or with flaps as per CL_max used [m/s]
    climb_rate_SL: float           # required rate of climb at sea level [m/s]
    takeoff_ground_roll: float     # [m]
    service_ceiling: float         # [m]
    loiter_time_s: float = 0.0     # [s]


@dataclass(frozen=True)
class DesignAssumptions:
    CD0: float
    AR: float
    e: float
    CL_max: float                  # for the stall constraint
    CL_max_TO: float               # take-off configuration
    eta_p: float                   # cruise/climb propeller efficiency
    c_p: float                     # kg/(W s)
    eta_p_TO: float = 0.6          # propeller efficiency at ~0.7 V_LOF
    mu_roll: float = 0.04          # rolling friction, dry concrete/asphalt (Raymer Table 17.1)
    CD0_TO_increment: float = 0.02 # flaps + gear drag increment at take-off
    CL_TO_ground: float = 0.5      # C_L during ground roll (Gudmundsson: ~0.5 typical)
    empty_mass_fraction: float | Callable[[float], float] = 0.55
    loiter_LD_factor: float = 0.866   # L/D at loiter relative to (L/D)max for props (Raymer Sec. 3.4)

    @property
    def polar(self) -> DragPolar:
        return DragPolar(self.CD0, self.AR, self.e)


@dataclass
class ConstraintCurves:
    WS: np.ndarray                          # wing loading grid [N/m^2]
    PW: dict = field(default_factory=dict)  # name -> P/W [W/N] (sea-level shaft power) on grid
    WS_stall_max: float = np.nan


# ---------------------------------------------------------------------------
# individual constraints (return T/W as a function of W/S)
# ---------------------------------------------------------------------------
def stall_wing_loading_limit(V_s: float, CL_max: float, rho: float = RHO0) -> float:
    """Raymer eq. 5.6: W/S <= 0.5 rho V_s^2 C_Lmax."""
    return 0.5 * rho * V_s ** 2 * CL_max


def tw_cruise(WS, V: float, rho: float, polar: DragPolar):
    """Gudmundsson eq. 3-4: T/W = q C_D0/(W/S) + k (W/S)/q."""
    q = dynamic_pressure(rho, V)
    return q * polar.CD0 / WS + polar.k * WS / q


def tw_climb(WS, V: float, rho: float, polar: DragPolar, V_v: float):
    """Gudmundsson eq. 3-3: T/W = V_v/V + q C_D0/(W/S) + k (W/S)/q."""
    q = dynamic_pressure(rho, V)
    return V_v / V + q * polar.CD0 / WS + polar.k * WS / q


def tw_takeoff(WS, S_G: float, rho: float, CL_max_TO: float, CD_TO: float, CL_TO: float, mu: float):
    """Gudmundsson eq. 3-9 (ground roll to lift-off at V_LOF = 1.1 V_s,TO)."""
    return (1.21 * WS / (G0 * rho * CL_max_TO * S_G)
            + 0.605 / CL_max_TO * (CD_TO - mu * CL_TO) + mu)


def climb_speed_for_min_power(WS, rho: float, polar: DragPolar):
    """Speed at C_L for minimum power required (best R/C for props), per wing loading."""
    return np.sqrt(2.0 * WS / (rho * polar.CL_min_power))


# ---------------------------------------------------------------------------
# constraint diagram
# ---------------------------------------------------------------------------
def constraint_diagram(req: MissionRequirements, da: DesignAssumptions,
                       WS: np.ndarray | None = None) -> ConstraintCurves:
    """Build all constraint curves in terms of required sea-level shaft P/W [W/N]."""
    polar = da.polar
    if WS is None:
        WS = np.linspace(50.0, 3000.0, 600)
    cc = ConstraintCurves(WS=WS)
    cc.WS_stall_max = stall_wing_loading_limit(req.stall_speed, da.CL_max)

    # cruise at altitude: P/W = T/W V / eta_p, then back to SL shaft power via lapse
    rho_c = density(req.cruise_altitude)
    tw = tw_cruise(WS, req.cruise_speed, rho_c, polar)
    cc.PW["cruise"] = tw * req.cruise_speed / da.eta_p / piston_power_lapse(rho_c / RHO0)

    # climb at sea level at the min-power speed for each W/S
    Vc = climb_speed_for_min_power(WS, RHO0, polar)
    tw = tw_climb(WS, Vc, RHO0, polar, req.climb_rate_SL)
    cc.PW["climb"] = tw * Vc / da.eta_p

    # take-off ground roll (sea level). Power converted at 0.707 V_LOF with eta_p_TO
    CD_TO = da.CD0 + da.CD0_TO_increment + polar.k * da.CL_TO_ground ** 2
    tw = tw_takeoff(WS, req.takeoff_ground_roll, RHO0, da.CL_max_TO, CD_TO, da.CL_TO_ground, da.mu_roll)
    V_LOF = 1.1 * np.sqrt(2.0 * WS / (RHO0 * da.CL_max_TO))
    cc.PW["takeoff"] = tw * (V_LOF / np.sqrt(2.0)) / da.eta_p_TO

    # service ceiling: R/C = 0.508 m/s at ceiling density, min-power speed there
    rho_ce = density(req.service_ceiling)
    Vce = climb_speed_for_min_power(WS, rho_ce, polar)
    tw = tw_climb(WS, Vce, rho_ce, polar, 0.508)
    cc.PW["ceiling"] = tw * Vce / da.eta_p / piston_power_lapse(rho_ce / RHO0)
    return cc


def design_point(cc: ConstraintCurves, WS_cap: float | None = None) -> tuple[float, float, str]:
    """Return (W/S, P/W, governing constraint) at the stall-limited wing loading."""
    WS_d = cc.WS_stall_max if WS_cap is None else min(cc.WS_stall_max, WS_cap)
    vals = {name: float(np.interp(WS_d, cc.WS, pw)) for name, pw in cc.PW.items()}
    gov = max(vals, key=vals.get)
    return float(WS_d), vals[gov], gov


# ---------------------------------------------------------------------------
# mission weight sizing (Raymer Ch. 3)
# ---------------------------------------------------------------------------
def cruise_fraction(range_m: float, c_p: float, eta_p: float, LD: float) -> float:
    """Breguet inverted: W_i/W_{i-1} = exp(-R g0 c_p/(eta_p L/D))."""
    return float(np.exp(-range_m * G0 * c_p / (eta_p * LD)))


def loiter_fraction(E_s: float, V: float, c_p: float, eta_p: float, LD: float) -> float:
    """Prop loiter: W_i/W_{i-1} = exp(-E V g0 c_p/(eta_p L/D))."""
    return float(np.exp(-E_s * V * G0 * c_p / (eta_p * LD)))


def fuel_fraction(req: MissionRequirements, da: DesignAssumptions, LD_cruise: float) -> float:
    """Raymer eq. 3.11: W_f/W0 = 1.06 (1 - product of segment fractions)."""
    prod = SEGMENT_FRACTIONS["warmup_takeoff"] * SEGMENT_FRACTIONS["climb"]
    prod *= cruise_fraction(req.range_m, da.c_p, da.eta_p, LD_cruise)
    if req.loiter_time_s > 0:
        LD_loiter = da.polar.LD_max * da.loiter_LD_factor
        V_loiter = 0.76 * req.cruise_speed   # conservative; loiter near min-power speed
        prod *= loiter_fraction(req.loiter_time_s, V_loiter, da.c_p, da.eta_p, LD_loiter)
    prod *= SEGMENT_FRACTIONS["landing"]
    return RESERVE_FACTOR * (1.0 - prod)


def takeoff_mass(payload: float, ff: float, empty_fraction, m_lo: float = 0.5, m_hi: float = 1e6) -> float:
    """Solve W0 = W_pay/(1 - W_f/W0 - W_e/W0) for W0 (Raymer eq. 3.4) with brentq.

    ``empty_fraction`` may be a constant or a callable of take-off mass [kg]."""
    ef = (lambda m: empty_fraction) if not callable(empty_fraction) else empty_fraction
    g = lambda m: m - payload / (1.0 - ff - ef(m))  # noqa: E731
    return float(brentq(g, m_lo, m_hi, xtol=1e-6))


def raymer_empty_fraction_ga_single(m0_kg: float) -> float:
    """Raymer Table 3.1, 'General aviation - single engine': We/W0 = 2.36 W0^-0.18 (W0 in lb)."""
    W0_lb = m0_kg * 2.20462
    return 2.36 * W0_lb ** -0.18


@dataclass
class SizingResult:
    wing_loading: float        # N/m^2
    power_to_weight: float     # W/N (sea-level shaft)
    governing_constraint: str
    takeoff_mass: float        # kg
    fuel_mass: float           # kg
    empty_mass: float          # kg
    wing_area: float           # m^2
    span: float                # m
    shaft_power: float         # W
    LD_cruise: float
    CL_cruise: float
    curves: ConstraintCurves


def size_aircraft(req: MissionRequirements, da: DesignAssumptions, WS_cap: float | None = None) -> SizingResult:
    """End-to-end conceptual sizing: constraint diagram -> W/S, P/W; mission -> W0; then S, P."""
    cc = constraint_diagram(req, da)
    WS_d, PW_d, gov = design_point(cc, WS_cap)

    # cruise C_L and L/D follow from W/S and cruise q (consistent with the diagram)
    q_c = dynamic_pressure(density(req.cruise_altitude), req.cruise_speed)
    CL_c = WS_d / q_c
    LD_c = float(da.polar.L_over_D(CL_c))

    ff = fuel_fraction(req, da, LD_c)
    m0 = takeoff_mass(req.payload_mass, ff, da.empty_mass_fraction)
    ef = da.empty_mass_fraction(m0) if callable(da.empty_mass_fraction) else da.empty_mass_fraction
    S = m0 * G0 / WS_d
    return SizingResult(WS_d, PW_d, gov, m0, ff * m0, ef * m0, S, float(np.sqrt(da.AR * S)),
                        PW_d * m0 * G0, LD_c, float(CL_c), cc)
