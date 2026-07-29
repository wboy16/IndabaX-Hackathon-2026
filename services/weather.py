import datetime
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

# Default coordinates for major regional capitals in Namibia
NAMIBIA_REGIONAL_COORDINATES: Dict[str, Dict[str, float]] = {
    "khomas": {"lat": -22.56, "lon": 17.08, "name": "Windhoek (Khomas)"},
    "erongo": {"lat": -21.94, "lon": 15.85, "name": "Karibib/Swakopmund (Erongo)"},
    "hardap": {"lat": -24.60, "lon": 17.96, "name": "Mariental (Hardap)"},
    "karas": {"lat": -26.58, "lon": 18.13, "name": "Keetmanshoop (Karas)"},
    "kunene": {"lat": -20.37, "lon": 14.96, "name": "Khorixas/Opuwo (Kunene)"},
    "ohangwena": {"lat": -17.47, "lon": 16.33, "name": "Eenhana (Ohangwena)"},
    "okavango east": {"lat": -17.92, "lon": 19.77, "name": "Rundu (Okavango East)"},
    "okavango west": {"lat": -17.62, "lon": 18.60, "name": "Nkurenkuru (Okavango West)"},
    "omaheke": {"lat": -22.45, "lon": 18.97, "name": "Gobabis (Omaheke)"},
    "omusati": {"lat": -17.50, "lon": 14.98, "name": "Outapi (Omusati)"},
    "oshana": {"lat": -17.78, "lon": 15.70, "name": "Oshakati (Oshana)"},
    "oshikoto": {"lat": -19.24, "lon": 17.71, "name": "Tsumeb/Omuthiya (Oshikoto)"},
    "otjozondjupa": {"lat": -20.46, "lon": 16.65, "name": "Otjiwarongo (Otjozondjupa)"},
    "zambezi": {"lat": -17.50, "lon": 24.27, "name": "Katima Mulilo (Zambezi)"},
}

class WeatherService:
    """Service to fetch live weather & historical rainfall from Open-Meteo & NASA POWER."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def resolve_location_coordinates(
        self,
        region: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """Resolves lat/lon from input or defaults to region center."""
        if lat is not None and lon is not None:
            return {"lat": lat, "lon": lon, "location_name": f"Coordinates ({lat}, {lon})"}

        if region and region.lower() in NAMIBIA_REGIONAL_COORDINATES:
            coord = NAMIBIA_REGIONAL_COORDINATES[region.lower()]
            return {"lat": coord["lat"], "lon": coord["lon"], "location_name": coord["name"]}

        # Default fallback to Windhoek (Khomas)
        default_coord = NAMIBIA_REGIONAL_COORDINATES["khomas"]
        return {"lat": default_coord["lat"], "lon": default_coord["lon"], "location_name": "Windhoek (Khomas Default)"}

    def fetch_open_meteo_weather(
        self,
        lat: float,
        lon: float,
        location_name: str = "Specified Location"
    ) -> Dict[str, Any]:
        """Calls Open-Meteo API for current weather and past 14-day rainfall."""
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=14)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "timezone": "Africa/Windhoek"
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            daily = data.get("daily", {})

            daily_precip = daily.get("precipitation_sum", [])
            total_14day_rainfall = sum(daily_precip) if daily_precip else 0.0

            # Rainfall condition rating
            if total_14day_rainfall > 50:
                rainfall_status = "High Recent Rainfall (Good pasture recharge)"
            elif total_14day_rainfall > 15:
                rainfall_status = "Moderate Recent Rainfall"
            elif total_14day_rainfall > 5:
                rainfall_status = "Low Recent Rainfall (Limited moisture)"
            else:
                rainfall_status = "Dry / Drought Risk (Negligible recent rainfall)"

            return {
                "status": "success",
                "source": "Open-Meteo",
                "location": location_name,
                "latitude": lat,
                "longitude": lon,
                "current_temperature_c": current.get("temperature_2m"),
                "current_relative_humidity_pct": current.get("relative_humidity_2m"),
                "current_wind_speed_kmh": current.get("wind_speed_10m"),
                "past_14_days_total_rainfall_mm": round(total_14day_rainfall, 2),
                "daily_rainfall_last_14_days": daily_precip,
                "rainfall_condition_status": rainfall_status,
                "fetched_at": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Open-Meteo fetch failed: {str(e)}")
            return {
                "status": "error",
                "source": "Open-Meteo",
                "location": location_name,
                "message": f"Could not retrieve live weather from Open-Meteo: {str(e)}",
                "fallback_estimate": {
                    "past_14_days_total_rainfall_mm": 12.0,
                    "rainfall_condition_status": "Estimated Moderate Conditions (API Offline)"
                }
            }

    def fetch_nasa_power_weather(
        self,
        lat: float,
        lon: float,
        location_name: str = "Specified Location"
    ) -> Dict[str, Any]:
        """Calls NASA POWER Agroclimatology API for daily precipitation & solar radiation."""
        end_date = datetime.date.today() - datetime.timedelta(days=2) # NASA POWER has ~2 day delay
        start_date = end_date - datetime.timedelta(days=14)

        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        params = {
            "parameters": "PRECTOTCORR,T2M,ALLSKY_SFC_SW_DWN",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
            "format": "JSON"
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            properties = data.get("properties", {}).get("parameter", {})
            precip_dict = properties.get("PRECTOTCORR", {})

            total_precip = sum(v for v in precip_dict.values() if v >= 0)

            return {
                "status": "success",
                "source": "NASA POWER Agroclimatology",
                "location": location_name,
                "latitude": lat,
                "longitude": lon,
                "past_14_days_total_rainfall_mm": round(total_precip, 2),
                "fetched_at": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"NASA POWER fetch failed: {str(e)}")
            return {
                "status": "error",
                "source": "NASA POWER",
                "message": f"NASA POWER API request failed: {str(e)}"
            }

    def get_weather_for_region_or_coords(
        self,
        region: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """Main helper method to resolve location and fetch live weather."""
        resolved = self.resolve_location_coordinates(region=region, lat=lat, lon=lon)
        return self.fetch_open_meteo_weather(
            lat=resolved["lat"],
            lon=resolved["lon"],
            location_name=resolved["location_name"]
        )
