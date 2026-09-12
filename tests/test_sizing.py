import numpy as np
import pytest

from aerosizing import sizing as sz
from aerosizing.aerodynamics import DragPolar
from aerosizing.atmosphere import G0, RHO0


def test_stall_wing_loading():
    assert sz.stall_wing_loading_limit(20.0, 1.5) == pytest.approx(0.5 * 1.225 * 400 * 1.5)


def test_cruise_constraint_minimum_is_one_over_LDmax():
    p = DragPolar(0.03, 8.0, 0.8)
    WS = np.linspace(50, 3000, 20000)
    tw = sz.tw_cruise(WS, 50.0, RHO0, p)
    assert tw.min() == pytest.approx(1.0 / p.LD_max, rel=1e-4)
    q = 0.5 * RHO0 * 50 ** 2
    assert WS[np.argmin(tw)] == pytest.approx(q * p.CL_LDmax, rel=2e-3)


def test_climb_constraint_adds_Vv_over_V():
    p = DragPolar(0.03, 8.0, 0.8)
    assert sz.tw_climb(800.0, 40.0, RHO0, p, 4.0) == pytest.approx(sz.tw_cruise(800.0, 40.0, RHO0, p) + 0.1)


def test_takeoff_constraint_hand_calc():
    # Gudmundsson eq. 3-9 with WS=1000, S_G=300, CLmax_TO=1.8, CD_TO=0.05, CL_TO=0.5, mu=0.04
    tw = sz.tw_takeoff(1000.0, 300.0, RHO0, 1.8, 0.05, 0.5, 0.04)
    expect = 1.21 * 1000 / (G0 * RHO0 * 1.8 * 300) + 0.605 / 1.8 * (0.05 - 0.04 * 0.5) + 0.04
    assert tw == pytest.approx(expect)


def test_fuel_fraction_zero_range():
    req = sz.MissionRequirements(0.0, 1.0, 30.0, 0.0, 15.0, 3.0, 100.0, 3000.0)
    da = sz.DesignAssumptions(0.03, 8, 0.8, 1.4, 1.6, 0.75, 1e-7)
    assert sz.fuel_fraction(req, da, 10.0) == pytest.approx(1.06 * (1 - 0.97 * 0.985 * 0.995))


def test_takeoff_mass_closed_form():
    m0 = sz.takeoff_mass(10.0, 0.2, 0.5)
    assert m0 == pytest.approx(10.0 / (1 - 0.2 - 0.5))


def test_size_aircraft_consistency():
    req = sz.MissionRequirements(100e3, 4.0, 30.0, 500.0, 14.0, 4.0, 60.0, 4000.0, 1800.0)
    da = sz.DesignAssumptions(0.035, 9.0, 0.8, 1.4, 1.6, 0.75, 1.1e-7, empty_mass_fraction=0.6)
    r = sz.size_aircraft(req, da)
    assert r.wing_loading == pytest.approx(sz.stall_wing_loading_limit(14.0, 1.4))
    assert r.wing_area * r.wing_loading == pytest.approx(r.takeoff_mass * G0)
    assert r.takeoff_mass == pytest.approx(req.payload_mass + r.fuel_mass + r.empty_mass, rel=1e-6)
    assert r.governing_constraint in r.curves.PW
