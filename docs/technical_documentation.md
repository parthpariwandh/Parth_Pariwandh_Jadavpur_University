# Technical notes

## State and observations

The twin state is plasma glucose G (mg/dL) and remote insulin action X (1/min). Observations are noisy CGM-like glucose. Insulin is not observed. It is an exogenous pulse tied to the logged meal, so this is not a hidden-state insulin estimator.

## Prior and update

The EHR prior sets basal glucose to the fasting value and sets insulin sensitivity from HbA1c, BMI, and a metformin indicator. The update minimises pre-meal glucose error over log SI, with a penalty toward the prior, then scales SI by a bounded step-count term. The forecast uses the logged carbohydrate mass. It does not see the post-meal glucose it is scored against.

## Why the hybrid model is not the primary score

On the seed-2026 split the physiology logistic, fit only on the twin peak and minutes at or above 180, had a higher held-out AUROC and a lower Brier score than gradient boosting on the full feature set. The boosting model is retained as a baseline, not as the deployed score.

## Reproducibility

From the repository root, with dependencies installed:

    PYTHONPATH=src python3 scripts/run_experiment.py

The command rewrites sample_data and results/metrics.json. Docs that quote metrics refer to the seed-2026 run archived in results/.

## Privacy

No real patient record is stored. Identifiers are SYN-000 style keys. The MIT licence covers the code and the synthetic tables in this repository.
