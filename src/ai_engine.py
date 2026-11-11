def explain_result(city: str, variable_label: str, unit: str, result: dict) -> str:
    """Evidence-bound deterministic explanation; no generated causes or forecasts."""
    if result.get("status") != "ok":
        return f"{city} ke {variable_label} ke liye abhi reliable trend statement nahi ban sakta: {result.get('message', 'insufficient data')}"
    slope = result["sen_slope_per_decade"]
    p = result["p_value"]
    sig = "statistically significant at the 0.05 level" if result["significant_005"] else "not statistically significant at the 0.05 level"
    return (
        f"{city} mein {variable_label} ka estimated direction **{result['direction']}** hai. "
        f"Sen's slope taqreeban **{slope:.4g} {unit}/decade** hai. "
        f"Kendall tau p-value **{p:.4g}** hai, is liye trend {sig}. "
        f"Analysis period {result['first_month']} se {result['last_month']} tak hai, "
        f"aur {result['n']} valid monthly observations use hue. "
        "Yeh historical trend hai, future forecast nahi. Yeh analysis cause establish nahi karta. "
        "Monthly seasonality/autocorrelation correction is MVP mein apply nahi hui."
    )
