"""Small hand-written integrators used to cross-check scipy (TUM MA9803 / Delft WBMT2049)."""
from __future__ import annotations

import numpy as np


def rk4(f, y0, t):
    """Classical 4th-order Runge-Kutta on a fixed grid t. f(t, y) -> dy/dt."""
    t = np.asarray(t, dtype=float)
    y = np.empty((len(t), len(y0)))
    y[0] = y0
    for i in range(len(t) - 1):
        h = t[i + 1] - t[i]
        k1 = f(t[i], y[i])
        k2 = f(t[i] + 0.5 * h, y[i] + 0.5 * h * k1)
        k3 = f(t[i] + 0.5 * h, y[i] + 0.5 * h * k2)
        k4 = f(t[i] + h, y[i] + h * k3)
        y[i + 1] = y[i] + h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return y
