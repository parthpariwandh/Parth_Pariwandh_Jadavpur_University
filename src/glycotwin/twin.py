"""Patient-specific twin: EHR prior, CGM update, 120-minute forecast."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from glycotwin.minimal_model import simulate_glucose


def prior_from_ehr(row: pd.Series) -> dict:
    hba1c = float(row["hba1c_pct"])
    bmi = float(row["bmi"])
    fasting = float(row["fasting_glucose_mg_dl"])
    si = 4.2e-4 * np.exp(-0.25 * (hba1c - 7.0) - 0.035 * (bmi - 25))
    if int(row["on_metformin"]) == 1:
        si *= 1.08
    sg = float(np.clip(0.017 - 0.001 * (hba1c - 7.0), 0.008, 0.025))
    return {
        "gb": fasting,
        "ib": 12.0,
        "sg": sg,
        "si": float(np.clip(si, 5e-5, 8e-4)),
        "p2": 0.025,
        "tau_min": 45.0,
        "delta_i": float(np.clip(16 - 1.2 * (hba1c - 7), 5, 25)),
        "tau_i": 40.0,
        "bioavailability": 0.78,
        "volume_dl": 150.0,
    }


def _fit_window(series: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    pre = series[series["minute_from_meal"] <= 0].sort_values("minute_from_meal")
    # Use the last 60 minutes before the meal plus the meal instant.
    window = pre[pre["minute_from_meal"] >= -60]
    return window["minute_from_meal"].to_numpy(float), window["cgm_mg_dl"].to_numpy(float)


def update_and_forecast(row: pd.Series, series: pd.DataFrame, carbs_g: float | None = None) -> dict:
    """Fit insulin sensitivity on the pre-meal CGM window and roll the twin forward."""
    prior = prior_from_ehr(row)
    carbs = float(row["meal_carbs_g"] if carbs_g is None else carbs_g)
    t_obs, g_obs = _fit_window(series)
    # Activity modifier the twin is allowed to see: steps slightly raise SI.
    activity = 1.0 + 0.08 * np.tanh((float(row["steps_prev_2h"]) - 800) / 1200)

    def loss(log_si: float) -> float:
        si = np.exp(log_si) * activity
        pred = simulate_glucose(
            t_obs,
            meal_time=10_000,
            carbs_g=0.0,
            gb=prior["gb"],
            ib=prior["ib"],
            sg=prior["sg"],
            si=si,
            p2=prior["p2"],
            tau_min=prior["tau_min"],
            delta_i=prior["delta_i"],
            tau_i=prior["tau_i"],
            bioavailability=prior["bioavailability"],
            volume_dl=prior["volume_dl"],
            g0=float(g_obs[0]),
        )
        reg = 0.15 * (log_si - np.log(prior["si"])) ** 2
        return float(np.mean((pred - g_obs) ** 2) + reg)

    fit = minimize_scalar(loss, bounds=(np.log(4e-5), np.log(1e-3)), method="bounded", options={"xatol": 1e-3})
    si_hat = float(np.exp(fit.x) * activity)
    horizon = np.arange(0, 125, 5)
    forecast = simulate_glucose(
        horizon,
        meal_time=0.0,
        carbs_g=carbs,
        gb=prior["gb"],
        ib=prior["ib"],
        sg=prior["sg"],
        si=si_hat,
        p2=prior["p2"],
        tau_min=prior["tau_min"],
        delta_i=prior["delta_i"],
        tau_i=prior["tau_i"],
        bioavailability=prior["bioavailability"],
        volume_dl=prior["volume_dl"],
        g0=float(series.loc[series["minute_from_meal"] == 0, "cgm_mg_dl"].iloc[0]),
    )
    peak = float(np.max(forecast))
    time_above = int(np.sum(forecast >= 180.0) * 5)
    return {
        "si_hat": si_hat,
        "si_prior": prior["si"],
        "fit_rmse": float(np.sqrt(max(fit.fun, 0.0))),
        "predicted_peak_mg_dl": peak,
        "minutes_above_180": time_above,
        "predicted_g_120": float(forecast[-1]),
        "spike_flag": int(peak >= 180.0),
        "horizon_min": horizon,
        "forecast_mg_dl": forecast,
    }
