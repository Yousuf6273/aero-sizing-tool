"""ISA checks against U.S. Standard Atmosphere 1976 tables (geopotential altitude)."""
import numpy as np
import pytest

from aerosizing import atmosphere as atm

# (H_geopotential [m], T [K], p [Pa], rho [kg/m^3]) - USSA-1976 Table I
TABLE = [
    (0.0, 288.15, 101325.0, 1.2250),
    (5000.0, 255.65, 54019.9, 0.73612),
    (11000.0, 216.65, 22632.1, 0.36392),
    (20000.0, 216.65, 5474.89, 0.088035),
    (32000.0, 228.65, 868.02, 0.013225),
    (47000.0, 270.65, 110.91, 0.0014275),
    (51000.0, 270.65, 66.939, 0.00086160),
    (71000.0, 214.65, 3.9564, 0.000064211),
]


@pytest.mark.parametrize("H,T,p,rho", TABLE)
def test_isa_table_values(H, T, p, rho):
    s = atm.isa(H, geometric=False)
    assert s.T == pytest.approx(T, rel=1e-4)
    assert s.p == pytest.approx(p, rel=2e-4)
    assert s.rho == pytest.approx(rho, rel=3e-4)


def test_sea_level_speed_of_sound_and_viscosity():
    s = atm.isa(0.0)
    assert s.a == pytest.approx(340.294, rel=1e-5)
    assert s.mu == pytest.approx(1.7894e-5, rel=1e-3)   # USSA-1976 Table I


def test_geometric_vs_geopotential():
    # 5000 m geometric = 4996.07 m geopotential (USSA-1976 eq. 18)
    assert atm.geometric_to_geopotential(5000.0) == pytest.approx(4996.07, abs=0.05)
    assert atm.isa(5000.0).p == pytest.approx(54048.3, rel=2e-4)


def test_pressure_monotonic_and_vectorised():
    h = np.linspace(0, 86000, 400)
    s = atm.isa(h)
    assert np.all(np.diff(s.p) < 0)
    assert np.all(np.diff(s.rho) < 0)
    assert s.T.shape == h.shape


def test_out_of_range_raises():
    with pytest.raises(ValueError):
        atm.isa(90000.0)
