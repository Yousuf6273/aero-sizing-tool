"""aerosizing: research-grounded aircraft performance/sizing and rocket trajectory tool.

Modules
-------
atmosphere            ISA / U.S. Standard Atmosphere 1976 (0-86 km)
aerodynamics          drag polar, lift curve, L/D
aircraft_performance  thrust/power required & available, climb, ceiling, Breguet
sizing                constraint diagram + mission weight sizing
rocket                Tsiolkovsky, Isp, thrust, nozzle relations, motor model
trajectory            2-D point-mass rocket trajectory (scipy RK45, RK4 cross-check)
plots                 matplotlib helpers
"""
from . import atmosphere, aerodynamics, aircraft_performance, sizing, rocket, trajectory, plots  # noqa: F401

__version__ = "0.1.0"
