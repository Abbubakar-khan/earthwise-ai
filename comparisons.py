import pandas as pd
from src.cleaning import monthly_aggregate
from src.statistics import analyze_trend

def compare_cities(city_frames: dict[str, pd.DataFrame], variable: str) -> pd.DataFrame:
    rows = []
    for city, frame in city_frames.items():
        monthly = monthly_aggregate(frame, variable)
        result = analyze_trend(monthly, variable)
        rows.append({"city": city, "variable": variable, **result})
    return pd.DataFrame(rows)
