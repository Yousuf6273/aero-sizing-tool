"""Rocket propulsion fundamentals: Tsiolkovsky equation, mass ratios, thrust,
ideal-nozzle relations, staging and a thrust-curve motor model.

Sources
-------
- Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed.: eqs. 2-1/2-3 (impulse, Isp),
  2-14 (thrust), 3-16 (exit velocity), 3-25 (area ratio), 3-30 (thrust coefficient),
  3-32 (characteristic velocity), 4-6 (rocket equation), Sec. 4.7 (staging).
- NASA Glenn Research Center, Beginner's Guide to Rockets: "Ideal Rocket Equation",
  "Rocket Thrust Equation".

Ideal-rocket assumptions (Sutton Sec. 3.1): 1-D isentropic flow of a calorically
perfect gas, frozen composition, steady, adiabatic, no friction.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import cumulative_trapezoid, trapezoid

from .atmosphere import G0


# ---------------------------------------------------------------------------
# rocket equation and mass bookkeeping
# ---------------------------------------------------------------------------
def delta_v(isp: float, m0: float, mf: float) -> float:
    """Tsiolkovsky (Sutton eq. 4-6): dv = Isp g0 ln(m0/mf)  [m/s]."""
    if mf <= 0 or m0 < mf:
        raise ValueError("require 0 < mf <= m0")
    return isp * G0 * np.log(m0 / mf)


def mass_ratio(dv: float, isp: float) -> float:
    """m0/mf required for a given dv."""
    return np.exp(np.asarray(dv, dtype=float) / (isp * G0))


def propellant_mass_fraction(dv: float, isp: float) -> float:
    """zeta = m_p/m0 = 1 - exp(-dv/(Isp g0))."""
    return 1.0 - 1.0 / mass_ratio(dv, isp)


def propellant_mass_for_dv(dv: float, isp: float, m_final: float) -> float:
    """Propellant needed so that a final mass m_final receives dv: m_p = m_final (MR - 1)."""
    return m_final * (mass_ratio(dv, isp) - 1.0)


@dataclass(frozen=True)
class Stage:
    """One rocket stage. Structural coefficient eps = m_s/(m_s + m_p) (Sutton Sec. 4.7)."""
    m_propellant: float
    m_structure: float
    isp: float

    @property
    def structural_coefficient(self) -> float:
        return self.m_structure / (self.m_structure + self.m_propellant)


def multistage_delta_v(stages: list[Stage], payload: float) -> tuple[float, list[float]]:
    """Total ideal dv of a serial-staged rocket (lower stage first). Returns (total, per-stage)."""
    dvs = []
    # mass above each stage = payload + all upper stages
    for i, st in enumerate(stages):
        upper = payload + sum(s.m_propellant + s.m_structure for s in stages[i + 1:])
        m0 = upper + st.m_structure + st.m_propellant
        mf = upper + st.m_structure
        dvs.append(delta_v(st.isp, m0, mf))
    return float(sum(dvs)), dvs


# ---------------------------------------------------------------------------
# thrust and ideal nozzle relations
# ---------------------------------------------------------------------------
def effective_exhaust_velocity(isp: float) -> float:
    """c = Isp g0 (Sutton eq. 2-6)."""
    return isp * G0


def thrust_from_isp(mdot: float, isp: float) -> float:
    """F = mdot Isp g0 (Sutton eq. 2-5 rearranged)."""
    return mdot * isp * G0


def thrust(mdot: float, v_e: float, p_e: float = 0.0, p_a: float = 0.0, A_e: float = 0.0) -> float:
    """Momentum + pressure thrust: F = mdot v_e + (p_e - p_a) A_e (Sutton eq. 2-14)."""
    return mdot * v_e + (p_e - p_a) * A_e


def ideal_exit_velocity(gamma: float, R: float, T_c: float, p_e: float, p_c: float) -> float:
    """Sutton eq. 3-16, isentropic expansion from chamber (T_c, p_c) to p_e.
    R is the specific gas constant of the exhaust [J/(kg K)]."""
    pr = p_e / p_c
    return float(np.sqrt(2.0 * gamma / (gamma - 1.0) * R * T_c * (1.0 - pr ** ((gamma - 1.0) / gamma))))


def area_ratio(gamma: float, p_e: float, p_c: float) -> float:
    """A_e/A_t for an exit pressure ratio (Sutton eq. 3-25)."""
    pr = p_e / p_c
    g1 = (gamma + 1.0) / 2.0
    num = g1 ** (1.0 / (gamma - 1.0)) * pr ** (1.0 / gamma)
    den = np.sqrt((gamma + 1.0) / (gamma - 1.0) * (1.0 - pr ** ((gamma - 1.0) / gamma)))
    return float(1.0 / (num * den))


def thrust_coefficient(gamma: float, p_c: float, p_e: float, p_a: float, eps: float | None = None) -> float:
    """Sutton eq. 3-30. If eps (A_e/A_t) is None it is computed from p_e/p_c."""
    if eps is None:
        eps = area_ratio(gamma, p_e, p_c)
    pr = p_e / p_c
    term = (2.0 * gamma ** 2 / (gamma - 1.0) * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (gamma - 1.0))
            * (1.0 - pr ** ((gamma - 1.0) / gamma)))
    return float(np.sqrt(term) + (p_e - p_a) / p_c * eps)


def characteristic_velocity(gamma: float, R: float, T_c: float) -> float:
    """c* = sqrt(gamma R T_c) / (gamma sqrt((2/(gamma+1))^((gamma+1)/(gamma-1))))  (Sutton eq. 3-32)."""
    return float(np.sqrt(gamma * R * T_c) / (gamma * np.sqrt((2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (gamma - 1.0)))))


def isp_from_c_star_cf(c_star: float, c_f: float) -> float:
    """Isp = c* C_F / g0 (Sutton eq. 3-33 rearranged)."""
    return c_star * c_f / G0


# ---------------------------------------------------------------------------
# motor model with a tabulated thrust curve
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Motor:
    """Solid motor described by a thrust-time table.

    Mass flow is taken proportional to thrust, mdot = F/(Isp g0) with
    Isp = I_t/(m_p g0), so that the integrated mass flow equals the propellant mass
    exactly (Sutton eqs. 2-1, 2-3). ``casing_mass`` is the burnt-out motor mass.
    """
    name: str
    time: np.ndarray            # s, monotonically increasing, starting at 0
    thrust_curve: np.ndarray    # N
    propellant_mass: float      # kg
    casing_mass: float          # kg (motor hardware without propellant)
    _mass_burned: np.ndarray = field(init=False, repr=False)
    _t_fine: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        t = np.asarray(self.time, dtype=float)
        F = np.asarray(self.thrust_curve, dtype=float)
        if t[0] != 0.0 or np.any(np.diff(t) <= 0) or np.any(F < 0):
            raise ValueError("time must start at 0 and increase; thrust must be >= 0")
        object.__setattr__(self, "time", t)
        object.__setattr__(self, "thrust_curve", F)
        # integrate the (piecewise-linear) thrust curve on a fine grid so that the
        # cumulative impulse - and hence burned mass - is accurate between table nodes
        t_fine = np.union1d(t, np.linspace(t[0], t[-1], 4001))
        F_fine = np.interp(t_fine, t, F)
        I_cum = cumulative_trapezoid(F_fine, t_fine, initial=0.0)
        object.__setattr__(self, "_t_fine", t_fine)
        object.__setattr__(self, "_mass_burned", self.propellant_mass * I_cum / I_cum[-1])

    @classmethod
    def trapezoid(cls, name: str, total_impulse: float, burn_time: float, peak_thrust: float,
                  propellant_mass: float, casing_mass: float, t_rise: float = 0.1) -> "Motor":
        """Idealised curve from catalogue values (I_t, t_b, F_peak): linear rise to
        ``peak_thrust`` in ``t_rise``, then a linear decay chosen so the total impulse
        matches. If the peak is too pronounced for a linear decay (typical of small
        motors with an ignition spike, e.g. Estes C6), the curve becomes a spike that
        decays over ``t_decay`` to a sustain level, held until burn-out."""
        t_tail = 1e-3
        if peak_thrust * burn_time < total_impulse:
            raise ValueError("peak_thrust is below the average thrust impulse/burn_time")
        # shape 1: rise (0..t_rise) to F_p, linear to F_end at burn_time, 1 ms tail-off
        # impulse = 0.5 F_p t_rise + 0.5 (F_p + F_end)(t_b - t_rise) + 0.5 F_end t_tail
        F_end = ((total_impulse - 0.5 * peak_thrust * t_rise - 0.5 * peak_thrust * (burn_time - t_rise))
                 / (0.5 * (burn_time - t_rise) + 0.5 * t_tail))
        if F_end >= 0:
            t = np.array([0.0, t_rise, burn_time, burn_time + t_tail])
            F = np.array([0.0, peak_thrust, F_end, 0.0])
            return cls(name, t, F, propellant_mass, casing_mass)
        # shape 2: spike to F_p, linear decay over t_decay to sustain F_s, constant to t_b
        # impulse = 0.5 F_p t_rise + 0.5 (F_p + F_s) t_decay + F_s (t_b - t_rise - t_decay) + 0.5 F_s t_tail
        t_decay = min(0.2, 0.5 * (burn_time - t_rise))
        F_s = ((total_impulse - 0.5 * peak_thrust * t_rise - 0.5 * peak_thrust * t_decay)
               / (0.5 * t_decay + (burn_time - t_rise - t_decay) + 0.5 * t_tail))
        if F_s < 0:
            raise ValueError("peak_thrust too high for this impulse/burn time")
        t = np.array([0.0, t_rise, t_rise + t_decay, burn_time, burn_time + t_tail])
        F = np.array([0.0, peak_thrust, F_s, F_s, 0.0])
        return cls(name, t, F, propellant_mass, casing_mass)

    @property
    def total_impulse(self) -> float:
        return float(trapezoid(np.interp(self._t_fine, self.time, self.thrust_curve), self._t_fine))

    @property
    def burn_time(self) -> float:
        return float(self.time[-1])

    @property
    def isp(self) -> float:
        return self.total_impulse / (self.propellant_mass * G0)

    @property
    def average_thrust(self) -> float:
        return self.total_impulse / self.burn_time

    def thrust_at(self, t):
        return np.interp(t, self.time, self.thrust_curve, left=0.0, right=0.0)

    def mass_flow_at(self, t):
        return self.thrust_at(t) / (self.isp * G0)

    def propellant_remaining(self, t):
        return self.propellant_mass - np.interp(t, self._t_fine, self._mass_burned,
                                                left=0.0, right=self.propellant_mass)

    def mass_at(self, t):
        return self.casing_mass + self.propellant_remaining(t)
