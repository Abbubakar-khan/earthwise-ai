"""Risk note must print a rounded p-value, never the raw 16-digit float.

Regression (live 2026-11-14): Risk & Outlook showed
"Kendall p=0.5162352652391138" from compute_risk's note.
"""

import pandas as pd

from src.risk import compute_risk

_MONTHS = pd.date_range("2015-01-01", periods=132, freq="MS")
_MONTHLY = pd.DataFrame({"date": _MONTHS, "value": range(132)})


def _trend(p_value=0.5162352652391138):
    return {
        "status": "ok",
        "direction": "decreasing",
        "sen_slope_per_decade": -1.337,
        "p_value": p_value,
        "n": 132,
    }


def test_risk_note_rounds_p_value_to_two_decimals():
    risk = compute_risk(_MONTHLY, "T2M", _trend())
    note = " ".join(risk["notes"])
    assert "p=0.52" in note
    assert "0.5162352652391138" not in note


def test_risk_note_missing_p_value_reads_unavailable():
    risk = compute_risk(_MONTHLY, "T2M", _trend(p_value=None))
    note = " ".join(risk["notes"])
    assert "p=unavailable" in note
    assert "None" not in note
