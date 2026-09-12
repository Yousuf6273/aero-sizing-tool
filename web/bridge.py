"""Glue between the browser UI and the aerosizing package (runs inside Pyodide).
Each run_* function takes a JSON string of inputs and returns a JSON string of
results plus base64-encoded PNG plots."""
import base64
import io
import json
import os

os.environ["MPLBACKEND"] = "Agg"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from aerosizing import aerodynamics as aero, aircraft_performance as ap, atmosphere as atm, plots, rocket as rk, sizing as sz, trajectory as tj
from aerosizing.atmosphere import G0

KT = 1 / 0.5144
FPM = 196.85
FT = 3.2808


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def run_aircraft(js):
    p = json.loads(js)
    AR = p["span"] ** 2 / p["S"]
    jet = p.get("propulsion", "prop") == "jet"
    if jet:
        prop = ap.Turbojet(p["thrust_kN"] * 1e3, p["lapse_m"])
        kw = {"c_t": p["tsfc_per_h"] / 3600.0}
    else:
        prop = ap.PistonProp(p["power_kW"] * 1e3, p["eta_p"])
        kw = {"c_p": p["sfc_kg_per_kWh"] / (1000.0 * 3600.0)}
    ac = ap.Aircraft(p["name"], p["mass"], p["S"], AR, p["e"], p["CD0"], p["CL_max"], prop,
                     fuel_mass=p["fuel_mass"], **kw)
    s = ap.performance_summary(ac, p["h_cruise"])
    a_sl = atm.isa(0.0).a
    a_cr = atm.isa(p["h_cruise"]).a
    M_sl = s["max_speed_SL_mps"] / a_sl
    M_cr = s["max_speed_cruise_alt_mps"] / a_cr
    rows = [
        ["Stall speed (clean, sea level)", f"{s['stall_speed_SL_mps']:.1f} m/s", f"{s['stall_speed_SL_mps']*KT:.0f} kt"],
        ["Max level speed (sea level)", f"{s['max_speed_SL_mps']:.1f} m/s", f"{s['max_speed_SL_mps']*KT:.0f} kt · Mach {M_sl:.2f}"],
        [f"Max level speed at {p['h_cruise']:.0f} m", f"{s['max_speed_cruise_alt_mps']:.1f} m/s", f"{s['max_speed_cruise_alt_mps']*KT:.0f} kt · Mach {M_cr:.2f}"],
        ["Max rate of climb (sea level)", f"{s['max_RC_SL_mps']:.1f} m/s", f"{s['max_RC_SL_mps']*FPM:.0f} ft/min at {s['V_for_max_RC_SL_mps']*KT:.0f} kt"],
        ["Service ceiling (R/C = 0.5 m/s)", f"{s['service_ceiling_m']:.0f} m", f"{s['service_ceiling_m']*FT:.0f} ft"],
        ["Absolute ceiling", f"{s['absolute_ceiling_m']:.0f} m", f"{s['absolute_ceiling_m']*FT:.0f} ft"],
        ["(L/D)max", f"{s['LD_max']:.1f}", f"at {s['V_LDmax_SL_mps']*KT:.0f} kt (sea level)"],
    ]
    if "range_m" in s:
        best = "max C_L^0.5/C_D" if jet else "best L/D"
        loit = "best L/D" if jet else "max C_L^1.5/C_D"
        rows += [[f"Breguet range ({best}, all fuel)", f"{s['range_m']/1e3:.0f} km", f"{s['range_m']/1852:.0f} nmi"],
                 [f"Breguet endurance ({loit})", f"{s['endurance_s']/3600:.1f} h", ""]]
    warn = []
    if max(M_sl, M_cr) > 0.7:
        warn.append(f"Mach {max(M_sl, M_cr):.2f} is beyond this model's validity. The drag polar is "
                    "incompressible (valid below about Mach 0.6-0.7) and has no wave drag, so top speed, "
                    "climb rate and ceiling are OVER-predicted for transonic and supersonic aircraft. "
                    "Treat the subsonic results (stall speed, L/D, loiter) as meaningful and the "
                    "high-speed ones as an upper bound only.")
    if jet and s["service_ceiling_m"] > 14000:
        warn.append("Above roughly 14 km the simple thrust lapse and the missing compressibility drag both "
                    "flatter the aircraft; the real service ceiling will be lower.")
    figs = [_png(plots.plot_drag_polar_and_LD(ac)),
            _png(plots.plot_power_curves(ac, (0.0, p["h_cruise"], min(2 * p["h_cruise"] + 1000, s["absolute_ceiling_m"] * 0.9)))),
            _png(plots.plot_climb(ac, s["absolute_ceiling_m"]))]
    tw = f", T/W = {p['thrust_kN']*1e3/ac.W:.2f}" if jet else ""
    return json.dumps({"rows": rows, "figs": figs, "warnings": warn,
                       "meta": f"AR = {AR:.2f}, W/S = {ac.wing_loading:.0f} N/m\u00b2, k = {ac.polar.k:.4f}{tw}"})


def run_sizing(js):
    p = json.loads(js)
    req = sz.MissionRequirements(p["range_km"] * 1e3, p["payload"], p["V_cruise"], p["h_cruise"], p["V_stall"],
                                 p["RC"], p["S_G"], p["h_ceiling"], p["loiter_min"] * 60.0)
    da = sz.DesignAssumptions(p["CD0"], p["AR"], p["e"], p["CL_max"], p["CL_max_TO"], p["eta_p"],
                              p["sfc_kg_per_kWh"] / 3.6e6, eta_p_TO=p["eta_p_TO"], empty_mass_fraction=p["empty_frac"])
    r = sz.size_aircraft(req, da)
    need = {k: float(np.interp(r.wing_loading, r.curves.WS, v)) for k, v in r.curves.PW.items()}
    rows = [
        ["Design wing loading W/S", f"{r.wing_loading:.0f} N/m²", "set by the stall-speed limit"],
        ["Required power loading P/W", f"{r.power_to_weight:.2f} W/N", f"governing constraint: {r.governing_constraint}"],
        ["Take-off mass", f"{r.takeoff_mass:.1f} kg", f"= payload {req.payload_mass:g} + fuel {r.fuel_mass:.2f} + empty {r.empty_mass:.1f}"],
        ["Wing area", f"{r.wing_area:.3f} m²", f"span {r.span:.2f} m (AR {da.AR:g})"],
        ["Installed shaft power", f"{r.shaft_power:.0f} W", f"{r.shaft_power/745.7:.2f} hp"],
        ["Cruise C_L / L/D", f"{r.CL_cruise:.2f} / {r.LD_cruise:.1f}", f"(L/D)max would be {da.polar.LD_max:.1f}"],
    ] + [[f"P/W needed for {k}", f"{v:.2f} W/N", ""] for k, v in need.items()]
    fig = plots.plot_constraint_diagram(r.curves, (r.wing_loading, r.power_to_weight, r.governing_constraint),
                                        PW_max=max(2.2 * r.power_to_weight, 5))
    return json.dumps({"rows": rows, "figs": [_png(fig)], "meta": ""})


def run_rocket(js):
    p = json.loads(js)
    m = rk.Motor.trapezoid(p["motor_name"], p["impulse"], p["burn_time"], p["peak_thrust"], p["prop_mass_g"] / 1e3, p["casing_mass_g"] / 1e3)
    veh = tj.RocketVehicle(p["name"], p["dry_mass_g"] / 1e3, m, p["Cd"], np.pi * (p["diameter_mm"] / 2e3) ** 2)
    res = tj.simulate(veh, p["launch_angle"], p["rail_length"])
    nodrag = tj.simulate(tj.RocketVehicle("nd", veh.dry_mass, m, 0.0, veh.ref_area), p["launch_angle"], p["rail_length"], stop_at_apogee=True)
    dv = rk.delta_v(m.isp, veh.liftoff_mass, veh.burnout_mass)
    rows = [
        ["Motor", f"I_t = {m.total_impulse:.1f} N·s, t_b = {m.burn_time:.2f} s", f"average thrust {m.average_thrust:.0f} N, Isp {m.isp:.0f} s"],
        ["Lift-off / burnout mass", f"{veh.liftoff_mass*1e3:.0f} g / {veh.burnout_mass*1e3:.0f} g", f"initial thrust-to-weight {m.average_thrust/(veh.liftoff_mass*G0):.1f}"],
        ["Ideal Δv (Tsiolkovsky)", f"{dv:.0f} m/s", "no gravity, no drag"],
        ["Burnout", f"{res.burnout_speed:.0f} m/s at {res.burnout_altitude:.0f} m", f"max Mach {res.max_mach:.2f}, max {res.max_accel_g:.1f} g, max q {res.max_q/1e3:.1f} kPa"],
        ["Apogee", f"{res.apogee:.0f} m", f"at t = {res.t_apogee:.1f} s"],
        ["Drag-free apogee", f"{nodrag.apogee:.0f} m", f"drag costs {100*(1-res.apogee/nodrag.apogee):.0f} % of altitude"],
        ["Ballistic impact (no parachute)", f"{res.impact_range:.0f} m downrange" if res.impact_range is not None else "—", f"t = {res.t_impact:.1f} s" if res.t_impact else ""],
    ]
    warn = []
    if m.average_thrust / (veh.liftoff_mass * G0) < 5:
        warn.append("Thrust-to-weight below 5: the rocket leaves the rail slowly and may weathercock. "
                    "Real launches want at least 5.")
    if res.max_mach > 0.8:
        warn.append(f"Max Mach {res.max_mach:.2f}: a constant C_D is no longer valid, because the transonic "
                    "drag rise is not modelled. The real apogee will be lower.")
    figs = [_png(plots.plot_thrust_curve(m)), _png(plots.plot_trajectory(res, veh.name))]
    return json.dumps({"rows": rows, "figs": figs, "meta": "", "warnings": warn})


def run_deltav(js):
    p = json.loads(js)
    isp = p["isp"]
    out = []
    if p["mode"] == "dv":
        dv = rk.delta_v(isp, p["m0"], p["mf"])
        out = [["Δv", f"{dv:.0f} m/s", f"mass ratio {p['m0']/p['mf']:.3f}"],
               ["Propellant mass fraction", f"{1 - p['mf']/p['m0']:.3f}", ""],
               ["Effective exhaust velocity", f"{isp*G0:.0f} m/s", "c = Isp · g0"]]
    else:
        mp = rk.propellant_mass_for_dv(p["dv"], isp, p["mf"])
        out = [["Propellant required", f"{mp:.1f} kg", f"for Δv = {p['dv']:.0f} m/s and final mass {p['mf']:g} kg"],
               ["Initial mass", f"{p['mf'] + mp:.1f} kg", f"mass ratio {rk.mass_ratio(p['dv'], isp):.3f}"],
               ["Propellant mass fraction", f"{rk.propellant_mass_fraction(p['dv'], isp):.3f}", ""]]
    dv = np.linspace(0, 12000, 300)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for i in (200, 250, 300, 350, 450):
        ax.plot(dv / 1e3, rk.propellant_mass_fraction(dv, i), label=f"Isp {i} s", lw=1.2 if i != isp else 2.5)
    if isp not in (200, 250, 300, 350, 450):
        ax.plot(dv / 1e3, rk.propellant_mass_fraction(dv, isp), "k", lw=2.5, label=f"Isp {isp:g} s (yours)")
    ax.set_xlabel("Δv [km/s]"); ax.set_ylabel("propellant mass fraction"); ax.set_title("Tsiolkovsky: propellant fraction vs Δv"); ax.legend(fontsize=8)
    return json.dumps({"rows": out, "figs": [_png(fig)], "meta": ""})


def run_atmos(js):
    p = json.loads(js)
    s = atm.isa(p["h"])
    rows = [["Temperature", f"{s.T:.2f} K", f"{s.T-273.15:.1f} °C"], ["Pressure", f"{s.p:.1f} Pa", f"{s.p/101325:.4f} atm"],
            ["Density", f"{s.rho:.5f} kg/m³", f"σ = {s.sigma:.4f}"], ["Speed of sound", f"{s.a:.1f} m/s", ""],
            ["Dynamic viscosity", f"{s.mu:.3e} Pa·s", ""]]
    return json.dumps({"rows": rows, "figs": [_png(plots.plot_atmosphere())], "meta": f"geopotential altitude {s.H:.0f} m"})
