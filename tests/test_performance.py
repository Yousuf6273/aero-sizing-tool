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
