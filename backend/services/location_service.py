"""
Location Service for AI Health Assistant.
Computes distances between coordinates using the Haversine formula.
Supports optional Google Maps geocoding / distance matrix if GOOGLE_MAPS_API_KEY is configured.
"""

import math
import requests
from backend.config import config

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth (in kilometers).
    Uses the Haversine formula.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert coordinates from degrees to radians
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    # Haversine formula
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)

def geocode_address(address):
    """
    Optional Google Maps Geocoding API if key is present.
    Returns (lat, lng) tuple or None.
    """
    if not config.GOOGLE_MAPS_API_KEY:
        return None
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": config.GOOGLE_MAPS_API_KEY}
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        if data.get("status") == "OK" and len(data.get("results", [])) > 0:
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None
