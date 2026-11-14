"""Whole-Pakistan map (2026-11-14): 172 places, all with real coordinates
inside Pakistan, and tap-to-load selection logic.

The map figure colours places by live temperature; places whose live
fetch failed are still plotted (grey) from REGIONS, never dropped.
"""
from src.pakistan_map import build_pakistan_map_figure, city_from_selection
from src.regions import REGIONS


def test_catalogue_covers_whole_pakistan():
    assert len(REGIONS) >= 160, f"only {len(REGIONS)} places"
    provinces = {v["province"] for v in REGIONS.values()}
    assert provinces == {
        "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan",
        "Gilgit-Baltistan", "Azad Jammu & Kashmir",
        "Islamabad Capital Territory"}


def test_all_coordinates_are_inside_pakistan():
    for name, info in REGIONS.items():
        assert 23.0 <= info["latitude"] <= 37.5, name
        assert 60.0 <= info["longitude"] <= 78.0, name
        assert info["province"]


def test_new_towns_present():
    for town in ("Murree", "Taxila", "Sadiqabad", "Sehwan", "Parachinar",
                 "Ziarat", "Khaplu", "Pallandri", "Burewala", "Daska"):
        assert town in REGIONS, f"missing town: {town}"


def test_figure_plots_every_place():
    records = [
        {"city": "Lahore", "latitude": 31.5204, "longitude": 74.3587,
         "temperature": 26.6, "condition": "Clear sky", "province": "Punjab"},
        {"city": "Karachi", "latitude": 24.8607, "longitude": 67.0011,
         "temperature": 29.0, "condition": "Haze", "province": "Sindh"},
    ]
    fig = build_pakistan_map_figure(records, "Lahore")
    # One scattergeo trace holds all places (plus the selected-place star).
    points = fig.data[0]
    assert len(points.lat) == len(REGIONS)
    assert "Lahore" in [c[0] for c in points.customdata]
    assert len(fig.data) == 2  # places + selected-place star


def test_figure_works_with_no_live_records():
    fig = build_pakistan_map_figure([], "Quetta")
    assert len(fig.data[0].lat) == len(REGIONS)


def test_city_from_selection():
    sel = {"points": [{"customdata": ["Multan"]}]}
    assert city_from_selection(sel, current_city="Lahore") == "Multan"


def test_city_from_selection_ignores_current_city_star():
    # The star marker for the already-selected place is not a new tap.
    sel = {"points": [{"customdata": ["Lahore"]}]}
    assert city_from_selection(sel, current_city="Lahore") is None


def test_city_from_selection_defensive():
    assert city_from_selection(None) is None
    assert city_from_selection({}) is None
    assert city_from_selection({"points": []}) is None
    assert city_from_selection({"points": [{"customdata": ["Atlantis"]}]}) is None
    assert city_from_selection({"points": [{"customdata": []}]}) is None
    assert city_from_selection({"points": ["not-a-dict"]}) is None
