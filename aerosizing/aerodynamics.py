"""Subsonic aerodynamics: parabolic drag polar, finite-wing lift curve, L/D.

Sources
-------
- Anderson, *Introduction to Flight*, 8th ed., Sec. 5.14-5.15 (drag polar, finite wings).
- Anderson, *Aircraft Performance and Design*, Sec. 2.7 (drag polar, (L/D)max, C_L^1.5/C_D).
- Raymer, *Aircraft Design: A Conceptual Approach*, 6th ed., Eq. 12.48 (Oswald e, straight wing).

Assumptions: incompressible/low-subsonic (M < ~0.6), attached flow, drag due to lift
purely quadratic in C_L, no wave drag. The polar is not valid beyond C_Lmax.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .atmosphere import RHO0


@dataclass(frozen=True)
class DragPolar:
    """Parabolic drag polar C_D = C_D0 + k C_L^2 with k = 1/(pi e AR)."""
    CD0: float   # zero-lift drag coefficient [-]
    AR: float    # aspect ratio b^2/S [-]
    e: float     # Oswald span efficiency [-]

    def __post_init__(self):
        if self.CD0 <= 0 or self.AR <= 0 or not (0 < self.e <= 1.05):
            raise ValueError("DragPolar requires CD0>0, AR>0, 0<e<=1.05")

    @property
    def k(self) -> float:
        """Induced-drag factor 1/(pi e AR)."""
        return 1.0 / (np.pi * self.e * self.AR)

    def CD(self, CL):
        return self.CD0 + self.k * np.asarray(CL, dtype=float) ** 2

    def L_over_D(self, CL):
        CL = np.asarray(CL, dtype=float)
        return CL / self.CD(CL)

    @property
    def CL_LDmax(self) -> float:
        """C_L for maximum L/D (minimum thrust required): sqrt(C_D0/k)."""
        return float(np.sqrt(self.CD0 / self.k))

    @property
    def LD_max(self) -> float:
        """(L/D)max = 1/(2 sqrt(C_D0 k))."""
        return float(1.0 / (2.0 * np.sqrt(self.CD0 * self.k)))

    @property
    def CL_min_power(self) -> float:
        """C_L maximising C_L^1.5/C_D (minimum power required): sqrt(3 C_D0/k)."""
        return float(np.sqrt(3.0 * self.CD0 / self.k))

    @property
    def CL15_over_CD_max(self) -> float:
        CL = self.CL_min_power
        return float(CL ** 1.5 / self.CD(CL))

    @property
    def CL_max_endurance_jet(self) -> float:
        """C_L maximising C_L^0.5/C_D (jet range): sqrt(C_D0/(3k))."""
        return float(np.sqrt(self.CD0 / (3.0 * self.k)))


def oswald_efficiency_straight_wing(AR: float) -> float:
    """Raymer (6th ed.) Eq. 12.48, straight (unswept) wings, valid roughly 4 <= AR <= 20."""
    return 1.78 * (1.0 - 0.045 * AR ** 0.68) - 0.64


def lift_curve_slope(AR: float, a0: float = 2.0 * np.pi, e1: float = 1.0) -> float:
    """Finite-wing lift-curve slope [rad^-1] from lifting-line theory.

    Anderson, *Introduction to Flight*, Sec. 5.15:  a = a0 / (1 + a0/(pi e1 AR)).
    ``a0`` is the airfoil (2-D) lift-curve slope, default thin-airfoil 2 pi.
    """
    return a0 / (1.0 + a0 / (np.pi * e1 * AR))


def lift_coefficient_from_alpha(alpha_rad, a: float, alpha_L0_rad: float = 0.0):
    """Linear lift curve C_L = a (alpha - alpha_L0), valid below stall."""
    return a * (np.asarray(alpha_rad, dtype=float) - alpha_L0_rad)


def dynamic_pressure(rho, V):
    return 0.5 * np.asarray(rho, dtype=float) * np.asarray(V, dtype=float) ** 2


def required_CL(W: float, rho, V, S: float):
    """Lift coefficient for steady level flight: C_L = 2W/(rho V^2 S)."""
    return W / (dynamic_pressure(rho, V) * S)


def velocity_for_CL(W: float, rho, CL, S: float):
    """Airspeed at which a given C_L carries weight W."""
    return np.sqrt(2.0 * W / (np.asarray(rho, dtype=float) * S * np.asarray(CL, dtype=float)))


def reynolds_number(rho, V, L, mu):
    return rho * V * L / mu


def LD_vs_airspeed(V, W: float, rho: float, S: float, polar: DragPolar):
    """Return (CL, CD, L/D, drag [N]) arrays for level flight at airspeeds V [m/s]."""
    V = np.asarray(V, dtype=float)
    CL = required_CL(W, rho, V, S)
    CD = polar.CD(CL)
    D = dynamic_pressure(rho, V) * S * CD
    return CL, CD, CL / CD, D


def equivalent_airspeed(V_true, rho):
    """EAS = TAS sqrt(rho/rho0)."""
    return V_true * np.sqrt(rho / RHO0)
