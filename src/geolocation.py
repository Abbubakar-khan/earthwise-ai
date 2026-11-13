"""Auto location detection for EarthWise AI.

Pure, testable logic for turning browser coordinates into a city in the
REGIONS catalogue, plus the free no-key reverse-geocode call.

Why a custom component (components/geolocation) instead of a plain
components.html snippet: Streamlit 1.63 renders components.html inside a
sandboxed iframe whose sandbox list is
  allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox
  allow-same-origin allow-scripts allow-downloads
— there is NO allow-top-navigation — so JavaScript in that iframe CANNOT
navigate the parent page to pass coordinates back via ?geo_lat= query
params. Verified 2026-11-14 in headless Chromium (Muse Browser 157) with
Streamlit's exact sandbox/allow attributes: assigning
window.parent.location.href throws "Failed to set the 'href' property on
'Location': The current window does not have permission to navigate the
target frame". The iframe DOES allow geolocation (its allow list includes
it), so detection itself works — only the return channel needed changing.
The vendored custom component uses Streamlit's own postMessage bridge
(Streamlit.setComponentValue), which the sandbox does not block.

No new API keys, no new paid services, no new pip dependencies: the
reverse-geocode uses BigDataCloud's free client endpoint (no key), and
live weather/AQI keep using the exact detected coordinates via the
Open-Meteo / CAMS APIs the app already calls.
"""
from __future__ import annotations

import difflib
import math
import re

import requests

from src.regions import REGIONS

REVERSE_GEOCODE_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"
REVERSE_GEOCODE_TIMEOUT_S = 8.0
# A reverse-geocoded locality is only trusted when its catalogue city is
# this close to the detected point; further away means the locality does
# not describe where the visitor actually is, so fall back to nearest.
LOCALITY_MAX_DISTANCE_KM = 150.0

GEO_QUERY_LAT = "geo_lat"
GEO_QUERY_LON = "geo_lon"
GEO_QUERY_STATUS = "geo_status"
GEO_STATUSES = ("ok", "denied", "timeout", "unavailable")


def _validate_lat_lon(latitude, longitude):
    if not (-90.0 <= float(latitude) <= 90.0):
        raise ValueError(f"latitude out of range: {latitude!r}")
    if not (-180.0 <= float(longitude) <= 180.0):
        raise ValueError(f"longitude out of range: {longitude!r}")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two points."""
    _validate_lat_lon(lat1, lon1)
    _validate_lat_lon(lat2, lon2)
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))


def _normalize_name(name) -> str:
    """Lowercase and keep words only ("Hunza (Karimabad)" -> "hunza karimabad").

    Parentheticals are kept as words: they are alternative names a
    reverse-geocoder may return ("Karimabad"), not noise.
    """
    text = (name or "").strip().casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def match_locality_to_city(locality, regions=None):
    """Match a reverse-geocoded locality name to a REGIONS city, or None.

    Exact normalized match first, then a unique whole-word match
    ("Karimabad" -> "Hunza (Karimabad)"), then a close spelling match
    (difflib, for minor geocoder spelling differences). Ambiguous or
    foreign localities ("London", "Dera") return None so the caller falls
    back to the haversine-nearest catalogue city.
    """
    if not locality or not str(locality).strip():
        return None
    regions = REGIONS if regions is None else regions
    want = _normalize_name(locality)
    if not want:
        return None
    by_norm = {_normalize_name(name): name for name in regions}
    if want in by_norm:
        return by_norm[want]
    want_words = set(want.split())
    word_matches = [name for norm, name in by_norm.items()
                    if want_words & set(norm.split()) and
                    (set(norm.split()) <= want_words or want_words <= set(norm.split()))]
    if len(word_matches) == 1:
        return word_matches[0]
    close = difflib.get_close_matches(want, list(by_norm), n=1, cutoff=0.8)
    if close:
        return by_norm[close[0]]
    return None


def nearest_region_city(latitude: float, longitude: float, regions=None):
    """Return (city, distance_km) of the closest REGIONS city."""
    regions = REGIONS if regions is None else regions
    best, best_km = None, None
    for name, info in regions.items():
        dist = haversine_km(latitude, longitude,
                            info["latitude"], info["longitude"])
        if best_km is None or dist < best_km:
            best, best_km = name, dist
    return best, best_km


def parse_reverse_geocode(payload):
    """Extract the locality name from a BigDataCloud client response."""
    if not isinstance(payload, dict):
        return None
    for key in ("locality", "city"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def reverse_geocode(latitude: float, longitude: float,
                    timeout: float = REVERSE_GEOCODE_TIMEOUT_S):
    """Reverse-geocode with BigDataCloud's free client endpoint (no key).

    Returns the locality name, or None on any failure. Never raises:
    callers fall back to haversine-nearest.
    """
    try:
        resp = requests.get(
            REVERSE_GEOCODE_URL,
            params={"latitude": latitude, "longitude": longitude,
                    "localityLanguage": "en"},
            timeout=timeout)
        resp.raise_for_status()
        return parse_reverse_geocode(resp.json())
    except Exception:
        return None


def resolve_detected_location(latitude, longitude, locality=None, regions=None):
    """Resolve detected coordinates to a catalogue city.

    Returns {"latitude", "longitude", "city", "locality", "distance_km",
    "method"} where method is "reverse-geocode" when the locality matched
    a nearby catalogue city, else "nearest" (reverse-geocode failed, the
    locality did not match, or the visitor is far outside Pakistan).
    Raises ValueError on out-of-range coordinates.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        raise ValueError("detected coordinates must be numbers")
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise ValueError("detected coordinates out of range")
    regions = REGIONS if regions is None else regions
    clean_locality = (locality.strip() if isinstance(locality, str)
                      and locality.strip() else None)
    matched = (match_locality_to_city(clean_locality, regions)
               if clean_locality else None)
    if matched is not None:
        dist = haversine_km(lat, lon, regions[matched]["latitude"],
                            regions[matched]["longitude"])
        if dist <= LOCALITY_MAX_DISTANCE_KM:
            return {"latitude": lat, "longitude": lon, "city": matched,
                    "locality": clean_locality, "distance_km": dist,
                    "method": "reverse-geocode"}
    nearest, dist = nearest_region_city(lat, lon, regions)
    return {"latitude": lat, "longitude": lon, "city": nearest,
            "locality": clean_locality, "distance_km": dist,
            "method": "nearest"}


def parse_geo_query_params(params):
    """Validate ?geo_lat=&geo_lon=&geo_status= from st.query_params.

    Returns {"status", "latitude", "longitude"} or None when no detection
    handoff is present. A non-ok status (denied/timeout/unavailable) is a
    valid handoff with no coordinates.
    """
    if params is None:
        return None
    try:
        status = params.get(GEO_QUERY_STATUS)
    except AttributeError:
        return None
    if status is None:
        return None
    if isinstance(status, (list, tuple)):
        status = status[0] if status else None
    if status is None:
        return None
    status = str(status).strip().lower()
    if status not in GEO_STATUSES:
        return None
    if status != "ok":
        return {"status": status, "latitude": None, "longitude": None}
    try:
        lat = float(params[GEO_QUERY_LAT])
        lon = float(params[GEO_QUERY_LON])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    return {"status": "ok", "latitude": lat, "longitude": lon}
