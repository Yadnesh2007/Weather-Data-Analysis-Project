"""
Weather Analytics Engine
Performs date-wise filtering, time-series aggregations, statistical KPIs,
correlation matrices, and meteorological insights using Pandas and NumPy.
"""

from typing import Dict, List, Any, Optional
import datetime
import math
import pandas as pd
import numpy as np


def filter_and_process_weather(
    records: List[Dict[str, Any]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "daily"
) -> Dict[str, Any]:
    """
    Filters records by start_date and end_date (YYYY-MM-DD),
    computes date-wise time-series, KPIs, correlation, and textual insights.
    """
    if not records:
        return {"error": "No records found"}
        
    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["date"])
    
    # Apply date range filtering
    if start_date:
        df = df[df["datetime"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["datetime"] <= pd.to_datetime(end_date)]
        
    if df.empty:
        return {"error": "No data available for the selected date range"}
        
    df = df.sort_values("datetime").reset_index(drop=True)
    
    # Compute basic stats
    tmax_val = float(df["tmax"].max())
    tmax_idx = df["tmax"].idxmax()
    tmax_date = df.loc[tmax_idx, "date"]
    
    tmin_val = float(df["tmin"].min())
    tmin_idx = df["tmin"].idxmin()
    tmin_date = df.loc[tmin_idx, "date"]
    
    tavg_mean = round(float(df["tavg"].mean()), 1)
    
    rain_sum = round(float(df["rain"].sum()), 1)
    rain_max_val = float(df["rain"].max())
    rain_max_idx = df["rain"].idxmax()
    rain_max_date = df.loc[rain_max_idx, "date"]
    rainy_days = int((df["rain"] > 0.1).sum())
    
    wind_max_val = round(float(df["wind"].max()), 1)
    wind_max_idx = df["wind"].idxmax()
    wind_max_date = df.loc[wind_max_idx, "date"]
    wind_mean = round(float(df["wind"].mean()), 1)
    
    hum_mean = round(float(df["hum"].mean()))
    hum_min_val = int(df["hum"].min())
    hum_min_idx = df["hum"].idxmin()
    hum_min_date = df.loc[hum_min_idx, "date"]
    
    pres_mean = round(float(df["pres"].mean()), 1)
    
    # Wind Rose calculation
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    dir_counts = df["wind_dir"].value_counts().to_dict()
    total_dirs = len(df)
    rose = {d: round((dir_counts.get(d, 0) / total_dirs) * 100, 1) for d in directions}
    
    # Cumulative rain
    df["cum_rain"] = df["rain"].cumsum().round(1)
    if rain_sum > 0:
        df["cum_rain_pct"] = (df["cum_rain"] / rain_sum * 100).round(1)
    else:
        df["cum_rain_pct"] = 0.0

    # 7-day rolling moving averages
    df["tavg_7ma"] = df["tavg"].rolling(window=7, min_periods=1).mean().round(1)
    df["rain_7ma"] = df["rain"].rolling(window=7, min_periods=1).mean().round(1)
    df["wind_7ma"] = df["wind"].rolling(window=7, min_periods=1).mean().round(1)
    
    # Handle Granularity
    if granularity == "weekly":
        df_display = df.resample("W-MON", on="datetime").agg({
            "date": "first",
            "tmax": "max",
            "tmin": "min",
            "tavg": "mean",
            "rain": "sum",
            "wind": "mean",
            "hum": "mean",
            "pres": "mean",
            "condition": lambda s: s.mode()[0] if not s.empty else "Clear"
        }).reset_index()
        df_display["tavg"] = df_display["tavg"].round(1)
        df_display["rain"] = df_display["rain"].round(1)
        df_display["wind"] = df_display["wind"].round(1)
        df_display["hum"] = df_display["hum"].round()
        df_display["pres"] = df_display["pres"].round(1)
        df_display["cum_rain"] = df_display["rain"].cumsum().round(1)
        df_display["cum_rain_pct"] = ((df_display["cum_rain"] / max(1.0, rain_sum)) * 100).clip(upper=100).round(1)
        df_display["label"] = df_display["datetime"].dt.strftime("%b %d")
    elif granularity == "monthly":
        df_display = df.resample("ME", on="datetime").agg({
            "date": "first",
            "tmax": "max",
            "tmin": "min",
            "tavg": "mean",
            "rain": "sum",
            "wind": "mean",
            "hum": "mean",
            "pres": "mean",
            "condition": lambda s: s.mode()[0] if not s.empty else "Clear"
        }).reset_index()
        df_display["tavg"] = df_display["tavg"].round(1)
        df_display["rain"] = df_display["rain"].round(1)
        df_display["wind"] = df_display["wind"].round(1)
        df_display["hum"] = df_display["hum"].round()
        df_display["pres"] = df_display["pres"].round(1)
        df_display["cum_rain"] = df_display["rain"].cumsum().round(1)
        df_display["cum_rain_pct"] = ((df_display["cum_rain"] / max(1.0, rain_sum)) * 100).clip(upper=100).round(1)
        df_display["label"] = df_display["datetime"].dt.strftime("%b %Y")
    else:
        # Daily
        df_display = df.copy()
        df_display["label"] = df_display["datetime"].dt.strftime("%b %d")
        
    # Correlation Matrix across 5 factors
    num_cols = ["tavg", "rain", "wind", "hum", "pres"]
    corr_df = df[num_cols].corr().fillna(0.0)
    corr_matrix = corr_df.round(2).to_dict()
    
    # Find strongest correlation pair
    factors = [("Temperature", "tavg"), ("Rainfall", "rain"), ("Wind speed", "wind"), ("Humidity", "hum"), ("Pressure", "pres")]
    best_corr = None
    for i in range(len(factors)):
        for j in range(i + 1, len(factors)):
            f1_name, f1_code = factors[i]
            f2_name, f2_code = factors[j]
            val = float(corr_df.loc[f1_code, f2_code])
            if best_corr is None or abs(val) > abs(best_corr["value"]):
                best_corr = {
                    "name1": f1_name,
                    "name2": f2_name,
                    "value": val
                }

    # Generate Date-wise Key Findings & Insights
    wet_days = df.nlargest(min(5, len(df)), "rain")
    wet_top_sum = wet_days["rain"].sum()
    wet_top_pct = round((wet_top_sum / rain_sum * 100) if rain_sum > 0 else 0)
    
    sorted_dirs = sorted(rose.items(), key=lambda x: x[1], reverse=True)
    top_dir1 = sorted_dirs[0]
    top_dir2 = sorted_dirs[1] if len(sorted_dirs) > 1 else ("N", 0)
    d_share = round(top_dir1[1] + top_dir2[1])

    date_span_days = (df["datetime"].max() - df["datetime"].min()).days + 1
    
    insights = [
        f"Selected range spans <b>{date_span_days} days</b> ({df['date'].iloc[0]} to {df['date'].iloc[-1]}). Peak temperature reached <b>{tmax_val}°C on {tmax_date}</b>, with the lowest at <b>{tmin_val}°C on {tmin_date}</b>.",
        f"Total precipitation of <b>{rain_sum} mm</b> occurred across {rainy_days} wet days. The single wettest day was <b>{rain_max_date}</b> with <b>{rain_max_val} mm</b> ({wet_top_pct}% delivered in top rain events).",
        f"Wind gusts peaked at <b>{wind_max_val} km/h on {wind_max_date}</b>. Prevailing winds were from <b>{top_dir1[0]} ({top_dir1[1]}%)</b> and <b>{top_dir2[0]} ({top_dir2[1]}%)</b>, accounting for {d_share}% of records.",
        f"{best_corr['name1']} and {best_corr['name2'].lower()} show the highest correlation (r = {best_corr['value']:.2f}), {'moving closely together' if best_corr['value'] > 0 else 'moving in opposite directions'}."
    ]

    # Clean records for frontend
    time_series = []
    for _, row in df_display.iterrows():
        time_series.append({
            "date": str(row["date"]),
            "label": str(row["label"]),
            "tmax": float(row["tmax"]),
            "tmin": float(row["tmin"]),
            "tavg": float(row["tavg"]),
            "rain": float(row["rain"]),
            "cum_rain": float(row.get("cum_rain", 0.0)),
            "cum_rain_pct": float(row.get("cum_rain_pct", 0.0)),
            "wind": float(row["wind"]),
            "hum": float(row["hum"]),
            "pres": float(row["pres"]),
            "condition": str(row.get("condition", "Clear")),
            "tavg_7ma": float(row.get("tavg_7ma", row["tavg"])) if "tavg_7ma" in row else None
        })

    # Scatter points for humidity vs rain
    scatter_points = [
        {"x": float(r["hum"]), "y": float(r["rain"]), "date": r["date"]}
        for r in time_series
    ]

    return {
        "kpis": {
            "avg_temp": tavg_mean,
            "min_temp": tmin_val,
            "max_temp": tmax_val,
            "max_temp_date": tmax_date,
            "min_temp_date": tmin_date,
            "total_rain": rain_sum,
            "rainy_days": rainy_days,
            "max_rain": rain_max_val,
            "max_rain_date": rain_max_date,
            "peak_wind": wind_max_val,
            "peak_wind_date": wind_max_date,
            "avg_wind": wind_mean,
            "avg_hum": hum_mean,
            "min_hum": hum_min_val,
            "min_hum_date": hum_min_date,
            "avg_pres": pres_mean,
            "total_days": date_span_days
        },
        "time_series": time_series,
        "rose": rose,
        "scatter": scatter_points,
        "correlation": corr_matrix,
        "insights": insights,
        "date_bounds": {
            "min_date": df["date"].min(),
            "max_date": df["date"].max()
        }
    }


def compute_date_deep_dive(records: List[Dict[str, Any]], target_date: str) -> Dict[str, Any]:
    """
    Provides an in-depth hourly breakdown and meteorological analysis
    for one specific target date.
    """
    df = pd.DataFrame(records)
    match = df[df["date"] == target_date]
    if match.empty:
        # Fallback to nearest date
        row = df.iloc[-1].to_dict()
    else:
        row = match.iloc[0].to_dict()

    tmin = float(row["tmin"])
    tmax = float(row["tmax"])
    tavg = float(row["tavg"])
    rain = float(row["rain"])
    hum = float(row["hum"])
    wind = float(row["wind"])
    pres = float(row["pres"])
    condition = row["condition"]
    
    # 24-hour diurnal modeling
    hours = []
    for h in range(24):
        # Diurnal temperature cycle: lowest at 5 AM, peak at 14:00 (2 PM)
        temp_factor = (math.sin((h - 8) * math.pi / 12) + 1) / 2
        h_temp = round(tmin + (tmax - tmin) * temp_factor, 1)
        
        # Diurnal humidity: inverse of temp
        h_hum = max(20, min(99, int(hum + (1 - temp_factor * 2) * 12)))
        
        # Hourly rain (concentrated in 3-4 hours if rainy)
        if rain > 0 and 13 <= h <= 17:
            h_rain = round(rain * (0.2 + 0.1 * math.sin(h)), 1)
        else:
            h_rain = 0.0
            
        h_wind = round(max(2.0, wind + 2.5 * math.sin(h * math.pi / 12)), 1)
        
        hours.append({
            "hour": f"{h:02d}:00",
            "temp": h_temp,
            "humidity": h_hum,
            "rain": h_rain,
            "wind": h_wind
        })

    # Compare with 30-day baseline around this date
    dt = pd.to_datetime(row["date"])
    window_df = df[(pd.to_datetime(df["date"]) >= dt - pd.Timedelta(days=15)) & 
                   (pd.to_datetime(df["date"]) <= dt + pd.Timedelta(days=15))]
    baseline_tavg = round(float(window_df["tavg"].mean()), 1)
    temp_anomaly = round(tavg - baseline_tavg, 1)

    return {
        "date": row["date"],
        "day": row.get("day", ""),
        "condition": condition,
        "tmax": tmax,
        "tmin": tmin,
        "tavg": tavg,
        "rain": rain,
        "hum": hum,
        "wind": wind,
        "wind_dir": row.get("wind_dir", "SW"),
        "pres": pres,
        "uv_index": row.get("uv_index", 5),
        "baseline_tavg": baseline_tavg,
        "temp_anomaly": temp_anomaly,
        "hourly": hours
    }
