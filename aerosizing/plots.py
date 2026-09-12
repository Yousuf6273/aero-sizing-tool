"""Matplotlib helpers. Every function returns the Figure so callers can save or show it."""
from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from .aerodynamics import LD_vs_airspeed
from .aircraft_performance import Aircraft, power_available, power_required, rate_of_climb, stall_speed, max_speed
from .atmosphere import density, isa
from .sizing import ConstraintCurves
from .trajectory import TrajectoryResult

matplotlib.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3})


def plot_atmosphere(h_max=86000.0):
    h = np.linspace(0, h_max, 500)
    st = isa(h)
    fig, axs = plt.subplots(1, 4, figsize=(13, 4), sharey=True)
    for ax, (v, lab) in zip(axs, [(st.T, "T [K]"), (st.p / 1e3, "p [kPa]"), (st.rho, r"$\rho$ [kg/m$^3$]"), (st.a, "a [m/s]")]):
        ax.plot(v, h / 1e3); ax.set_xlabel(lab)
    axs[0].set_ylabel("geometric altitude [km]")
    fig.suptitle("ISA / U.S. Standard Atmosphere 1976")
    fig.tight_layout()
    return fig


def plot_drag_polar_and_LD(ac: Aircraft, h=0.0):
    rho = density(h)
    Vs = stall_speed(ac, h)
    V = np.linspace(Vs, 2.5 * Vs, 300)
    CL, CD, LD, D = LD_vs_airspeed(V, ac.W, rho, ac.S, ac.polar)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    CLg = np.linspace(0, ac.CL_max, 200)
    a1.plot(ac.polar.CD(CLg), CLg); a1.set_xlabel(r"$C_D$"); a1.set_ylabel(r"$C_L$")
    a1.set_title(f"Drag polar: $C_{{D0}}$={ac.CD0}, AR={ac.AR:.1f}, e={ac.e}")
    a2.plot(V, LD); a2.axvline(Vs, ls="--", c="k", label="stall")
    a2.set_xlabel("true airspeed [m/s]"); a2.set_ylabel("L/D"); a2.set_title(f"{ac.name}: L/D vs V at h={h:.0f} m")
    a2.legend(); fig.tight_layout()
    return fig


def plot_power_curves(ac: Aircraft, altitudes=(0.0, 2000.0, 4000.0)):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for h in altitudes:
        Vs = stall_speed(ac, h)
        try:
            Vmax = max_speed(ac, h)
        except ValueError:
            Vmax = 3 * Vs
        V = np.linspace(Vs, 1.15 * Vmax, 300)
        line, = ax.plot(V, power_required(ac, V, h) / 1e3, label=f"$P_R$ h={h/1e3:.0f} km")
        ax.plot(V, power_available(ac, V, h) / 1e3 * np.ones_like(V), ls="--", c=line.get_color(),
                label=f"$P_A$ h={h/1e3:.0f} km")
    ax.set_xlabel("true airspeed [m/s]"); ax.set_ylabel("power [kW]"); ax.set_title(f"{ac.name}: power required vs available")
    ax.legend(ncol=2, fontsize=8); fig.tight_layout()
    return fig


def plot_climb(ac: Aircraft, h_max: float):
    from .aircraft_performance import max_rate_of_climb
    hs = np.linspace(0, h_max, 30)
    rc = np.array([max_rate_of_climb(ac, h)[0] for h in hs])
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(rc, hs / 1e3); ax.axvline(0.508, ls="--", c="k", label="service ceiling (0.508 m/s)")
    ax.set_xlabel("max rate of climb [m/s]"); ax.set_ylabel("altitude [km]"); ax.set_title(f"{ac.name}: climb hodograph")
    ax.legend(); fig.tight_layout()
    return fig


def plot_constraint_diagram(cc: ConstraintCurves, design=None, PW_max=None):
    fig, ax = plt.subplots(figsize=(7, 5))
    for name, pw in cc.PW.items():
        ax.plot(cc.WS, pw, label=name)
    ax.axvline(cc.WS_stall_max, c="k", ls="--", label="stall (max W/S)")
    ymax = PW_max or float(np.nanpercentile(np.concatenate(list(cc.PW.values())), 95))
    ax.fill_between(cc.WS, np.max(np.array(list(cc.PW.values())), axis=0), ymax,
                    where=cc.WS <= cc.WS_stall_max, color="green", alpha=0.12, label="feasible")
    if design is not None:
        ax.plot(design[0], design[1], "ro", ms=8, label=f"design point ({design[2]})")
    ax.set_ylim(0, ymax); ax.set_xlabel(r"wing loading $W/S$ [N/m$^2$]"); ax.set_ylabel("sea-level shaft power / weight [W/N]")
    ax.set_title("Constraint diagram (matching plot)"); ax.legend(fontsize=8); fig.tight_layout()
    return fig


def plot_thrust_curve(motor):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    t = np.linspace(0, motor.burn_time, 300)
    ax.plot(t, motor.thrust_at(t)); ax.set_xlabel("t [s]"); ax.set_ylabel("thrust [N]")
    ax.set_title(f"{motor.name}: $I_t$={motor.total_impulse:.1f} N s, $I_{{sp}}$={motor.isp:.0f} s")
    fig.tight_layout(); return fig


def plot_trajectory(res: TrajectoryResult, name=""):
    fig, axs = plt.subplots(2, 2, figsize=(11, 7))
    axs[0, 0].plot(res.t, res.z); axs[0, 0].set_xlabel("t [s]"); axs[0, 0].set_ylabel("altitude [m]")
    axs[0, 0].axhline(res.apogee, ls="--", c="k", lw=0.8); axs[0, 0].set_title(f"apogee {res.apogee:.0f} m at {res.t_apogee:.1f} s")
    axs[0, 1].plot(res.t, res.speed); axs[0, 1].set_xlabel("t [s]"); axs[0, 1].set_ylabel("speed [m/s]")
    axs[0, 1].set_title(f"max speed {res.max_speed:.0f} m/s (M {res.max_mach:.2f})")
    axs[1, 0].plot(res.t, res.thrust, label="thrust"); axs[1, 0].plot(res.t, res.drag, label="drag")
    axs[1, 0].plot(res.t, res.mass * 9.80665, label="weight"); axs[1, 0].set_xlabel("t [s]"); axs[1, 0].set_ylabel("force [N]")
    axs[1, 0].legend(); axs[1, 0].set_xlim(0, min(res.t[-1], 3 * res.t_apogee))
    axs[1, 1].plot(res.x, res.z); axs[1, 1].set_xlabel("downrange x [m]"); axs[1, 1].set_ylabel("altitude z [m]"); axs[1, 1].set_aspect("equal", adjustable="datalim")
    fig.suptitle(f"{name} trajectory"); fig.tight_layout()
    return fig
