import numpy as np
import pytest

from aerosizing import aerodynamics as aero


def test_LDmax_matches_numerical_maximum():
    p = aero.DragPolar(0.025, 8.0, 0.8)
    CL = np.linspace(0.05, 2.0, 20000)
    assert p.LD_max == pytest.approx(np.max(p.L_over_D(CL)), rel=1e-5)
    assert p.CL_LDmax == pytest.approx(CL[np.argmax(p.L_over_D(CL))], rel=1e-3)


def test_min_power_CL_is_sqrt3_times_LDmax_CL():
    p = aero.DragPolar(0.03, 7.0, 0.75)
    assert p.CL_min_power == pytest.approx(np.sqrt(3) * p.CL_LDmax)
    CL = np.linspace(0.05, 3.0, 20000)
    f = CL ** 1.5 / p.CD(CL)
    assert p.CL15_over_CD_max == pytest.approx(f.max(), rel=1e-5)


def test_hand_calculated_polar_point():
    # CD0=0.02, AR=10, e=0.8 -> k = 1/(pi*8) = 0.039789 ; CL=1 -> CD = 0.059789
    p = aero.DragPolar(0.02, 10.0, 0.8)
    assert p.k == pytest.approx(0.0397887, rel=1e-5)
    assert p.CD(1.0) == pytest.approx(0.0597887, rel=1e-5)
    assert p.LD_max == pytest.approx(1 / (2 * np.sqrt(0.02 * 0.0397887)), rel=1e-5)


def test_oswald_estimate_range():
    assert 0.7 < aero.oswald_efficiency_straight_wing(8.0) < 0.9
    assert aero.oswald_efficiency_straight_wing(6.0) > aero.oswald_efficiency_straight_wing(12.0)


def test_lift_curve_slope_limits():
    assert aero.lift_curve_slope(8.0) < 2 * np.pi
    assert aero.lift_curve_slope(1e9) == pytest.approx(2 * np.pi, rel=1e-6)
    # AR=8, a0=2pi: a = 2pi/(1+2/8) = 5.0265
    assert aero.lift_curve_slope(8.0) == pytest.approx(2 * np.pi / 1.25)


def test_required_CL_and_velocity_roundtrip():
    W, rho, S = 10000.0, 1.225, 16.0
    V = aero.velocity_for_CL(W, rho, 0.5, S)
    assert aero.required_CL(W, rho, V, S) == pytest.approx(0.5)
