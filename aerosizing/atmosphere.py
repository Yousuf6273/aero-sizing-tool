"""International Standard Atmosphere / U.S. Standard Atmosphere 1976, 0-86 km.

Source: NOAA/NASA/USAF, *U.S. Standard Atmosphere, 1976* (NASA-TM-X-74335),
eqs. 18 (geopotential), 23-25 (temperature), 33a/33b (pressure), 42 (density),
50 (speed of sound), 51 (Sutherland viscosity). Identical to ISO 2533 below 32 km.

All functions accept scalars or numpy arrays of *geometric* altitude in metres
unless ``geometric=False`` is passed, in which case geopotential altitude is assumed.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --- constants (USSA-1976, Table 2) -------------------------------------------
G0 = 9.80665          # m/s^2   standard gravity
R_AIR = 287.05287     # J/(kg K) specific gas constant of dry air
GAMMA = 1.4           # -       ratio of specific heats
T0 = 288.15           # K       sea-level temperature
P0 = 101325.0         # Pa      sea-level pressure
RHO0 = P0 / (R_AIR * T0)   # kg/m^3 = 1.2250
R_EARTH = 6356766.0   # m       effective Earth radius for geopotential conversion
_BETA = 1.458e-6      # kg/(m s K^0.5)  Sutherland constant
_S_SUTH = 110.4       # K               Sutherland temperature

# layer base geopotential altitudes [m] and lapse rates [K/m] (USSA-1976 Table 4)
H_BASE = np.array([0.0, 11000.0, 20000.0, 32000.0, 47000.0, 51000.0, 71000.0, 84852.0])
LAPSE = np.array([-6.5e-3, 0.0, 1.0e-3, 2.8e-3, 0.0, -2.8e-3, -2.0e-3])
H_MAX_GEOMETRIC = 86000.0


def _layer_bases():
    """Pre-compute base temperature and pressure of each layer by marching upward."""
    T_b = np.empty(len(LAPSE))
    p_b = np.empty(len(LAPSE))
    T_b[0], p_b[0] = T0, P0
    for i in range(1, len(LAPSE)):
        dH = H_BASE[i] - H_BASE[i - 1]
        L = LAPSE[i - 1]
        T_b[i] = T_b[i - 1] + L * dH
        if L != 0.0:
            p_b[i] = p_b[i - 1] * (T_b[i] / T_b[i - 1]) ** (-G0 / (L * R_AIR))
        else:
            p_b[i] = p_b[i - 1] * np.exp(-G0 * dH / (R_AIR * T_b[i - 1]))
    return T_b, p_b


T_BASE, P_BASE = _layer_bases()


@dataclass(frozen=True)
class AtmosphereState:
    """Thermodynamic state of the standard atmosphere at one or more altitudes."""
    h: np.ndarray | float      # geometric altitude [m]
    H: np.ndarray | float      # geopotential altitude [m]
    T: np.ndarray | float      # temperature [K]
    p: np.ndarray | float      # pressure [Pa]
    rho: np.ndarray | float    # density [kg/m^3]
    a: np.ndarray | float      # speed of sound [m/s]
    mu: np.ndarray | float     # dynamic viscosity [Pa s]

    @property
    def sigma(self):
        """Density ratio rho/rho_0."""
        return self.rho / RHO0


def geometric_to_geopotential(h):
    """USSA-1976 eq. 18: H = r_E h / (r_E + h)."""
    h = np.asarray(h, dtype=float)
    return R_EARTH * h / (R_EARTH + h)


def geopotential_to_geometric(H):
    H = np.asarray(H, dtype=float)
    return R_EARTH * H / (R_EARTH - H)


def isa(h, geometric: bool = True) -> AtmosphereState:
    """Standard-atmosphere state at altitude ``h`` [m].

    Parameters
    ----------
    h : float or array-like
        Altitude in metres (geometric by default).
    geometric : bool
        If False, ``h`` is interpreted as geopotential altitude.
    """
    h_in = np.asarray(h, dtype=float)
    scalar = h_in.ndim == 0
    h_arr = np.atleast_1d(h_in)
    if geometric:
        if np.any(h_arr > H_MAX_GEOMETRIC) or np.any(h_arr < -5000.0):
            raise ValueError("ISA model valid for -5 km <= h <= 86 km geometric")
        H = geometric_to_geopotential(h_arr)
        h_geom = h_arr
    else:
        H = h_arr
        h_geom = geopotential_to_geometric(H)

    idx = np.clip(np.searchsorted(H_BASE, H, side="right") - 1, 0, len(LAPSE) - 1)
    Tb, pb, Hb, L = T_BASE[idx], P_BASE[idx], H_BASE[idx], LAPSE[idx]
    T = Tb + L * (H - Hb)
    with np.errstate(divide="ignore", invalid="ignore"):
        p_grad = pb * (T / Tb) ** (-G0 / np.where(L == 0.0, 1.0, L) / R_AIR)
    p_iso = pb * np.exp(-G0 * (H - Hb) / (R_AIR * Tb))
    p = np.where(L == 0.0, p_iso, p_grad)
    rho = p / (R_AIR * T)
    a = np.sqrt(GAMMA * R_AIR * T)
    mu = _BETA * T ** 1.5 / (T + _S_SUTH)

    if scalar:
        return AtmosphereState(float(h_geom[0]), float(H[0]), float(T[0]), float(p[0]),
                               float(rho[0]), float(a[0]), float(mu[0]))
    return AtmosphereState(h_geom, H, T, p, rho, a, mu)


def temperature(h, geometric=True):
    return isa(h, geometric).T


def pressure(h, geometric=True):
    return isa(h, geometric).p


def density(h, geometric=True):
    return isa(h, geometric).rho


def speed_of_sound(h, geometric=True):
    return isa(h, geometric).a


def dynamic_viscosity(h, geometric=True):
    return isa(h, geometric).mu


def density_ratio(h, geometric=True):
    """sigma = rho/rho_0."""
    return isa(h, geometric).sigma
