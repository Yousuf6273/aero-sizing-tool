import numpy as np
import pytest

from aerosizing import aircraft_performance as ap
from aerosizing.atmosphere import G0, RHO0, density


@pytest.fixture
def light_single():
    return ap.Aircraft("test single", 1000.0, 16.0, 7.5, 0.8, 0.03, 1.5,
                       ap.PistonProp(120e3, 0.8), c_p=7.6e-8, fuel_mass=120.0)


def test_stall_speed_hand_calc(light_single):
    W = 1000.0 * G0
    Vs = np.sqrt(2 * W / (RHO0 * 16.0 * 1.5))
    assert ap.stall_speed(light_single) == pytest.approx(Vs)


def test_min_thrust_required_equals_W_over_LDmax(light_single):
    ac = light_single
    V = np.linspace(ap.stall_speed(ac), 120, 4000)
    assert ap.thrust_required(ac, V).min() == pytest.approx(ac.W / ac.polar.LD_max, rel=1e-4)


def test_max_speed_is_power_balance_root(light_single):
    V = ap.max_speed(light_single, 0.0)
    assert ap.power_available(light_single, V, 0.0) == pytest.approx(ap.power_required(light_single, V, 0.0), rel=1e-6)
    assert ap.rate_of_climb(light_single, V, 0.0) == pytest.approx(0.0, abs=1e-6)


def test_service_ceiling_definition(light_single):
    h = ap.service_ceiling(light_single)
    assert ap.max_rate_of_climb(light_single, h)[0] == pytest.approx(0.508, abs=2e-3)
    assert ap.absolute_ceiling(light_single) > h


def test_piston_lapse():
    assert ap.piston_power_lapse(1.0) == pytest.approx(1.0)
    assert ap.piston_power_lapse(0.0) == 0.0


def test_breguet_range_prop_hand_calc():
    # eta=0.8, c_p=7.6e-8 kg/(W s), L/D=12, W0/W1=1.2
    R = ap.breguet_range_prop(0.8, 7.6e-8, 12.0, 1.2, 1.0)
    assert R == pytest.approx(0.8 / (G0 * 7.6e-8) * 12.0 * np.log(1.2), rel=1e-12)
    assert R == pytest.approx(2.348e6, rel=2e-3)


def test_breguet_jet_endurance():
    assert ap.breguet_endurance_jet(2e-5, 15.0, 2.0, 1.0) == pytest.approx(15.0 / 2e-5 * np.log(2.0))


def test_jet_thrust_lapse():
    j = ap.Turbojet(10e3)
    assert j.thrust_available(100.0, density(0.0)) == pytest.approx(10e3)
    assert j.thrust_available(100.0, density(11000.0)) < 3.5e3


@pytest.fixture
def fighter_like():
    """High thrust-to-weight jet: top speed lies well beyond 6x the stall speed,
    which the adaptive speed bracket must still find."""
    return ap.Aircraft("fighter", 27200.0, 52.49, 19.55 ** 2 / 52.49, 0.75, 0.024, 1.6,
                       ap.Turbojet(186e3, 0.8), c_t=0.67 / 3600.0, fuel_mass=7348.0)


def test_adaptive_bracket_finds_high_jet_top_speed(fighter_like):
    V = ap.max_speed(fighter_like, 0.0)
    assert V > 6.0 * ap.stall_speed(fighter_like, 0.0)      # beyond the old fixed bracket
    assert ap.power_available(fighter_like, V, 0.0) == pytest.approx(
        ap.power_required(fighter_like, V, 0.0), rel=1e-6)


def test_jet_best_range_CL_is_below_LDmax_CL():
    from aerosizing.aerodynamics import DragPolar
    p = DragPolar(0.024, 7.28, 0.75)
    assert p.CL_best_range_jet == pytest.approx(p.CL_LDmax / np.sqrt(3))
    CL = np.linspace(0.05, 2.0, 20000)
    f = np.sqrt(CL) / p.CD(CL)
    assert p.CL_best_range_jet == pytest.approx(CL[np.argmax(f)], rel=2e-3)
    assert p.CL_max_endurance_jet == p.CL_best_range_jet      # deprecated alias


def test_jet_range_endurance_matches_closed_form(fighter_like):
    ac = fighter_like
    out = ap.jet_range_endurance(ac, 10000.0)
    W0, W1 = ac.W, (ac.mass - ac.fuel_mass) * G0
    assert out["endurance_s"] == pytest.approx(
        ap.breguet_endurance_jet(ac.c_t, ac.polar.LD_max, W0, W1))
    assert out["range_m"] > 0 and out["endurance_s"] > 0


def test_performance_summary_uses_jet_breguet(fighter_like):
    s = ap.performance_summary(fighter_like, 10000.0)
    assert "range_m" in s and "endurance_s" in s
    assert s["range_m"] == pytest.approx(ap.jet_range_endurance(fighter_like, 10000.0)["range_m"])
