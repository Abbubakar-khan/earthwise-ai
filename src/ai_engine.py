def explain_result(city: str, variable_label: str, unit: str, result: dict) -> str:
    """Evidence-bound English explanation; no generated causes or forecasts."""
    if result.get("status") != "ok":
        message = result.get("message", "insufficient data")
        return (
            f"A reliable trend statement cannot currently be produced for "
            f"{variable_label} in {city}: {message}"
        )

    slope = result["sen_slope_per_decade"]
    p_value = result.get("p_value")
    if p_value is None:
        significance = "not statistically testable for this dataset"
        p_value_text = "unavailable"
    else:
        significance = (
            "statistically significant at the 0.05 level"
            if result.get("significant_005") is True
            else "not statistically significant at the 0.05 level"
        )
        p_value_text = f"{p_value:.4g}"
    return (
        f"For **{city}**, the estimated long-term direction of "
        f"**{variable_label}** is **{result['direction']}**. "
        f"Sen's slope is approximately **{slope:.4g} {unit} per decade**. "
        f"The Kendall tau p-value is **{p_value_text}**, indicating that this "
        f"trend is {significance}. "
        f"The analysis covers **{result['first_month']} to {result['last_month']}** "
        f"and uses **{result['n']} valid monthly observations**.\n\n"
        "**How to interpret this:** This is a historical statistical trend, "
        "not a future forecast. The analysis does not establish the cause of "
        "the observed pattern. Monthly seasonality and serial autocorrelation "
        "are not corrected for in this MVP, so interpret the p-value cautiously."
    )
