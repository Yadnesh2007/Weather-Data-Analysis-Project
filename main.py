"""
FastAPI Backend for Weather Data Analysis Application
Provides date-wise weather analytics, hourly drill-downs, CSV upload, and static dashboard serving.
"""

import os
import io
import datetime
from typing import Optional
from fastapi import FastAPI, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

from weather_data import get_city_weather_dataset, CITIES, DATA_STORE
from analytics import filter_and_process_weather, compute_date_deep_dive


app = FastAPI(
    title="Weather Analysis API",
    description="Date-wise Weather Analytics & Meteorological Intelligence Backend",
    version="1.0.0"
)

# Enable CORS for external frontend or cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Custom uploaded datasets storage
CUSTOM_DATASETS = {}


@app.get("/api/weather/cities")
def get_cities():
    """Returns list of supported geographic locations with climate details."""
    cities_list = [
        {
            "name": name,
            "lat": cfg["lat"],
            "lon": cfg["lon"],
            "climate": cfg["climate"]
        }
        for name, cfg in CITIES.items()
    ]
    # Add custom uploaded datasets if any
    for custom_id in CUSTOM_DATASETS:
        cities_list.append({
            "name": f"Uploaded ({custom_id})",
            "lat": 0.0,
            "lon": 0.0,
            "climate": "Custom Uploaded Dataset"
        })
    return {"cities": cities_list}


@app.get("/api/weather/analysis")
def get_weather_analysis(
    city: str = Query("New York", description="City name or uploaded dataset ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: str = Query("daily", description="'daily', 'weekly', or 'monthly'")
):
    """
    Returns date-wise meteorological analytics for the chosen date range and location.
    Includes KPIs, date-wise time-series, correlation matrix, wind distribution, and textual insights.
    """
    if city.startswith("Uploaded ("):
        cid = city[len("Uploaded ("):-1]
        records = CUSTOM_DATASETS.get(cid)
        if not records:
            raise HTTPException(status_code=404, detail="Uploaded dataset not found")
    else:
        records = get_city_weather_dataset(city)

    result = filter_and_process_weather(
        records=records,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    result["city"] = city
    result["granularity"] = granularity
    return result


@app.get("/api/weather/date/{target_date}")
def get_date_analysis(
    target_date: str,
    city: str = Query("New York", description="City name")
):
    """
    Detailed date-wise deep dive for a single day:
    24-hour diurnal cycle, temp anomalies against 30-day baseline, and UV index.
    """
    if city.startswith("Uploaded ("):
        cid = city[len("Uploaded ("):-1]
        records = CUSTOM_DATASETS.get(cid)
        if not records:
            raise HTTPException(status_code=404, detail="Uploaded dataset not found")
    else:
        records = get_city_weather_dataset(city)

    return compute_date_deep_dive(records, target_date)


@app.post("/api/weather/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a custom CSV file with date-wise weather data.
    Expected columns: date (YYYY-MM-DD), tmax, tmin, tavg, rain, wind, hum, pres
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate columns
        required = ["date"]
        for col in required:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"CSV must contain '{col}' column")
                
        # Fill standard weather defaults if missing
        if "tmax" not in df.columns and "tavg" in df.columns:
            df["tmax"] = df["tavg"] + 4
        if "tmin" not in df.columns and "tavg" in df.columns:
            df["tmin"] = df["tavg"] - 4
        if "tavg" not in df.columns:
            df["tavg"] = (df["tmax"] + df["tmin"]) / 2
        if "rain" not in df.columns:
            df["rain"] = 0.0
        if "wind" not in df.columns:
            df["wind"] = 12.0
        if "hum" not in df.columns:
            df["hum"] = 55
        if "pres" not in df.columns:
            df["pres"] = 1013.0
        if "wind_dir" not in df.columns:
            df["wind_dir"] = "SW"
        if "condition" not in df.columns:
            df["condition"] = "Clear"

        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date").reset_index(drop=True)
        
        records = df.to_dict(orient="records")
        custom_id = f"custom_{datetime.datetime.now().strftime('%H%M%S')}"
        CUSTOM_DATASETS[custom_id] = records
        
        return {
            "status": "success",
            "dataset_id": f"Uploaded ({custom_id})",
            "rows_loaded": len(records),
            "min_date": records[0]["date"],
            "max_date": records[-1]["date"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")


@app.get("/api/weather/export")
def export_weather_csv(
    city: str = Query("New York"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Exports the filtered date-wise data as a downloadable CSV."""
    records = get_city_weather_dataset(city)
    df = pd.DataFrame(records)
    if start_date:
        df = df[df["date"] >= start_date]
    if end_date:
        df = df[df["date"] <= end_date]
        
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=weather_data_{city}_{start_date or 'start'}_to_{end_date or 'end'}.csv"
    return response


# Mount static directory and serve main HTML
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Weather Analysis API is Running.</h1><p>Index file not found in static folder.</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
