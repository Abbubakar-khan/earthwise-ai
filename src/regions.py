"""Initial Pakistan city coordinates and NASA POWER daily parameters."""
REGIONS = {
    "Islamabad": {"latitude": 33.6844, "longitude": 73.0479},
    "Lahore": {"latitude": 31.5204, "longitude": 74.3587},
    "Karachi": {"latitude": 24.8607, "longitude": 67.0011},
    "Peshawar": {"latitude": 34.0151, "longitude": 71.5249},
    "Quetta": {"latitude": 30.1798, "longitude": 66.9750},
    "Faisalabad": {"latitude": 31.4504, "longitude": 73.1350},
    "Multan": {"latitude": 30.1575, "longitude": 71.5249},
    "Skardu": {"latitude": 35.2971, "longitude": 75.6333},
    "Gilgit": {"latitude": 35.9208, "longitude": 74.3089},
}
VARIABLES = {
    "T2M": {"label": "Air temperature at 2 m", "unit": "°C", "aggregation": "mean"},
    "T2M_MAX": {"label": "Daily maximum air temperature", "unit": "°C", "aggregation": "mean"},
    "T2M_MIN": {"label": "Daily minimum air temperature", "unit": "°C", "aggregation": "mean"},
    "RH2M": {"label": "Relative humidity at 2 m", "unit": "%", "aggregation": "mean"},
    "PRECTOTCORR": {"label": "Corrected precipitation", "unit": "mm/day", "aggregation": "sum"},
    "WS10M": {"label": "Wind speed at 10 m", "unit": "m/s", "aggregation": "mean"},
    "ALLSKY_SFC_SW_DWN": {"label": "All-sky surface shortwave irradiance", "unit": "kWh/m²/day", "aggregation": "mean"},
}
