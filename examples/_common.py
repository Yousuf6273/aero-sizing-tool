"""Shared vehicle definitions for the examples, tests and notebook."""
import numpy as np

from aerosizing import aircraft_performance as ap, rocket as rk, sizing as sz, trajectory as tj

FIG_DIR = "figures"


def cessna_172s() -> ap.Aircraft:
    """Cessna 172S-like light single.

    Geometry and engine from public type data (MTOW 2550 lb = 1157 kg, S = 174 ft^2 =
    16.17 m^2, span 36 ft 1 in -> AR 7.32, Lycoming IO-360-L2A 180 hp = 134 kW, usable fuel
    53 US gal = 144 kg). Aerodynamic coefficients (C_D0 = 0.033, e = 0.75, C_Lmax = 1.6 clean)
    and propeller efficiency (0.78) are ASSUMED textbook-range values for a strut-braced
    fixed-gear single, not manufacturer data. BSFC 0.45 lb/(hp h) = 7.6e-8 kg/(W s).
    """
    return ap.Aircraft("Cessna 172S-like", mass=1157.0, S=16.17, AR=7.32, e=0.75, CD0=0.033,
                       CL_max=1.6, propulsion=ap.PistonProp(P_shaft_SL=134e3, eta_p=0.78),
                       c_p=7.6e-8, fuel_mass=144.0)


# Approximate published Cessna 172S figures (POH / type certificate), for sanity checks.
C172S_PUBLISHED = {
    "stall_speed_SL_mps": 53 * 0.5144,       # ~53 KCAS clean (Vs1)
    "max_speed_SL_mps": 126 * 0.5144,        # ~126 KTAS max level speed at sea level
    "max_RC_SL_mps": 730 * 0.00508,          # 730 ft/min
    "service_ceiling_m": 14000 * 0.3048,     # 14 000 ft
    "range_m": 640 * 1852.0,                 # ~640 nmi at 45 % power with reserves
}


def uav_mission() -> tuple[sz.MissionRequirements, sz.DesignAssumptions]:
    """Small gasoline fixed-wing survey UAV: 4 kg sensor payload, 150 km range, 30 min loiter."""
    req = sz.MissionRequirements(range_m=150e3, payload_mass=4.0, cruise_speed=30.0,
                                 cruise_altitude=1000.0, stall_speed=14.0, climb_rate_SL=4.0,
                                 takeoff_ground_roll=60.0, service_ceiling=4000.0, loiter_time_s=1800.0)
    # small two-stroke: BSFC ~0.9 lb/(hp h) = 1.5e-7 kg/(W s); small props eta ~0.7
    da = sz.DesignAssumptions(CD0=0.035, AR=9.0, e=0.80, CL_max=1.4, CL_max_TO=1.6, eta_p=0.70,
                              c_p=1.5e-7, eta_p_TO=0.55, empty_mass_fraction=0.60)
    return req, da


def g80_motor() -> rk.Motor:
    """AeroTech G80 (29 mm) approximated from catalogue data on thrustcurve.org:
    total impulse ~136.6 N s, average thrust ~80 N, peak ~116 N, burn ~1.7 s,
    propellant 62.5 g, loaded motor ~125 g. Curve shape is an idealised trapezoid."""
    return rk.Motor.trapezoid("AeroTech G80 (approx.)", total_impulse=136.6, burn_time=1.7,
                              peak_thrust=116.0, propellant_mass=0.0625, casing_mass=0.0625)


def mid_power_rocket() -> tj.RocketVehicle:
    """54 mm mid-power rocket: 600 g airframe+recovery+payload without motor, C_D 0.45."""
    return tj.RocketVehicle("54 mm mid-power rocket", dry_mass=0.60, motor=g80_motor(),
                            Cd=0.45, ref_area=np.pi * 0.027 ** 2)
