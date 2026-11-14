"""Tests for the AI assistant's trend answer formatting.

Regression: the trend answer printed the raw float p-value
(0.5162352652391138) — 16 digits in the middle of a plain-language answer.
It must be rounded to 2 decimals, and a missing p-value must read
"not available", never "None".
"""

from src.ai_assistant import answer_question


def _trend_ctx(p_value=0.5162352652391138):
    return {
        "city": "Lahore",
        "variable_label": "Mean Air Temperature",
        "unit": "°C",
        "trend": {
            "status": "ok",
            "direction": "decreasing",
            "sen_slope_per_decade": -1.337,
            "p_value": p_value,
            "significant_005": False,
            "first_month": "2015-01",
            "last_month": "2025-12",
            "n": 132,
        },
    }


def test_trend_answer_rounds_p_value_to_two_decimals():
    ans = answer_question("what is the trend", _trend_ctx())
    assert "0.52" in ans
    assert "0.5162352652391138" not in ans


def test_trend_answer_missing_p_value_reads_not_available():
    ans = answer_question("is it warming", _trend_ctx(p_value=None))
    assert "not available" in ans
    assert "None" not in ans


def test_trend_answer_keeps_honest_significance_wording():
    ans = answer_question("trend", _trend_ctx())
    assert "not significant" in ans
    assert "-1.34" in ans or "-1.337" in ans
