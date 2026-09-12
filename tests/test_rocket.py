import numpy as np
import pytest
from scipy.integrate import trapezoid

from aerosizing import rocket as rk
from aerosizing.atmosphere import G0


def test_tsiolkovsky_hand_calc():
    # Isp=300 s, m0/mf = e -> dv = 300 * 9.80665 = 2941.995 m/s
    assert rk.delta_v(300.0, np.e, 1.0) == pytest.approx(300.0 * G0, rel=1e-12)
    # Sutton example-like: Isp=310 s, mass ratio 5 -> dv = 310*9.80665*ln5 = 4893 m/s
    assert rk.delta_v(310.0, 5.0, 1.0) == pytest.approx(4893.0, rel=1e-3)


def test_propellant_mass_roundtrip():
    mp = rk.propellant_mass_for_dv(3000.0, 250.0, 100.0)
    assert rk.delta_v(250.0, 100.0 + mp, 100.0) == pytest.approx(3000.0)
    assert rk.propellant_mass_fraction(3000.0, 250.0) == pytest.approx(mp / (100.0 + mp))


def test_staging_beats_single_stage_for_same_propellant():
    s1 = rk.Stage(1000.0, 100.0, 300.0)
    s2 = rk.Stage(200.0, 20.0, 300.0)
    dv2, parts = rk.multistage_delta_v([s1, s2], payload=50.0)
    dv1 = rk.delta_v(300.0, 1000 + 100 + 200 + 20 + 50, 100 + 20 + 50)
    assert dv2 > dv1 and len(parts) == 2


def test_thrust_relations():
    assert rk.thrust_from_isp(2.0, 250.0) == pytest.approx(2.0 * 250.0 * G0)
    assert rk.thrust(2.0, 2500.0, 50e3, 100e3, 0.1) == pytest.approx(5000.0 - 5000.0)


def test_ideal_nozzle_identity_isp_equals_ve_over_g0():
    # For optimum expansion (p_e = p_a) Isp = c* C_F / g0 must equal v_e / g0 exactly
    gamma, R, Tc, pc, pe = 1.2, 350.0, 3200.0, 5e6, 101325.0
    ve = rk.ideal_exit_velocity(gamma, R, Tc, pe, pc)
    cf = rk.thrust_coefficient(gamma, pc, pe, pe)
    cs = rk.characteristic_velocity(gamma, R, Tc)
    assert rk.isp_from_c_star_cf(cs, cf) == pytest.approx(ve / G0, rel=1e-10)
    assert 1.4 < cf < 1.9          # Sutton Fig. 3-6 range for pc/pe ~ 50
    assert 1.0 < rk.area_ratio(gamma, pe, pc) < 20.0


def test_motor_bookkeeping():
    m = rk.Motor.trapezoid("test", 100.0, 2.0, 80.0, 0.05, 0.05)
    assert m.total_impulse == pytest.approx(100.0, rel=1e-6)
    assert m.isp == pytest.approx(100.0 / (0.05 * G0))
    assert m.mass_at(0.0) == pytest.approx(0.10)
    assert m.mass_at(10.0) == pytest.approx(0.05)
    # burned propellant follows the cumulative impulse fraction
    t = 0.7
    frac = trapezoid(m.thrust_at(np.linspace(0, t, 5001)), np.linspace(0, t, 5001)) / 100.0
    assert m.propellant_remaining(t) == pytest.approx(0.05 * (1 - frac), rel=1e-4)
