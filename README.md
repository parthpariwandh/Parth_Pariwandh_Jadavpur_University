# GlycoTwin-IN

A hybrid Bergman digital twin that forecasts whether a virtual adult with type 2 diabetes will reach 180 mg/dL within 120 minutes of a logged meal.

Competition: Digital Twin Challenge 2026, Prototype and Code Submission, Happiest Health, Reimagining and Reforming Healthcare in India Summit 2026.

Repository folder name, as requested: Parth_Pariwandh_Jadavpur_University.

## Team details

Participant: Parth Pariwandh

Team size: 1

Team member: Parth Pariwandh

Role: individual participant and team leader

This is an individual submission. No additional members, supervisors, or collaborators are claimed.

## College information

Institution: Jadavpur University

Program: Bachelor of Mechanical Engineering

Year: Fourth year, final year

There is no incubator affiliation on this entry. Jadavpur University is the college. This repository is not an official university product and does not imply an institutional endorsement.

## Project title

GlycoTwin-IN: a hybrid Bergman digital twin for two-hour postprandial hyperglycaemia risk.

## Problem statement

Clinic HbA1c summarises months of glucose. It does not say what the next logged meal is likely to do in the following two hours. ICMR-INDIAB-17, a national survey of adults aged 20 and older, reported a weighted diabetes prevalence of 11.4 percent, about 101 million people with diabetes and 136 million with prediabetes (Anjana et al., Lancet Diabetes and Endocrinology, 2023). Post-meal spikes are a routine part of that burden.

Current finger-stick or visit-based review sees the excursion after it has happened. A wearable trace without a physiological state has no natural way to roll a declared meal forward. The prototype treats the person as a small dynamical system: a glucose and insulin-action state, initialised from a static record, updated from a recent trace, then simulated 120 minutes ahead.

Intended user: a clinician looking at a decision-support sketch. Expected benefit, if a later real-data study supported it, would be an earlier flag before a post-meal peak, not an automated prescription. That benefit is not demonstrated here.

Assumptions: one logged meal, carbohydrate mass known, glucose the only chemical observation, and a 180 mg/dL operational flag. That flag follows a commonly cited 1–2 hour post-meal target. It is not a diagnosis and not a claim that this cut is optimal.

Evaluation: a held-out simulation study. Discrimination, calibration-style Brier score, and peak error. No clinical outcome was measured.

## Healthcare use case

Localised condition: type 2 diabetes, postprandial hyperglycaemia.

Population in the prototype: synthetic adults with India-relevant simulation ranges for age, BMI, HbA1c, and fasting glucose. These are not draws from ICMR microdata and not real patients.

Adverse event: interstitial or plasma glucose at or above 180 mg/dL at any 5-minute step in the 120 minutes after a logged meal.

Streams fused:

Static record: age, sex, BMI, diabetes duration, HbA1c, fasting glucose, metformin indicator.

Dynamic record: 5-minute CGM-like glucose, sleep hours, resting heart rate, steps in the prior two hours.

Output: a 120-minute glucose trajectory, a peak, minutes at or above 180, and a probability from a logistic model on the twin outputs. A conceptual clinician view exposes the trajectory and a meal-carbohydrate scenario slider.

## Project motivation

Whole-body twins are out of scope for one undergraduate and a short challenge. A minimal glucose–insulin twin is small enough to implement, simulate, and criticise. It also matches the brief’s example of flagging a glucose spike about two hours ahead.

## Objectives

Build a proof of concept that initialises a patient-specific state from a static record, updates it from a recent trace, and forecasts a defined adverse flag.

Keep the physiological model and the machine-learning comparison separate, and report whichever one the held-out split actually supports.

Make the run reproducible from the public repository without credentials.

## Proposed solution

GlycoTwin-IN is a simulation prototype.

1. A synthetic EHR row sets the prior: basal glucose, glucose effectiveness, and insulin sensitivity.
2. The last 60 minutes of CGM update insulin sensitivity, with a penalty toward that prior. Steps apply a bounded scale.
3. The Bergman minimal model rolls the state forward under the declared carbohydrate load.
4. A logistic model, fit on the training patients, turns the forecast peak and time-above-flag into a probability.
5. Gradient boosting on the full feature set is a comparison, not the primary score.

## Innovation and technical contribution

The contribution is the closed loop from record, to state, to update, to 120-minute scenario, to flag. A classifier on HbA1c and carbs can rank risk. It cannot show the clinician the forecast curve or answer a different carbohydrate scenario. The twin can.

On this split the physiology score beat both the EHR-only logistic and the hybrid boosting model. That result is reported rather than overridden.

## Digital twin concept and operational workflow

Physical entity: an adult with type 2 diabetes. In this repository the entity is simulated.

Digital representation: glucose G (mg/dL) and remote insulin action X (1/min).

Data acquisition: files. There is no live sensor.

Initialisation: EHR prior.

Update: bounded fit of insulin sensitivity on the pre-meal window.

Simulation: 120-minute forward run. The post-meal glucose used as the label is not an input to that run.

Decision support: peak, minutes at or above 180, probability, clinician view.

The prototype uses historical synthetic batches plus a user-set meal scenario. It does not use live data.

Full-scale deployment, not built: consented CGM and EHR, a site-specific prior, prospective evaluation, and a human review step before any flag reaches a patient.

## System architecture

The implemented diagram is in [docs/architecture_diagram.pdf](docs/architecture_diagram.pdf).

Flow: synthetic person, static EHR, dynamic CGM and wearable summary, loader, twin state, sensitivity update, Bergman forecast, physiology logistic, clinician view, evaluation log. A separate box marks live integration and clinical validation as not implemented.

## Mathematical model

Bergman minimal model, time in minutes:

dG/dt = −(SG + X) G + SG Gb + Ra(t)

dX/dt = −p2 X + p2 SI (I − Ib)

G glucose (mg/dL). X insulin action (1/min). SG glucose effectiveness (1/min). Gb basal glucose (mg/dL). SI insulin sensitivity (1/min per µU/mL). I insulin (µU/mL), an exogenous meal pulse, not an estimated state. Ra meal appearance (mg/dL/min) from a two-compartment gut: dose, bioavailability, distribution volume, and a time constant.

The data generator adds sleep and heart-rate stress and sensor noise. The twin equations do not include that stress term. The twin is therefore misspecified on purpose.

Assumptions: one meal, known carbohydrate mass, no hypo-counter-regulation, fixed volume of distribution, insulin not observed.

## AI model and justification

Primary score: logistic regression on the twin peak and minutes at or above 180, after standardisation. Chosen because the twin already produces the decision variables, and a linear probability model is inspectable.

Comparison 1: logistic regression on the EHR and meal size only.

Comparison 2: gradient boosting, 120 trees, depth 2, learning rate 0.06, on EHR, wearable, and twin features. It did not improve held-out discrimination. It is not the deployed score.

No deep network. The sample is 160 synthetic patients.

Inputs and outputs are listed in the use-case section. Training is an internal 112/48 patient split, seed 2026. No hyperparameter search beyond the fixed boosting settings. Metrics: AUROC, AUPRC, Brier, precision, recall, specificity, F1 at 0.5, plus peak MAE and RMSE.

## Technical stack

Python for the model, the cohort, and the app.

NumPy, Pandas, and SciPy for the ODE solve and the sensitivity fit.

scikit-learn for the logistic and boosting comparisons.

Matplotlib for the result figures.

Streamlit for the interactive clinician view.

Static HTML for a no-install view of two virtual patients.

ReportLab for the architecture PDF and the presentation PDF.

Git and GitHub for the public submission. SQLite was not needed.

## Dataset sources

No external patient file is shipped.

Name: GlycoTwin-IN synthetic cohort, seed 2026.

Source: generated in this repository by src/glycotwin/synthetic.py.

Access: sample_data/synthetic_ehr.csv and sample_data/synthetic_cgm.csv.

Size: 160 virtual patients, one meal event each, 5-minute glucose from 90 minutes before the meal to 120 minutes after.

Format: CSV.

Use: train the comparison models and score the twin.

Limits: synthetic, one meal, generator in the same model family as the twin plus a stress term. Not a substitute for OhioT1DM, ShanghaiT1DM/T2DM, or MIMIC. Those sets were not used. OhioT1DM needs registration; shipping a private extract would have broken the public-access rule.

Licence: the synthetic tables are released with the code under MIT.

## Data preprocessing

Pre-meal window for the update: minutes −60 to 0. Label window: minutes 5 to 120, peak at or above 180. No imputation was required. Sensor noise is applied in the generator, mean zero, standard deviation 5.5 mg/dL, plus a small per-patient bias.

## System implementation

src/glycotwin/minimal_model.py solves the ODE.

src/glycotwin/synthetic.py builds the cohort.

src/glycotwin/twin.py sets the prior, fits sensitivity, and forecasts.

scripts/run_experiment.py trains the comparisons and writes metrics.

app.py is the Streamlit view.

docs/clinician_dashboard.html is the static view.

tests/test_model.py checks that a meal raises glucose and that higher sensitivity lowers the peak.

## Repository structure

Parth_Pariwandh_Jadavpur_University/

app.py clinician view

LICENSE MIT

requirements.txt

sample_data synthetic EHR, CGM, and the twin feature table

results metrics, bootstrap intervals, test predictions, figures

scripts/run_experiment.py and scripts/build_docs.py

src/glycotwin model, generator, twin

tests/test_model.py

docs architecture PDF, presentation PDF, technical notes, video script, static dashboard

## Installation

Python 3.10 or newer.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Configuration

No API key. No environment file. The split seed is 2026 inside scripts/run_experiment.py.

## Execution

From the repository root:

    PYTHONPATH=src python3 scripts/run_experiment.py
    PYTHONPATH=src python3 -c "import tests.test_model as t; t.test_meal_raises_glucose(); t.test_higher_sensitivity_lowers_peak()"
    streamlit run app.py

The static view opens in a browser from docs/clinician_dashboard.html.

## Prototype functionality

A judge can regenerate the cohort, read results/metrics.json, open two virtual-patient cards, and move a carbohydrate slider in the Streamlit app. The slider reruns the twin. It does not retrain the logistic model.

## Experimental methodology

160 synthetic patients. 48 held out by a shuffle of identifiers, seed 2026. The twin forecast for a patient does not use that patient’s post-meal glucose. Models fit on the other 112 only. Bootstrap intervals resample the same 48 test patients 1,000 times and are percentile intervals, not external validation.

## Evaluation metrics and actual results

Test prevalence 0.729. Peak MAE 17.06 mg/dL. Peak RMSE 25.69 mg/dL.

EHR logistic: AUROC 0.945, bootstrap 0.870 to 0.998, AUPRC 0.980, Brier 0.115, F1 0.892.

Twin physiology: AUROC 0.976, bootstrap 0.926 to 1.000, AUPRC 0.992, Brier 0.068, F1 0.925.

Hybrid gradient boosting: AUROC 0.936, bootstrap 0.853 to 0.994, AUPRC 0.978, Brier 0.089, F1 0.930.

The boosting model’s higher recall at the 0.5 cut did not compensate for worse discrimination and a worse Brier score. Intervals are wide. Prevalence is high, so accuracy is not used as a headline. These figures are simulation results, not clinical accuracy.

## Limitations

Synthetic data in the same model family as the twin, plus one stress term. Small test set. One meal. Carbohydrate mass is given. No medication timing, no menstrual cycle, no illness. No external cohort. No clinician study. The 180 mg/dL flag is operational. Do not quote these AUROC values as expected hospital performance.

## Privacy, safety, and responsible AI

No real patient record, identifier, or credential is in the repository. The clinician view carries a not-for-clinical-use warning. The flag is decision support in a sketch, not an instruction to change insulin or tablets. A deployment would need a clinical protocol, consent, and the DPDP Act constraints that this sandbox avoids by using synthetic data.

## Future development

An external open CGM cohort, a proper insulin state estimator, meal-size uncertainty, and a prospective silent-trial design. Not claimed as done.

## Open-source licence

MIT. Full text in [LICENSE](LICENSE). Copyright 2026 Parth Pariwandh. The licence covers the code and the synthetic tables. It does not make this a medical device, and it does not add contributors who are not named above.

## Architecture diagram

[docs/architecture_diagram.pdf](docs/architecture_diagram.pdf)

## Presentation

[docs/project_presentation.pdf](docs/project_presentation.pdf)

## Other documents

[docs/technical_documentation.md](docs/technical_documentation.md)

[docs/clinician_dashboard.html](docs/clinician_dashboard.html)

[docs/demo_video_script.md](docs/demo_video_script.md)

## Demo video

Status: not uploaded yet.

The Unstop form asks for a 15–20 minute unlisted YouTube video linked from this README. The challenge text also says a minimum 20-minute video, as a PowerPoint recording or an unlisted YouTube link. Record about 20 minutes from docs/demo_video_script.md, upload it unlisted, and replace this paragraph with the URL before submission. Do not tick that form box until the link in this section opens without a sign-in.

## Public access

This repository is public. The PDF, HTML, CSV, and code links above are relative and do not need extra permission. No credential is required.

## References

Anjana RM, Unnikrishnan R, Deepa M, et al. Metabolic non-communicable disease health report of India: the ICMR-INDIAB national cross-sectional study (ICMR-INDIAB-17). Lancet Diabetes and Endocrinology. 2023;11(7):474-489. doi:10.1016/S2213-8587(23)00119-5. Prevalence figures used above are from that paper.

Bergman RN, Ider YZ, Bowden CR, Cobelli C. Quantitative estimation of insulin sensitivity. American Journal of Physiology. 1979;236(6):E667-E677. Source of the minimal-model structure.

American Diabetes Association. Standards of Care in Diabetes. The 180 mg/dL line is used here only as a commonly cited 1–2 hour post-meal target and as an operational flag, not as a validated cut for this prototype.

## Submission links

Public GitHub repository: https://github.com/parthpariwandh/Parth_Pariwandh_Jadavpur_University

Architecture diagram: https://github.com/parthpariwandh/Parth_Pariwandh_Jadavpur_University/blob/main/docs/architecture_diagram.pdf

Presentation: https://github.com/parthpariwandh/Parth_Pariwandh_Jadavpur_University/blob/main/docs/project_presentation.pdf

Form field: paste the repository URL. Tick an item only after this README contains it. The video box stays unticked until the unlisted link is pasted above.
