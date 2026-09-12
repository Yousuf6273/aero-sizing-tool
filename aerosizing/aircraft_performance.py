"""Fixed-wing aircraft performance: thrust/power required vs available, stall,
max/cruise speed, rate of climb, ceilings, Breguet range and endurance.

Sources
-------
- Anderson, *Introduction to Flight*, 8th ed., Ch. 6 (Secs. 6.2-6.13).
- Anderson, *Aircraft Performance and Design*, Ch. 5 (steady climb, ceilings, range).
- Gagg & Ferrar (1934) piston power lapse P/P_SL = 1.132 sigma - 0.132, as reproduced in
  Raymer (6th ed.) Ch. 13 and Gudmundsson Ch. 7.

Conventions: masses in kg, weights W = m g0 in N, speeds true airspeed in m/s,
altitudes geometric metres, shaft power in W, specific fuel consumption
c_p in kg/(W s) (power-specific) and c_t in 1/s (thrust-specific, kg/(N s) * g0).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from scipy.optimize import brentq, minimize_scalar

from .aerodynamics import DragPolar, dynamic_pressure, required_CL, velocity_for_CL
from .atmosphere import G0, RHO0, density

SERVICE_CEILING_RC = 0.508   # m/s (100 ft/min), Anderson Intro to Flight Sec. 6.10


# ---------------------------------------------------------------------------
# propulsion models
# ---------------------------------------------------------------------------
class Propulsion(Protocol):
    def power_available(self, V, rho): ...
    def thrust_available(self, V, rho): ...


def piston_power_lapse(sigma):
    """Gagg-Ferrar normally-aspirated piston lapse, clipped at zero."""
    return np.maximum(1.132 * np.asarray(sigma, dtype=float) - 0.132, 0.0)


@dataclass(frozen=True)
class PistonProp:
    """Normally aspirated piston engine driving a propeller of constant efficiency."""
    P_shaft_SL: float      # rated sea-level shaft power [W]
    eta_p: float = 0.8     # propeller efficiency [-] (assumed constant)

    def power_available(self, V, rho):
        return self.eta_p * self.P_shaft_SL * piston_power_lapse(np.asarray(rho) / RHO0)

    def thrust_available(self, V, rho):
        return self.power_available(V, rho) / np.asarray(V, dtype=float)


@dataclass(frozen=True)
class ElectricProp:
    """Electric motor + propeller: no altitude lapse on shaft power."""
    P_shaft: float
    eta_p: float = 0.8

    def power_available(self, V, rho):
        return self.eta_p * self.P_shaft * np.ones_like(np.asarray(rho, dtype=float))

    def thrust_available(self, V, rho):
        return self.power_available(V, rho) / np.asarray(V, dtype=float)


@dataclass(frozen=True)
class Turbojet:
    """Subsonic turbojet/turbofan: thrust independent of V, T = T_SL sigma^m."""
    T_SL: float          # sea-level static thrust [N]
    m: float = 1.0       # lapse exponent; Anderson uses sigma^1 for turbojets

    def thrust_available(self, V, rho):
        return self.T_SL * (np.asarray(rho, dtype=float) / RHO0) ** self.m * np.ones_like(np.asarray(V, dtype=float))

    def power_available(self, V, rho):
        return self.thrust_available(V, rho) * np.asarray(V, dtype=float)


# ---------------------------------------------------------------------------
# aircraft definition
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Aircraft:
    name: str
    mass: float            # take-off mass [kg]
    S: float               # wing reference area [m^2]
    AR: float              # aspect ratio [-]
    e: float               # Oswald efficiency [-]
    CD0: float             # zero-lift drag coefficient [-]
    CL_max: float          # clean maximum lift coefficient [-]
    propulsion: object     # PistonProp | ElectricProp | Turbojet
    c_p: float | None = None   # power-specific fuel consumption [kg/(W s)] (prop)
    c_t: float | None = None   # thrust-specific fuel consumption [1/s] (jet)
    fuel_mass: float = 0.0     # usable fuel [kg]
    polar: DragPolar = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "polar", DragPolar(self.CD0, self.AR, self.e))

    @property
    def W(self) -> float:
        return self.mass * G0

    @property
    def b(self) -> float:
        return float(np.sqrt(self.AR * self.S))

    @property
    def wing_loading(self) -> float:
        return self.W / self.S


# ---------------------------------------------------------------------------
# level-flight quantities
# ---------------------------------------------------------------------------
def stall_speed(ac: Aircraft, h: float = 0.0, CL_max: float | None = None, W: float | None = None) -> float:
    """V_s = sqrt(2W/(rho S C_Lmax)), Anderson Intro to Flight Sec. 6.6."""
    CL = ac.CL_max if CL_max is None else CL_max
    W = ac.W if W is None else W
    return float(velocity_for_CL(W, density(h), CL, ac.S))


def thrust_required(ac: Aircraft, V, h: float = 0.0, W: float | None = None):
    """T_R = q S C_D with C_L set by level flight."""
    W = ac.W if W is None else W
    rho = density(h)
    CL = required_CL(W, rho, V, ac.S)
    return dynamic_pressure(rho, V) * ac.S * ac.polar.CD(CL)


def power_required(ac: Aircraft, V, h: float = 0.0, W: float | None = None):
    return thrust_required(ac, V, h, W) * np.asarray(V, dtype=float)


def power_available(ac: Aircraft, V, h: float = 0.0):
    return ac.propulsion.power_available(V, density(h))


def thrust_available(ac: Aircraft, V, h: float = 0.0):
    return ac.propulsion.thrust_available(V, density(h))


def rate_of_climb(ac: Aircraft, V, h: float = 0.0, W: float | None = None):
    """R/C = (P_A - P_R)/W (unaccelerated, small climb angle), Anderson Sec. 6.8."""
    W = ac.W if W is None else W
    return (power_available(ac, V, h) - power_required(ac, V, h, W)) / W


def _speed_bracket(ac: Aircraft, h: float, W: float):
    """Speeds bracketing the P_A - P_R = 0 roots: from stall to a generous upper bound."""
    V_lo = stall_speed(ac, h, W=W)
    V_hi = 6.0 * V_lo
    return V_lo, V_hi


def max_rate_of_climb(ac: Aircraft, h: float = 0.0, W: float | None = None) -> tuple[float, float]:
    """Return (max R/C [m/s], speed for max R/C [m/s]) at altitude h.

    Uses a bounded scalar minimisation of -R/C between V_stall and 6 V_stall
    (scipy `minimize_scalar`, Brent method), seeded by a coarse grid to avoid
    converging to a local maximum for jet aircraft.
    """
    W = ac.W if W is None else W
    V_lo, V_hi = _speed_bracket(ac, h, W)
    Vg = np.linspace(V_lo, V_hi, 200)
    rc = rate_of_climb(ac, Vg, h, W)
    i = int(np.argmax(rc))
    a = Vg[max(i - 1, 0)]
    b = Vg[min(i + 1, len(Vg) - 1)]
    res = minimize_scalar(lambda V: -rate_of_climb(ac, V, h, W), bounds=(a, b), method="bounded")
    return float(-res.fun), float(res.x)


def max_speed(ac: Aircraft, h: float = 0.0, W: float | None = None) -> float:
    """Maximum level-flight speed: largest root of P_A(V) - P_R(V) = 0 (scipy brentq)."""
    W = ac.W if W is None else W
    V_lo, V_hi = _speed_bracket(ac, h, W)
    _, V_rc = max_rate_of_climb(ac, h, W)
    f = lambda V: power_available(ac, V, h) - power_required(ac, V, h, W)  # noqa: E731
    if f(V_rc) <= 0:
        raise ValueError(f"{ac.name}: insufficient power for level flight at h={h:.0f} m")
    return float(brentq(f, V_rc, V_hi, xtol=1e-6))


def min_speed_power_limited(ac: Aircraft, h: float = 0.0, W: float | None = None) -> float:
    """Lowest speed at which P_A >= P_R (may be below stall, in which case stall governs)."""
    W = ac.W if W is None else W
    V_lo, _ = _speed_bracket(ac, h, W)
    _, V_rc = max_rate_of_climb(ac, h, W)
    f = lambda V: power_available(ac, V, h) - power_required(ac, V, h, W)  # noqa: E731
    if f(V_lo) >= 0:
        return V_lo
    return float(brentq(f, V_lo, V_rc, xtol=1e-6))


def ceiling(ac: Aircraft, rc_min: float = SERVICE_CEILING_RC, W: float | None = None,
            h_max: float = 25000.0) -> float:
    """Altitude at which max R/C equals ``rc_min`` (0.508 m/s -> service ceiling,
    0 -> absolute ceiling). Solved with scipy brentq on max_rate_of_climb(h) - rc_min."""
    W = ac.W if W is None else W
    g = lambda h: max_rate_of_climb(ac, h, W)[0] - rc_min  # noqa: E731
    if g(0.0) <= 0:
        return 0.0
    # walk upward to find a sign change (climb capability decreases monotonically)
    hs = np.linspace(0.0, h_max, 26)
    prev = 0.0
    for h in hs[1:]:
        if g(h) <= 0:
            return float(brentq(g, prev, h, xtol=0.5))
        prev = h
    raise ValueError("ceiling above h_max")


def service_ceiling(ac: Aircraft, W: float | None = None) -> float:
    return ceiling(ac, SERVICE_CEILING_RC, W)


def absolute_ceiling(ac: Aircraft, W: float | None = None) -> float:
    return ceiling(ac, 0.0, W)


# ---------------------------------------------------------------------------
# Breguet range and endurance (Anderson Intro to Flight Secs. 6.12-6.13)
# ---------------------------------------------------------------------------
def breguet_range_prop(eta_p: float, c_p: float, LD: float, W0: float, W1: float) -> float:
    """R = eta_p/(g0 c_p) (L/D) ln(W0/W1)   [m];  c_p in kg/(W s)."""
    return eta_p / (G0 * c_p) * LD * np.log(W0 / W1)


def breguet_endurance_prop(eta_p: float, c_p: float, CL: float, CD: float, rho: float,
                           S: float, W0: float, W1: float) -> float:
    """E = eta_p/(g0 c_p) (C_L^1.5/C_D) sqrt(2 rho S) (W1^-1/2 - W0^-1/2)   [s]."""
    return eta_p / (G0 * c_p) * (CL ** 1.5 / CD) * np.sqrt(2.0 * rho * S) * (W1 ** -0.5 - W0 ** -0.5)


def breguet_range_jet(c_t: float, CL: float, CD: float, rho: float, S: float, W0: float, W1: float) -> float:
    """R = 2 sqrt(2/(rho S)) (1/c_t) (C_L^0.5/C_D) (W0^0.5 - W1^0.5)   [m];  c_t in 1/s."""
    return 2.0 * np.sqrt(2.0 / (rho * S)) / c_t * (CL ** 0.5 / CD) * (W0 ** 0.5 - W1 ** 0.5)


def breguet_endurance_jet(c_t: float, LD: float, W0: float, W1: float) -> float:
    """E = (1/c_t)(L/D) ln(W0/W1)   [s]."""
    return LD / c_t * np.log(W0 / W1)


def prop_range_endurance(ac: Aircraft, h: float = 0.0, fuel_mass: float | None = None) -> dict:
    """Best-case Breguet range (at (L/D)max) and endurance (at max C_L^1.5/C_D) for a
    propeller aircraft burning ``fuel_mass`` kg. Returns a dict with SI values."""
    if ac.c_p is None:
        raise ValueError("c_p required for propeller Breguet estimates")
    mf = ac.fuel_mass if fuel_mass is None else fuel_mass
    W0, W1 = ac.W, (ac.mass - mf) * G0
    rho = density(h)
    eta = ac.propulsion.eta_p
    R = breguet_range_prop(eta, ac.c_p, ac.polar.LD_max, W0, W1)
    CLe = ac.polar.CL_min_power
    E = breguet_endurance_prop(eta, ac.c_p, CLe, ac.polar.CD(CLe), rho, ac.S, W0, W1)
    return {"range_m": float(R), "endurance_s": float(E),
            "V_best_range_start": float(velocity_for_CL(W0, rho, ac.polar.CL_LDmax, ac.S)),
            "V_best_endurance_start": float(velocity_for_CL(W0, rho, CLe, ac.S))}


def performance_summary(ac: Aircraft, h_cruise: float = 0.0) -> dict:
    """One-call summary used by the examples and notebook."""
    rc0, V_rc0 = max_rate_of_climb(ac, 0.0)
    out = {
        "stall_speed_SL_mps": stall_speed(ac, 0.0),
        "max_speed_SL_mps": max_speed(ac, 0.0),
        "max_speed_cruise_alt_mps": max_speed(ac, h_cruise),
        "max_RC_SL_mps": rc0,
        "V_for_max_RC_SL_mps": V_rc0,
        "service_ceiling_m": service_ceiling(ac),
        "absolute_ceiling_m": absolute_ceiling(ac),
        "LD_max": ac.polar.LD_max,
        "V_LDmax_SL_mps": float(velocity_for_CL(ac.W, RHO0, ac.polar.CL_LDmax, ac.S)),
    }
    if ac.c_p is not None and ac.fuel_mass > 0:
        out.update(prop_range_endurance(ac, h_cruise))
    return out
