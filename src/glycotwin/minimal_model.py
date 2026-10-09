"""Bergman minimal-model glucose–insulin dynamics with a two-compartment meal."""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def meal_appearance(t_min: np.ndarray, carbs_g: float, tau_min: float, bioavailability: float, volume_dl: float) -> np.ndarray:
    """Glucose rate of appearance in mg/dL/min. t_min is minutes after the meal."""
    t = np.asarray(t_min, dtype=float)
    ra = np.zeros_like(t)
    if carbs_g <= 0 or tau_min <= 0 or volume_dl <= 0:
        return ra
    dose_mg = carbs_g * 1000.0 * bioavailability
    positive = t > 0
    ra[positive] = (dose_mg / (volume_dl * tau_min**2)) * t[positive] * np.exp(-t[positive] / tau_min)
    return ra


def insulin_excursion(t_min: np.ndarray, ib: float, delta_i: float, tau_i: float) -> np.ndarray:
    """Simple endogenous insulin pulse above basal, µU/mL."""
    t = np.asarray(t_min, dtype=float)
    i = np.full_like(t, ib)
    positive = t > 0
    i[positive] = ib + delta_i * (t[positive] / tau_i) * np.exp(1.0 - t[positive] / tau_i)
    return i


def simulate_glucose(
    minutes: np.ndarray,
    meal_time: float,
    carbs_g: float,
    gb: float,
    ib: float,
    sg: float,
    si: float,
    p2: float,
    tau_min: float,
    delta_i: float,
    tau_i: float,
    bioavailability: float = 0.8,
    volume_dl: float = 150.0,
    stress: float = 0.0,
    g0: float | None = None,
) -> np.ndarray:
    """Forward-simulate plasma glucose (mg/dL) on an arbitrary minute grid.

    States follow the Bergman minimal model. `stress` is an additive glucose
    appearance used only by the data-generating process, not by the twin.
    """
    minutes = np.asarray(minutes, dtype=float)
    if minutes.size == 0:
        return np.array([])
    t0 = float(minutes[0])
    t1 = float(minutes[-1])
    if t1 <= t0:
        return np.full(minutes.shape, gb if g0 is None else g0)

    def rhs(_t, y):
        g, x = y
        dt = _t - meal_time
        ra = 0.0
        insulin = ib
        if dt > 0 and carbs_g > 0:
            dose_mg = carbs_g * 1000.0 * bioavailability
            ra = (dose_mg / (volume_dl * tau_min**2)) * dt * np.exp(-dt / tau_min)
            insulin = ib + delta_i * (dt / tau_i) * np.exp(1.0 - dt / tau_i)
        dg = -(sg + x) * g + sg * gb + ra + stress
        dx = -p2 * x + p2 * si * (insulin - ib)
        return [dg, dx]

    sol = solve_ivp(
        rhs,
        (t0, t1),
        [gb if g0 is None else g0, 0.0],
        t_eval=minutes,
        method="RK45",
        rtol=1e-4,
        atol=1e-4,
    )
    if not sol.success:
        # Fall back to a coarse Euler step so a stiff draw cannot crash the cohort.
        g = gb if g0 is None else g0
        x = 0.0
        out = np.empty(minutes.size)
        out[0] = g
        for i in range(1, minutes.size):
            dt = minutes[i] - minutes[i - 1]
            dg, dx = rhs(minutes[i - 1], [g, x])
            g = max(40.0, g + dt * dg)
            x = x + dt * dx
            out[i] = g
        return out
    return sol.y[0]
