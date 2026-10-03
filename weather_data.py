"""
Weather Data Generator and Store
Provides realistic 365+ day date-wise weather records for multiple cities,
with seasonal variations, realistic synoptic storms, diurnal cycles, and weather conditions.
"""

import datetime
import math
import random
from typing import Dict, List, Any


CITIES = {
    "New York": {
        "lat": 40.7128,
        "lon": -74.0060,
        "base_temp": 13.0,
        "temp_amp": 14.0,  # Cold winters, hot summers
        "rain_factor": 1.0,
        "wind_base": 14.0,
        "climate": "Humid Subtropical / Continental"
    },
    "London": {
        "lat": 51.5074,
        "lon": -0.1278,
        "base_temp": 11.5,
        "temp_amp": 8.0,   # Moderate oceanic
        "rain_factor": 0.85,
        "wind_base": 16.0,
        "climate": "Temperate Oceanic"
    },
    "Tokyo": {
        "lat": 35.6762,
        "lon": 139.6503,
        "base_temp": 16.0,
        "temp_amp": 12.0,
        "rain_factor": 1.3,
        "wind_base": 11.0,
        "climate": "Humid Subtropical"
    },
    "Mumbai": {
        "lat": 19.0760,
        "lon": 72.8777,
        "base_temp": 27.5,
        "temp_amp": 3.5,   # Tropical monsoon
        "rain_factor": 2.2,
        "wind_base": 12.5,
        "climate": "Tropical Wet & Dry (Monsoon)"
    },
    "San Francisco": {
        "lat": 37.7749,
        "lon": -122.4194,
        "base_temp": 14.5,
        "temp_amp": 4.0,   # Mediterranean coastal
        "rain_factor": 0.7,
        "wind_base": 18.0,
        "climate": "Warm-summer Mediterranean"
    },
    "Sydney": {
        "lat": -33.8688,
        "lon": 151.2093,
        "base_temp": 18.5,
        "temp_amp": 7.0,   # Southern hemisphere
        "rain_factor": 1.1,
        "wind_base": 15.0,
        "climate": "Humid Subtropical"
    }
}

DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def generate_city_data(city_name: str, days: int = 365, end_date: datetime.date = None) -> List[Dict[str, Any]]:
    """Generates daily date-wise weather records up to `end_date`."""
    if end_date is None:
        end_date = datetime.date(2024, 12, 31)
    
    cfg = CITIES.get(city_name, CITIES["New York"])
    start_date = end_date - datetime.timedelta(days=days - 1)
    
    # Deterministic seed per city so results are consistent yet dynamic
    rng = random.Random(hash(city_name) & 0xffffffff)
    
    records = []
    
    # Southern hemisphere phase shift
    phase_shift = math.pi if cfg["lat"] < 0 else 0.0
    
    # Markov weather state: 0 = Clear, 1 = Cloudy, 2 = Rain, 3 = Heavy Rain / Storm
    current_state = 0
    
    for i in range(days):
        current_date = start_date + datetime.timedelta(days=i)
        day_of_year = current_date.timetuple().tm_yday
        
        # Annual seasonal temperature wave (peak around July in North, Jan in South)
        season_angle = (2 * math.pi * (day_of_year - 20) / 365.25) - phase_shift
        seasonal_temp = cfg["base_temp"] + cfg["temp_amp"] * math.sin(season_angle)
        
        # Daily atmospheric noise
        temp_noise = rng.gauss(0, 2.5)
        tavg = round(seasonal_temp + temp_noise, 1)
        
        # Diurnal range: 6 - 12 degrees
        diurnal_spread = rng.uniform(7.0, 13.0)
        tmax = round(tavg + (diurnal_spread / 2) + rng.uniform(-0.5, 1.0), 1)
        tmin = round(tavg - (diurnal_spread / 2) + rng.uniform(-1.0, 0.5), 1)
        if tmax < tmin:
            tmax, tmin = tmin + 2.0, tmax
            tavg = round((tmax + tmin) / 2, 1)
            
        # Markov weather transitions
        r = rng.random()
        if current_state == 0:  # Clear
            if r < 0.65:
                current_state = 0
            elif r < 0.90:
                current_state = 1
            else:
                current_state = 2
        elif current_state == 1:  # Cloudy
            if r < 0.40:
                current_state = 0
            elif r < 0.75:
                current_state = 1
            else:
                current_state = 2
        else:  # Rainy
            if r < 0.50:
                current_state = 2
            elif r < 0.75:
                current_state = 1
            else:
                current_state = 0
                
        # Rain calculation based on city & seasonal monsoon/winter rain
        rain = 0.0
        if city_name == "Mumbai":
            # Heavy monsoon between June (day 152) and September (day 273)
            is_monsoon = 152 <= day_of_year <= 273
            if is_monsoon:
                rain_prob = 0.85
                rain_amt = rng.expovariate(1 / 18.0) * cfg["rain_factor"]
            else:
                rain_prob = 0.08
                rain_amt = rng.expovariate(1 / 4.0)
            if rng.random() < rain_prob:
                rain = round(rain_amt, 1)
        else:
            if current_state == 2:
                # Moderate to heavy rain
                rain = round(rng.expovariate(1 / 7.5) * cfg["rain_factor"], 1)
                if rain < 0.2:
                    rain = 0.8
            elif current_state == 1 and rng.random() < 0.25:
                # Drizzle
                rain = round(rng.uniform(0.1, 2.5) * cfg["rain_factor"], 1)
            else:
                rain = 0.0

        # Humidity calculation: inversely linked to temperature, positively to rain
        base_hum = 65.0 - (tavg - 15.0) * 0.8 + (15.0 if rain > 0 else -5.0)
        hum = max(20, min(98, int(base_hum + rng.gauss(0, 6))))
        
        # Pressure: typically lower during rain/storms, higher during clear cool high-pressure
        storm_depression = -12.0 if rain > 15 else (-5.0 if rain > 0 else 2.0)
        pres = round(1013.25 + storm_depression + rng.gauss(0, 4.0), 1)
        
        # Wind speed: higher in winter/spring, or during storms
        wind_seasonal = cfg["wind_base"] + 3.0 * math.cos(season_angle)
        wind_gust = rng.uniform(0, 8.0) + (10.0 if rain > 10 else 0.0)
        wind = round(max(3.0, wind_seasonal + wind_gust + rng.gauss(0, 2.0)), 1)
        
        # Wind direction: prevailing winds with local randomness
        if city_name in ["New York", "London"]:
            weights = [0.08, 0.07, 0.06, 0.09, 0.12, 0.32, 0.18, 0.08]
        elif city_name == "San Francisco":
            weights = [0.05, 0.05, 0.05, 0.05, 0.10, 0.20, 0.40, 0.10]
        else:
            weights = [0.10, 0.12, 0.15, 0.12, 0.11, 0.18, 0.12, 0.10]
        wind_dir = rng.choices(DIRECTIONS, weights=weights)[0]
        
        # Condition description & icon code
        if rain > 20:
            condition = "Thunderstorm / Heavy Rain"
            icon = "rain-thunder"
        elif rain > 5:
            condition = "Moderate Rain"
            icon = "rain"
        elif rain > 0:
            condition = "Light Rain / Showers"
            icon = "rain-light"
        elif hum > 85 and tavg < 15:
            condition = "Misty / Foggy"
            icon = "fog"
        elif current_state == 1:
            condition = "Partly Cloudy"
            icon = "cloudy-sun"
        elif current_state == 0 and hum > 60:
            condition = "Mostly Clear"
            icon = "sun-cloud"
        else:
            condition = "Clear / Sunny"
            icon = "sun"

        # UV Index estimation
        solar_elevation = max(0.0, math.sin(season_angle + phase_shift + math.pi/2))
        uv_cloud_factor = 0.3 if rain > 0 else (0.6 if current_state == 1 else 1.0)
        uv_index = max(1, min(12, int(solar_elevation * 10 * uv_cloud_factor + rng.uniform(-0.5, 0.5))))

        records.append({
            "date": current_date.isoformat(),
            "day": current_date.strftime("%a"),
            "month": current_date.strftime("%b"),
            "year": current_date.year,
            "tmax": tmax,
            "tmin": tmin,
            "tavg": tavg,
            "rain": rain,
            "wind": wind,
            "wind_dir": wind_dir,
            "hum": hum,
            "pres": pres,
            "condition": condition,
            "icon": icon,
            "uv_index": uv_index
        })
        
    return records


# Cache pre-generated records for performance
DATA_STORE: Dict[str, List[Dict[str, Any]]] = {}

def get_city_weather_dataset(city: str = "New York") -> List[Dict[str, Any]]:
    if city not in DATA_STORE:
        DATA_STORE[city] = generate_city_data(city, days=365)
    return DATA_STORE[city]
