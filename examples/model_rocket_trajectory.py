"""Example 3: 2-D trajectory of a 54 mm mid-power rocket on an AeroTech G80-class motor."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use("Agg")

from _common import FIG_DIR, mid_power_rocket
from aerosizing import plots, rocket as rk, trajectory as tj
from aerosizing.atmosphere import G0


def main():
    veh = mid_power_rocket()
    m = veh.motor
    print(f"\n=== {veh.name} on {m.name}")
    print(f"motor: I_t={m.total_impulse:.1f} N s, t_b={m.burn_time:.2f} s, F_avg={m.average_thrust:.0f} N, Isp={m.isp:.0f} s")
    print(f"lift-off mass {veh.liftoff_mass*1e3:.0f} g, burnout mass {veh.burnout_mass*1e3:.0f} g, "
          f"ideal (Tsiolkovsky) dv = {rk.delta_v(m.isp, veh.liftoff_mass, veh.burnout_mass):.0f} m/s, "
          f"initial thrust/weight = {m.average_thrust/(veh.liftoff_mass*G0):.1f}")
    res = tj.simulate(veh, launch_angle_deg=5.0, rail_length=1.5)
    print(f"burnout: h={res.burnout_altitude:.0f} m, V={res.burnout_speed:.0f} m/s (max {res.max_speed:.0f} m/s, M {res.max_mach:.2f}, {res.max_accel_g:.1f} g, q_max {res.max_q/1e3:.1f} kPa)")
    print(f"apogee: {res.apogee:.0f} m at t={res.t_apogee:.1f} s; ballistic impact at {res.impact_range:.0f} m downrange, t={res.t_impact:.1f} s")
    nodrag = tj.simulate(tj.RocketVehicle("no drag", veh.dry_mass, m, 0.0, veh.ref_area), 5.0, stop_at_apogee=True)
    print(f"drag-free apogee would be {nodrag.apogee:.0f} m -> drag costs {100*(1-res.apogee/nodrag.apogee):.0f} % of altitude")
    os.makedirs(FIG_DIR, exist_ok=True)
    plots.plot_thrust_curve(m).savefig(f"{FIG_DIR}/rocket_thrust_curve.png")
    plots.plot_trajectory(res, veh.name).savefig(f"{FIG_DIR}/rocket_trajectory.png")
    return res


if __name__ == "__main__":
    main()
