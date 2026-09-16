import requests
from langchain_core.tools import tool


def _geocode(place: str):
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": place, "count": 1, "language": "en", "format": "json", "countryCode": "IN"},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        return None
    return results[0]["latitude"], results[0]["longitude"]


@tool
def get_weather(location: str) -> str:
    """Get current weather for an Indian destination."""
    try:
        coords = _geocode(location)
        if not coords:
            return f"Weather unavailable because {location} could not be geocoded."

        lat, lon = coords
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=10,
        )
        response.raise_for_status()
        current = response.json().get("current") or {}
        return (
            f"Current temperature {current.get('temperature_2m', 'N/A')}°C, "
            f"feels like {current.get('apparent_temperature', 'N/A')}°C, "
            f"precipitation {current.get('precipitation', 'N/A')} mm, "
            f"wind {current.get('wind_speed_10m', 'N/A')} km/h."
        )
    except Exception as exc:
        return f"Weather information unavailable: {exc}"
