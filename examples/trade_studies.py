"""Design trade studies:
  A. wing aspect ratio vs Breguet range and endurance for the survey UAV (fixed W/S, mass).
  B. propellant mass fraction vs delta-v (Tsiolkovsky) and, via the trajectory model,
     propellant mass vs apogee for the mid-power rocket.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from _common import FIG_DIR, g80_motor, uav_mission
from aerosizing import aerodynamics as aero, aircraft_performance as ap, rocket as rk, sizing as sz, trajectory as tj
from aerosizing.atmosphere import G0, density


def aspect_ratio_study(ARs=np.linspace(4, 16, 25)):
    req, da = uav_mission()
    base = sz.size_aircraft(req, da)
    m0, mf, S = base.takeoff_mass, base.fuel_mass, base.wing_area
    W0, W1 = m0 * G0, (m0 - mf) * G0
    rho = density(req.cruise_altitude)
    R, E, LDs = [], [], []
    for AR in ARs:
        e = aero.oswald_efficiency_straight_wing(AR)   # Raymer 12.48: e falls as AR rises
        p = aero.DragPolar(da.CD0, AR, e)
        R.append(ap.breguet_range_prop(da.eta_p, da.c_p, p.LD_max, W0, W1))
        CLe = p.CL_min_power
        E.append(ap.breguet_endurance_prop(da.eta_p, da.c_p, CLe, p.CD(CLe), rho, S, W0, W1))
        LDs.append(p.LD_max)
    R, E = np.array(R), np.array(E)
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    ax1.plot(ARs, R / 1e3, "b-", label="Breguet range (at (L/D)max)"); ax1.set_xlabel("aspect ratio"); ax1.set_ylabel("range [km]", color="b")
    ax2 = ax1.twinx(); ax2.plot(ARs, E / 3600, "r--", label="endurance (at max $C_L^{1.5}/C_D$)"); ax2.set_ylabel("endurance [h]", color="r"); ax2.grid(False)
    ax1.axvline(da.AR, c="k", ls=":", label=f"baseline AR={da.AR}")
    ax1.set_title("UAV: aspect ratio vs range & endurance (fixed fuel, W/S, S)")
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")
    fig.tight_layout()
    return ARs, R, E, np.array(LDs), fig


def propellant_fraction_study():
    dv = np.linspace(0, 12000, 300)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for isp in (250, 300, 350, 450):
        a1.plot(dv / 1e3, rk.propellant_mass_fraction(dv, isp), label=f"Isp = {isp} s")
    a1.axhline(0.90, c="k", ls=":", label="~0.90 practical single-stage limit")
    a1.axvline(9.4, c="gray", ls="--", label="~9.4 km/s to LEO incl. losses")
    a1.set_xlabel(r"$\Delta v$ [km/s]"); a1.set_ylabel(r"propellant mass fraction $m_p/m_0$"); a1.set_title("Tsiolkovsky: propellant fraction vs $\\Delta v$"); a1.legend(fontsize=8)

    # trajectory-based: scale the G80's propellant (same Isp, same burn time, thrust scales) for the mid-power rocket
    base = g80_motor()
    fracs = np.linspace(0.4, 2.5, 15)
    apogees, ideal_dv = [], []
    for f in fracs:
        m = rk.Motor(base.name, base.time, base.thrust_curve * f, base.propellant_mass * f, base.casing_mass)
        veh = tj.RocketVehicle("scaled", 0.60, m, 0.45, np.pi * 0.027 ** 2)
        apogees.append(tj.simulate(veh, 5.0, stop_at_apogee=True).apogee)
        ideal_dv.append(rk.delta_v(m.isp, veh.liftoff_mass, veh.burnout_mass))
    mp = base.propellant_mass * fracs * 1e3
    a2.plot(mp, apogees, "o-", label="simulated apogee (with drag & gravity)")
    a2.set_xlabel("propellant mass [g] (same Isp, burn time)"); a2.set_ylabel("apogee [m]"); a2.set_title("Mid-power rocket: propellant mass vs apogee")
    ax3 = a2.twinx(); ax3.plot(mp, ideal_dv, "r--", label="ideal $\\Delta v$ (Tsiolkovsky)"); ax3.set_ylabel(r"ideal $\Delta v$ [m/s]", color="r"); ax3.grid(False)
    h1, l1 = a2.get_legend_handles_labels(); h2, l2 = ax3.get_legend_handles_labels(); a2.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")
    fig.tight_layout()
    return mp, np.array(apogees), np.array(ideal_dv), fig


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    ARs, R, E, LD, fig = aspect_ratio_study()
    fig.savefig(f"{FIG_DIR}/trade_aspect_ratio.png")
    print("\n=== Trade study A: aspect ratio (UAV)")
    for AR, r, e_, ld in zip(ARs[::6], R[::6], E[::6], LD[::6]):
        print(f"AR {AR:5.1f}: (L/D)max {ld:5.1f}  range {r/1e3:6.0f} km  endurance {e_/3600:5.2f} h")
    mp, apo, dv, fig = propellant_fraction_study()
    fig.savefig(f"{FIG_DIR}/trade_propellant.png")
    print("\n=== Trade study B: propellant mass (rocket)")
    for a, b, c in zip(mp[::3], apo[::3], dv[::3]):
        print(f"m_p {a:6.1f} g: ideal dv {c:5.0f} m/s  apogee {b:6.0f} m  (m per m/s: {b/c:5.2f})")


if __name__ == "__main__":
    main()
