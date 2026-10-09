"""Doctor-facing conceptual dashboard. Run: streamlit run app.py"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from glycotwin.twin import update_and_forecast

st.set_page_config(page_title="GlycoTwin-IN", layout="wide")
st.title("GlycoTwin-IN")
st.caption("Conceptual clinician view. Synthetic patients only. Not a medical device and not for clinical use.")

ehr = pd.read_csv(ROOT / "sample_data" / "synthetic_ehr.csv")
cgm = pd.read_csv(ROOT / "sample_data" / "synthetic_cgm.csv")

left, right = st.columns([1, 2])
with left:
    pid = st.selectbox("Virtual patient", ehr["patient_id"])
    row = ehr[ehr.patient_id == pid].iloc[0]
    carbs = st.slider("Declared meal carbohydrate (g)", 20, 140, int(row.meal_carbs_g), 5)
    st.markdown(
        f"**Age** {int(row.age)} · **Sex** {row.sex} · **BMI** {row.bmi}  \n"
        f"**HbA1c** {row.hba1c_pct}% · **Fasting glucose** {row.fasting_glucose_mg_dl} mg/dL  \n"
        f"**Duration** {row.diabetes_duration_y} y · **Metformin** {'yes' if row.on_metformin else 'no'}  \n"
        f"**Sleep** {row.sleep_h} h · **Resting HR** {row.resting_hr_bpm} bpm · **Steps, prior 2 h** {int(row.steps_prev_2h)}"
    )
series = cgm[cgm.patient_id == pid]
twin = update_and_forecast(row, series, carbs_g=carbs)
with right:
    flag = twin["predicted_peak_mg_dl"] >= 180
    st.metric("Predicted peak in 120 min", f"{twin['predicted_peak_mg_dl']:.0f} mg/dL")
    st.metric("Minutes forecast at or above 180", twin["minutes_above_180"])
    if flag:
        st.error("Twin flag: postprandial hyperglycaemia risk within 2 hours. This is a simulation flag, not a diagnosis.")
    else:
        st.success("Twin flag: forecast peak stays below 180 mg/dL on this meal scenario.")
    chart = pd.DataFrame({"minute": twin["horizon_min"], "twin_forecast_mg_dl": twin["forecast_mg_dl"]})
    observed = series[series.minute_from_meal <= 0][["minute_from_meal", "cgm_mg_dl"]].rename(
        columns={"minute_from_meal": "minute", "cgm_mg_dl": "observed_cgm"}
    )
    st.line_chart(chart.set_index("minute"))
    st.line_chart(observed.set_index("minute"))
    st.caption(
        f"Updated insulin-sensitivity estimate {twin['si_hat']:.2e} per min per µU/mL "
        f"(EHR prior {twin['si_prior']:.2e}). Fit RMSE {twin['fit_rmse']:.1f}."
    )
st.warning(
    "Data are synthetic. The 180 mg/dL line is an operational flag aligned with a common post-meal target, "
    "not a validated diagnostic cut-off for this prototype."
)
