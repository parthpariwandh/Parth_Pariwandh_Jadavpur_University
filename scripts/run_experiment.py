"""Train baselines and the hybrid twin classifier. Writes measured metrics only."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from glycotwin.synthetic import make_cohort
from glycotwin.twin import update_and_forecast

ROOT = Path(__file__).resolve().parents[1]
EHR_FEATURES = ["age", "bmi", "diabetes_duration_y", "hba1c_pct", "fasting_glucose_mg_dl", "on_metformin", "meal_carbs_g"]
WEARABLE_FEATURES = ["sleep_h", "resting_hr_bpm", "steps_prev_2h"]
TWIN_FEATURES = ["si_hat", "predicted_peak_mg_dl", "minutes_above_180", "predicted_g_120", "fit_rmse"]


def build_table(ehr: pd.DataFrame, series: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in ehr.iterrows():
        patient_series = series[series["patient_id"] == row["patient_id"]]
        twin = update_and_forecast(row, patient_series)
        records.append(
            {
                **row.to_dict(),
                "si_hat": twin["si_hat"],
                "predicted_peak_mg_dl": twin["predicted_peak_mg_dl"],
                "minutes_above_180": twin["minutes_above_180"],
                "predicted_g_120": twin["predicted_g_120"],
                "fit_rmse": twin["fit_rmse"],
                "twin_flag": twin["spike_flag"],
            }
        )
    return pd.DataFrame(records)


def _metrics(y_true: np.ndarray, proba: np.ndarray, threshold: float = 0.5) -> dict:
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    return {
        "n": int(len(y_true)),
        "prevalence": round(float(np.mean(y_true)), 4),
        "auroc": round(float(roc_auc_score(y_true, proba)), 4) if len(np.unique(y_true)) > 1 else None,
        "auprc": round(float(average_precision_score(y_true, proba)), 4),
        "brier": round(float(brier_score_loss(y_true, proba)), 4),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "specificity": round(float(spec), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "threshold": threshold,
    }


def run(seed: int = 2026) -> dict:
    ehr, series = make_cohort(160, seed)
    table = build_table(ehr, series)
    rng = np.random.default_rng(seed)
    ids = table["patient_id"].to_numpy()
    rng.shuffle(ids)
    test_ids = set(ids[:48])
    train = table[~table["patient_id"].isin(test_ids)]
    test = table[table["patient_id"].isin(test_ids)]
    y_train = train["spike_120min"].to_numpy(int)
    y_test = test["spike_120min"].to_numpy(int)

    ehr_model = Pipeline(
        [("scale", StandardScaler()), ("clf", LogisticRegression(max_iter=500, class_weight="balanced"))]
    )
    ehr_model.fit(train[EHR_FEATURES], y_train)
    ehr_proba = ehr_model.predict_proba(test[EHR_FEATURES])[:, 1]

    hybrid = GradientBoostingClassifier(n_estimators=120, max_depth=2, learning_rate=0.06, random_state=seed)
    hybrid_cols = EHR_FEATURES + WEARABLE_FEATURES + TWIN_FEATURES
    hybrid.fit(train[hybrid_cols], y_train)
    hybrid_proba = hybrid.predict_proba(test[hybrid_cols])[:, 1]

    # Physiology-only score: twin peak mapped through a logistic fit on the training set.
    phys = Pipeline(
        [("scale", StandardScaler()), ("clf", LogisticRegression(max_iter=400))]
    )
    phys.fit(train[["predicted_peak_mg_dl", "minutes_above_180"]], y_train)
    phys_proba = phys.predict_proba(test[["predicted_peak_mg_dl", "minutes_above_180"]])[:, 1]

    peak_mae = float(np.mean(np.abs(test["predicted_peak_mg_dl"] - test["true_peak_mg_dl"])))
    peak_rmse = float(np.sqrt(np.mean((test["predicted_peak_mg_dl"] - test["true_peak_mg_dl"]) ** 2)))

    out = {
        "seed": seed,
        "n_patients": int(len(table)),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "train_prevalence": round(float(y_train.mean()), 4),
        "test_prevalence": round(float(y_test.mean()), 4),
        "peak_mae_mg_dl": round(peak_mae, 2),
        "peak_rmse_mg_dl": round(peak_rmse, 2),
        "ehr_logistic": _metrics(y_test, ehr_proba),
        "twin_physiology": _metrics(y_test, phys_proba),
        "hybrid_twin_ml": _metrics(y_test, hybrid_proba),
        "note": "All patients are synthetic. Metrics are simulation-study results, not clinical performance.",
    }
    data_dir = ROOT / "sample_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    ehr.to_csv(data_dir / "synthetic_ehr.csv", index=False)
    series.to_csv(data_dir / "synthetic_cgm.csv", index=False)
    table.to_csv(data_dir / "twin_feature_table.csv", index=False)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "metrics.json").write_text(json.dumps(out, indent=2))
    test.assign(hybrid_proba=hybrid_proba, ehr_proba=ehr_proba, phys_proba=phys_proba).to_csv(
        ROOT / "results" / "test_predictions.csv", index=False
    )
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    run()
