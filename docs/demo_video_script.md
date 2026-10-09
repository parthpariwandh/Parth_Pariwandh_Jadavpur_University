# Demo video script

Target length: 20 minutes, to cover both the form item (15–20 minutes, unlisted YouTube) and the brief (minimum 20 minutes). Record yourself speaking. Do not rely on an AI voice. Upload as unlisted, then paste the URL into the README line marked for the video and into the Unstop form.

0:00–1:00. Title slide. Name, Jadavpur University, Mechanical Engineering, final year, team of one. Competition name. One sentence: GlycoTwin-IN forecasts whether a virtual patient will cross 180 mg/dL within two hours of a logged meal.

1:00–3:30. Problem. ICMR-INDIAB-17: 11.4% weighted prevalence, about 101 million adults with diabetes. HbA1c does not answer the next-meal question. Users: a clinician in a decision-support sketch, not a patient self-treatment app.

3:30–6:00. What is implemented. Two streams: synthetic EHR and synthetic CGM plus sleep, heart rate, and steps. Bergman twin. 120-minute roll-forward. Clinician view. Say clearly that no live wearable and no hospital connection exist.

6:00–9:00. Equations on the model slide. Define G, X, SI, SG, Ra. Explain the EHR prior and the 60-minute sensitivity update. Explain the generator is richer than the twin, so this is not a fit to the same equation.

9:00–12:30. Repository walk-through. README, src/glycotwin, scripts/run_experiment.py, sample_data, results/metrics.json, app.py, both PDFs, MIT licence. Run the experiment command on camera if the machine is ready, or show the already written metrics file and say it was produced by that command.

12:30–16:00. Dashboard. Open the Streamlit app or docs/clinician_dashboard.html. Show SYN-109 and SYN-044. Move the carbohydrate slider. Read the flag and the disclaimer. Do not call the flag a diagnosis.

16:00–18:30. Results slide. Test n = 48. Twin physiology AUROC 0.976, EHR logistic 0.945, hybrid gradient boosting 0.936. Peak MAE 17.1 mg/dL. Bootstrap intervals are wide. Prevalence is 0.73, so accuracy would be a weak summary. These numbers are simulation results.

18:30–20:00. Limits and close. Synthetic data, small test set, no external cohort, no clinical validation, MIT licence, public repo. What a full deployment would add, and what this submission does not claim.
