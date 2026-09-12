"""Example 2: conceptual sizing of a small gasoline survey UAV from mission requirements."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use("Agg")
import numpy as np

from _common import FIG_DIR, uav_mission
from aerosizing import plots, sizing as sz
from aerosizing.atmosphere import G0


def main():
    req, da = uav_mission()
    r = sz.size_aircraft(req, da)
    print("\n=== Small survey UAV sizing (constraint diagram + Raymer mission fractions)")
    print(f"requirements: range {req.range_m/1e3:.0f} km, payload {req.payload_mass} kg, cruise {req.cruise_speed} m/s @ {req.cruise_altitude:.0f} m, "
          f"Vs {req.stall_speed} m/s, R/C {req.climb_rate_SL} m/s, S_G {req.takeoff_ground_roll} m, ceiling {req.service_ceiling:.0f} m, loiter {req.loiter_time_s/60:.0f} min")
    print(f"design point: W/S = {r.wing_loading:.0f} N/m2, P/W = {r.power_to_weight:.2f} W/N (governing: {r.governing_constraint})")
    for name, pw in r.curves.PW.items():
        print(f"   {name:8s} needs P/W = {np.interp(r.wing_loading, r.curves.WS, pw):.2f} W/N")
    print(f"take-off mass {r.takeoff_mass:.1f} kg = payload {req.payload_mass} + fuel {r.fuel_mass:.2f} + empty {r.empty_mass:.1f}")
    print(f"wing area {r.wing_area:.3f} m2, span {r.span:.2f} m, shaft power {r.shaft_power:.0f} W ({r.shaft_power/745.7:.2f} hp)")
    print(f"cruise C_L {r.CL_cruise:.2f}, cruise L/D {r.LD_cruise:.1f}")
    os.makedirs(FIG_DIR, exist_ok=True)
    fig = plots.plot_constraint_diagram(r.curves, (r.wing_loading, r.power_to_weight, r.governing_constraint), PW_max=15)
    fig.savefig(f"{FIG_DIR}/uav_constraint_diagram.png")
    return r


if __name__ == "__main__":
    main()
