"""Planar point-mass rocket trajectory with thrust, gravity and drag.

Model (Sutton Sec. 4.2-4.3 "flight in the atmosphere", zero-lift gravity turn):

    dx/dt = v_x,   dz/dt = v_z
    m dv/dt = F(t) u_v - 0.5 rho(z) |v|^2 C_D A u_v - m g0 e_z
    m(t) = m_dry + m_motor(t)

with u_v the unit velocity vector after leaving the launch rail (thrust along the
velocity vector, i.e. zero angle of attack), the rail direction before that.
Integrated with scipy.integrate.solve_ivp (RK45) with terminal events; a fixed-step
RK4 is provided for cross-checking.

Assumptions: flat Earth, constant g0, no wind, constant C_D (no Mach dependence),
no lift, no thrust misalignment.  Validity: low-altitude (< 86 km) rockets.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .atmosphere import G0, density, speed_of_sound
from .numerics import rk4
from .rocket import Motor


@dataclass(frozen=True)
class RocketVehicle:
    name: str
    dry_mass: float       # airframe + recovery + payload, WITHOUT motor [kg]
    motor: Motor
    Cd: float             # drag coefficient referenced to ``ref_area`` [-]
    ref_area: float       # frontal reference area [m^2]

    def mass(self, t):
        return self.dry_mass + self.motor.mass_at(t)

    @property
    def liftoff_mass(self) -> float:
        return float(self.mass(0.0))

    @property
    def burnout_mass(self) -> float:
        return float(self.mass(self.motor.burn_time))


@dataclass
class TrajectoryResult:
    t: np.ndarray
    x: np.ndarray
    z: np.ndarray
    vx: np.ndarray
    vz: np.ndarray
    mass: np.ndarray
    thrust: np.ndarray
    drag: np.ndarray
    apogee: float
    t_apogee: float
    burnout_altitude: float
    burnout_speed: float
    max_speed: float
    max_mach: float
    max_q: float
    max_accel_g: float
    impact_range: float | None
    t_impact: float | None

    @property
    def speed(self):
        return np.hypot(self.vx, self.vz)


def _rhs(veh: RocketVehicle, rail_dir: np.ndarray, rail_length: float):
    def f(t, y):
        x, z, vx, vz = y
        V = np.hypot(vx, vz)
        m = veh.mass(t)
        F = veh.motor.thrust_at(t)
        along = np.hypot(x, z)
        if along < rail_length or V < 1e-6:
            u = rail_dir
        else:
            u = np.array([vx, vz]) / V
        rho = density(max(z, 0.0))
        D = 0.5 * rho * V ** 2 * veh.Cd * veh.ref_area
        ax = (F - D) * u[0] / m
        az = (F - D) * u[1] / m - G0
        # on the pad/rail the structure supports the rocket: no motion until the net
        # acceleration along the rail becomes positive
        supported = (along < rail_length) or (z <= 1e-9)
        if supported and V < 1e-6 and (F * 1.0 - m * G0 * u[1]) <= 0.0:
            return [0.0, 0.0, 0.0, 0.0]
        return [vx, vz, ax, az]
    return f


def simulate(veh: RocketVehicle, launch_angle_deg: float = 0.0, rail_length: float = 1.5,
             t_max: float = 300.0, rtol: float = 1e-8, atol: float = 1e-10,
             n_out: int = 2000, stop_at_apogee: bool = False) -> TrajectoryResult:
    """Integrate the launch. ``launch_angle_deg`` is measured from vertical (positive
    tilts the rail toward +x). Stops at ground impact (or apogee if requested)."""
    th = np.radians(launch_angle_deg)
    rail_dir = np.array([np.sin(th), np.cos(th)])
    f = _rhs(veh, rail_dir, rail_length)

    def apogee_event(t, y):
        # ignore the rail phase (v_z == 0 there would trigger spuriously)
        return y[3] if y[1] > 0.5 * rail_length + 0.1 else 1.0
    apogee_event.terminal = stop_at_apogee
    apogee_event.direction = -1

    def impact_event(t, y):
        # only arm once the rocket is clearly descending (avoids pad-phase noise)
        return y[1] if y[3] < -0.5 else 1.0
    impact_event.terminal = True
    impact_event.direction = -1

    sol = solve_ivp(f, (0.0, t_max), [0.0, 0.0, 0.0, 0.0], method="RK45", rtol=rtol, atol=atol,
                    events=[apogee_event, impact_event], dense_output=True, max_step=0.05)
    t_end = sol.t[-1]
    t = np.linspace(0.0, t_end, n_out)
    x, z, vx, vz = sol.sol(t)
    m = veh.mass(t)
    F = veh.motor.thrust_at(t)
    V = np.hypot(vx, vz)
    rho = density(np.maximum(z, 0.0))
    D = 0.5 * rho * V ** 2 * veh.Cd * veh.ref_area
    a_mag = np.abs(F - D) / m
    a = speed_of_sound(np.maximum(z, 0.0))

    if len(sol.t_events[0]) > 0:
        t_ap = float(sol.t_events[0][0])
        ap = float(sol.sol(t_ap)[1])
    else:
        i = int(np.argmax(z)); t_ap, ap = float(t[i]), float(z[i])
    tb = veh.motor.burn_time
    yb = sol.sol(min(tb, t_end))
    impact = None; t_imp = None
    if len(sol.t_events[1]) > 0:
        t_imp = float(sol.t_events[1][0]); impact = float(sol.sol(t_imp)[0])
    return TrajectoryResult(t, x, z, vx, vz, m, F, D, ap, t_ap, float(yb[1]), float(np.hypot(yb[2], yb[3])),
                            float(V.max()), float((V / a).max()), float((0.5 * rho * V ** 2).max()),
                            float(a_mag.max() / G0), impact, t_imp)


def simulate_rk4(veh: RocketVehicle, launch_angle_deg: float = 0.0, rail_length: float = 1.5,
                 t_end: float = 30.0, dt: float = 0.005):
    """Same model integrated with the fixed-step classical RK4 (for verification)."""
    th = np.radians(launch_angle_deg)
    f = _rhs(veh, np.array([np.sin(th), np.cos(th)]), rail_length)
    t = np.arange(0.0, t_end + dt, dt)
    y = rk4(lambda tt, yy: np.asarray(f(tt, yy)), np.zeros(4), t)
    return t, y


def vertical_no_drag_speed(motor: Motor, m_dry: float, t):
    """Analytic check (Sutton eq. 4-12, vertical, no drag): v = c ln(m0/m(t)) - g0 t."""
    m0 = m_dry + motor.mass_at(0.0)
    c = motor.isp * G0
    return c * np.log(m0 / (m_dry + motor.mass_at(t))) - G0 * np.asarray(t, dtype=float)
