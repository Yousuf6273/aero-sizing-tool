import numpy as np
import pytest

from aerosizing import rocket as rk, trajectory as tj
from aerosizing.atmosphere import G0


def constant_thrust_motor():
    # 60 N for 2 s, 30 g propellant -> Isp = 120/(0.03 g0) = 407.9 s
    return rk.Motor("const", np.array([0.0, 2.0, 2.001]), np.array([60.0, 60.0, 0.0]), 0.03, 0.05)


def test_vertical_no_drag_matches_analytic():
    m = constant_thrust_motor()
    veh = tj.RocketVehicle("nodrag", 0.5, m, 0.0, 1.0)
    res = tj.simulate(veh, 0.0, rail_length=0.0, stop_at_apogee=True)
    t = np.array([0.5, 1.0, 1.5, 2.0])
    v_num = np.interp(t, res.t, res.speed)
    assert v_num == pytest.approx(tj.vertical_no_drag_speed(m, 0.5, t), rel=2e-3)


def test_no_drag_apogee_is_ballistic_after_burnout():
    m = constant_thrust_motor()
    veh = tj.RocketVehicle("nodrag", 0.5, m, 0.0, 1.0)
    res = tj.simulate(veh, 0.0, rail_length=0.0, stop_at_apogee=True)
    h_expected = res.burnout_altitude + res.burnout_speed ** 2 / (2 * G0)
    assert res.apogee == pytest.approx(h_expected, rel=1e-3)


def test_rk4_agrees_with_scipy():
    m = rk.Motor.trapezoid("G80", 136.6, 1.7, 116.0, 0.0625, 0.0625)
    veh = tj.RocketVehicle("mid", 0.6, m, 0.45, np.pi * 0.027 ** 2)
    res = tj.simulate(veh, 5.0)
    _, y = tj.simulate_rk4(veh, 5.0, t_end=res.t_apogee, dt=0.002)
    assert y[-1, 1] == pytest.approx(res.apogee, rel=1e-3)


def test_drag_lowers_apogee_and_impact_follows_apogee():
    m = rk.Motor.trapezoid("G80", 136.6, 1.7, 116.0, 0.0625, 0.0625)
    A = np.pi * 0.027 ** 2
    hi = tj.simulate(tj.RocketVehicle("drag", 0.6, m, 0.45, A), 5.0)
    lo = tj.simulate(tj.RocketVehicle("nodrag", 0.6, m, 0.0, A), 5.0)
    assert hi.apogee < lo.apogee
    assert hi.t_impact is not None and hi.t_impact > hi.t_apogee
    assert hi.impact_range > 0
