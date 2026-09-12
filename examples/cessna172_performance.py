"""Example 1: performance analysis of a Cessna 172S-like aircraft, compared with published figures."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use("Agg")

from _common import C172S_PUBLISHED, FIG_DIR, cessna_172s
from aerosizing import aircraft_performance as ap, plots


def main():
    ac = cessna_172s()
    s = ap.performance_summary(ac, h_cruise=2438.0)   # 8000 ft cruise
    print(f"\n=== {ac.name}: W={ac.W/1e3:.1f} kN, W/S={ac.wing_loading:.0f} N/m2, AR={ac.AR:.2f}, (L/D)max={s['LD_max']:.1f}")
    rows = [
        ("stall speed (clean, SL)", "stall_speed_SL_mps", 1 / 0.5144, "kt"),
        ("max level speed (SL)", "max_speed_SL_mps", 1 / 0.5144, "kt"),
        ("max rate of climb (SL)", "max_RC_SL_mps", 196.85, "ft/min"),
        ("service ceiling", "service_ceiling_m", 3.2808, "ft"),
        ("Breguet range (best L/D, full fuel)", "range_m", 1 / 1852, "nmi"),
    ]
    print(f"{'quantity':38s}{'model':>10s}{'published':>12s}  unit")
    for label, key, f, unit in rows:
        print(f"{label:38s}{s[key]*f:10.0f}{C172S_PUBLISHED[key]*f:12.0f}  {unit}")
    print(f"endurance at best C_L^1.5/C_D: {s['endurance_s']/3600:.1f} h; V_max at 8000 ft: {s['max_speed_cruise_alt_mps']/0.5144:.0f} KTAS")
    os.makedirs(FIG_DIR, exist_ok=True)
    plots.plot_drag_polar_and_LD(ac).savefig(f"{FIG_DIR}/c172_polar_LD.png")
    plots.plot_power_curves(ac, (0.0, 2438.0, 4000.0)).savefig(f"{FIG_DIR}/c172_power.png")
    plots.plot_climb(ac, s["absolute_ceiling_m"]).savefig(f"{FIG_DIR}/c172_climb.png")
    return s


if __name__ == "__main__":
    main()
