"""Synthetic EHR and wearable streams. Not real patients."""

from __future__ import annotations

import numpy as np
import pandas as pd

from glycotwin.minimal_model import simulate_glucose


def make_cohort(n_patients: int = 160, seed: int = 2026) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a synthetic Indian adult type 2 diabetes cohort and one meal event each.

    The generator is intentionally richer than the twin: gastric-emptying noise,
    a sleep/heart-rate stress term, and sensor bias are not in the twin equations.
    Ranges are literature-informed simulation bounds, not draws from ICMR microdata.
    """
    rng = np.random.default_rng(seed)
    age = rng.integers(32, 71, n_patients)
    sex = rng.choice(["F", "M"], n_patients)
    bmi = rng.normal(28.5, 3.2, n_patients).clip(21, 40)
    duration = rng.uniform(1.0, 18.0, n_patients)
    hba1c = rng.normal(8.1, 1.1, n_patients).clip(6.5, 12.0)
    fasting = (90 + 12 * (hba1c - 6.5) + rng.normal(0, 8, n_patients)).clip(100, 220)
    metformin = rng.random(n_patients) < 0.72
    rural = rng.random(n_patients) < 0.45

    # Ground-truth physiology. Higher HbA1c and BMI lower insulin sensitivity.
    sg = (0.018 - 0.0012 * (hba1c - 7.0) + rng.normal(0, 0.002, n_patients)).clip(0.006, 0.03)
    si = (4.5e-4 * np.exp(-0.28 * (hba1c - 7.0) - 0.04 * (bmi - 25)) * rng.uniform(0.75, 1.25, n_patients)).clip(4e-5, 9e-4)
    if metformin.any():
        si[metformin] *= 1.12
    p2 = rng.normal(0.025, 0.004, n_patients).clip(0.012, 0.04)
    tau = rng.normal(45, 10, n_patients).clip(25, 80)
    delta_i = (18 - 1.4 * (hba1c - 7) + rng.normal(0, 3, n_patients)).clip(4, 30)
    tau_i = rng.normal(40, 6, n_patients).clip(25, 60)
    bio = rng.normal(0.78, 0.05, n_patients).clip(0.6, 0.9)

    sleep_h = rng.normal(6.3, 1.1, n_patients).clip(3.5, 9.0)
    hr = rng.normal(78, 8, n_patients).clip(58, 110)
    steps_2h = rng.integers(80, 3500, n_patients)
    carbs = rng.choice([35, 50, 65, 80, 100, 120], n_patients, p=[0.12, 0.2, 0.24, 0.22, 0.14, 0.08])

    # Unmodeled stress: short sleep and high resting HR raise glucose appearance.
    stress = (0.015 * np.maximum(0, 6.5 - sleep_h) + 0.004 * np.maximum(0, hr - 80) - 0.00001 * steps_2h)
    stress = stress.clip(-0.05, 0.35)

    rows = []
    series = []
    pre_minutes = np.arange(0, 90, 5)
    horizon = np.arange(0, 125, 5)
    for i in range(n_patients):
        pid = f"SYN-{i:03d}"
        # 90 min pre-meal near fasting, then 120 min after a logged meal.
        baseline = simulate_glucose(
            pre_minutes,
            meal_time=10_000,
            carbs_g=0,
            gb=float(fasting[i]),
            ib=12.0,
            sg=float(sg[i]),
            si=float(si[i]),
            p2=float(p2[i]),
            tau_min=float(tau[i]),
            delta_i=float(delta_i[i]),
            tau_i=float(tau_i[i]),
            bioavailability=float(bio[i]),
            stress=float(stress[i]) * 0.2,
            g0=float(fasting[i]),
        )
        post = simulate_glucose(
            horizon,
            meal_time=0.0,
            carbs_g=float(carbs[i]),
            gb=float(fasting[i]),
            ib=12.0,
            sg=float(sg[i]),
            si=float(si[i]),
            p2=float(p2[i]),
            tau_min=float(tau[i]),
            delta_i=float(delta_i[i]),
            tau_i=float(tau_i[i]),
            bioavailability=float(bio[i]),
            stress=float(stress[i]),
            g0=float(baseline[-1]),
        )
        bias = rng.normal(0, 2.5)
        noise_pre = rng.normal(0, 5.5, baseline.size)
        noise_post = rng.normal(0, 5.5, post.size)
        observed_pre = baseline + bias + noise_pre
        observed_post = post + bias + noise_post
        peak = float(np.max(post[1:]))
        label = int(peak >= 180.0)
        rows.append(
            {
                "patient_id": pid,
                "age": int(age[i]),
                "sex": sex[i],
                "bmi": round(float(bmi[i]), 2),
                "diabetes_duration_y": round(float(duration[i]), 2),
                "hba1c_pct": round(float(hba1c[i]), 2),
                "fasting_glucose_mg_dl": round(float(fasting[i]), 1),
                "on_metformin": int(metformin[i]),
                "rural": int(rural[i]),
                "sleep_h": round(float(sleep_h[i]), 2),
                "resting_hr_bpm": round(float(hr[i]), 1),
                "steps_prev_2h": int(steps_2h[i]),
                "meal_carbs_g": int(carbs[i]),
                "true_si": float(si[i]),
                "true_peak_mg_dl": round(peak, 1),
                "spike_120min": label,
                "data_origin": "synthetic",
            }
        )
        for t, g in zip(pre_minutes - 90, observed_pre):
            series.append({"patient_id": pid, "minute_from_meal": int(t), "cgm_mg_dl": round(float(g), 2), "phase": "pre"})
        for t, g in zip(horizon, observed_post):
            series.append({"patient_id": pid, "minute_from_meal": int(t), "cgm_mg_dl": round(float(g), 2), "phase": "post"})
    return pd.DataFrame(rows), pd.DataFrame(series)
