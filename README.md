# Parth_Pariwandh_Jadavpur_University

![Challenge](https://img.shields.io/badge/Digital%20Twin%20Challenge-2026-navy)
![Model](https://img.shields.io/badge/Bergman-minimal%20model-blue)
![University](https://img.shields.io/badge/Jadavpur%20University-ME-lightgrey)

GlycoTwin-IN: a hybrid Bergman digital twin for two hour postprandial hyperglycaemia risk. The repository name is unchanged.

Competition: Digital Twin Challenge 2026, Happiest Health. Individual submission by Parth Pariwandh, Jadavpur University. This is not an official university product.

## At a glance

- Forecasts whether a virtual adult with type 2 diabetes reaches 180 mg/dL within 120 minutes of a logged meal
- Synthetic cohort only. Not a clinical device
- Physiology score beat the comparison models on the held out split
- Public repository: https://github.com/parthpariwandh/Parth_Pariwandh_Jadavpur_University

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python3 scripts/run_experiment.py
streamlit run app.py
```

## Documents

- Architecture: docs/architecture_diagram.pdf
- Presentation: docs/project_presentation.pdf
- Static clinician view: docs/clinician_dashboard.html

## Licence

MIT. Copyright 2026 Parth Pariwandh. Not a medical device.
