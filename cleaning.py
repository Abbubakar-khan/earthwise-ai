import pandas as pd

def monthly_aggregate(df: pd.DataFrame, variable: str) -> pd.DataFrame:
    if "date" not in df or variable not in df:
        raise ValueError(f"Data must contain date and {variable}")
    work = df[["date", variable]].copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work[variable] = pd.to_numeric(work[variable], errors="coerce")
    work = work.dropna(subset=["date"])
    work.loc[work[variable] <= -900, variable] = float("nan")
    work = work.dropna(subset=[variable]).set_index("date").sort_index()
    if variable == "PRECTOTCORR":
        monthly = work[variable].resample("MS").sum(min_count=1)
    else:
        monthly = work[variable].resample("MS").mean()
    out = monthly.rename(variable).reset_index()
    out["year"] = out["date"].dt.year
    out["month"] = out["date"].dt.month
    return out

def coverage_summary(df: pd.DataFrame, variable: str) -> dict:
    values = pd.to_numeric(df[variable], errors="coerce")
    valid = values.notna() & (values > -900)
    dates = pd.to_datetime(df["date"], errors="coerce")
    return {
        "rows": int(len(df)),
        "valid_rows": int(valid.sum()),
        "coverage_pct": round(float(valid.mean() * 100), 2) if len(df) else 0.0,
        "first_date": str(dates.min().date()) if dates.notna().any() else None,
        "last_date": str(dates.max().date()) if dates.notna().any() else None,
    }
