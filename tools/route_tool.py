import requests
from langchain_core.tools import tool

HEADERS = {"User-Agent": "AITripPlanner/1.0"}


def _coordinates(place: str):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": f"{place}, India", "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


@tool
def get_route_info(origin: str, destination: str) -> str:
    """Get approximate road distance and driving time between two places in India."""
    try:
        start = _coordinates(origin)
        end = _coordinates(destination)
        if not start:
            return f"Could not locate origin: {origin}."
        if not end:
            return f"Could not locate destination: {destination}."

        start_lat, start_lon = start
        end_lat, end_lon = end
        response = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}",
            params={"overview": "false"},
            timeout=12,
        )
        response.raise_for_status()
        routes = response.json().get("routes") or []
        if not routes:
            return "No driving route was found."

        route = routes[0]
        distance_km = round(route["distance"] / 1000, 1)
        duration_hours = round(route["duration"] / 3600, 1)
        return f"{origin} to {destination}: about {distance_km} km by road and roughly {duration_hours} hours of driving."
    except Exception as exc:
        return f"Route information unavailable: {exc}"
