import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from glycotwin.minimal_model import simulate_glucose
import numpy as np


def test_meal_raises_glucose():
    t = np.arange(0, 121, 5)
    fasting = simulate_glucose(t, 10_000, 0, 120, 12, 0.015, 2e-4, 0.025, 45, 12, 40, g0=120)
    fed = simulate_glucose(t, 0, 80, 120, 12, 0.015, 2e-4, 0.025, 45, 12, 40, g0=120)
    assert fed.max() > fasting.max() + 20


def test_higher_sensitivity_lowers_peak():
    t = np.arange(0, 121, 5)
    resistant = simulate_glucose(t, 0, 80, 130, 12, 0.012, 8e-5, 0.025, 45, 10, 40, g0=130)
    sensitive = simulate_glucose(t, 0, 80, 130, 12, 0.012, 6e-4, 0.025, 45, 10, 40, g0=130)
    assert sensitive.max() < resistant.max()
