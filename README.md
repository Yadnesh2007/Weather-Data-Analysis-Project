# Weather Analysis & Date-Wise Meteorological Intelligence Dashboard

A full-stack weather analysis web application with an interactive modern dashboard frontend (Chart.js, glassmorphic UI, responsive themes) powered by a high-performance **Python backend (FastAPI, Pandas, NumPy)**.

---

## 🌟 Key Features

1. **Date-Wise Meteorological Analysis**:
   - Filter any custom date range (`start_date` to `end_date`) or use one-click presets (**7 Days**, **30 Days**, **90 Days**, **Full Year**).
   - Dynamic time-series aggregation: **Daily (Date-wise)**, **Weekly summaries**, or **Monthly aggregates**.
   - Date-wise KPI badges highlighting the exact calendar dates of:
     - 🌡️ **Maximum & Minimum Temperatures** (with exact date of occurrence)
     - 🌧️ **Wettest Day & Total Precipitation**
     - 💨 **Peak Wind Gust Day & Prevailing Direction**
     - 💧 **Lowest Relative Humidity Day**

2. **Python Analytics Engine (`analytics.py`)**:
   - Real-time **Pearson Correlation Matrix** computed across Temperature, Rainfall, Wind Speed, Humidity, and Atmospheric Pressure.
   - **Automated Textual Insights**: Natural-language findings generated from the filtered date range.
   - **Wind Rose Quadrant Analysis**: Percentage distribution across 8 compass directions.
   - **Cumulative Precipitation Curves** & Diurnal temperature variations.

3. **Date Deep-Dive Inspector**:
   - Click on any point on the charts (or click **"Inspect Date"**) to open an in-depth breakdown for that exact date:
     - 24-hour diurnal temperature curve and humidity cycle.
     - Atmospheric anomaly comparison against the surrounding 30-day baseline (e.g., `+3.2°C warmer than normal`).
     - UV Index rating and localized weather condition badge.

4. **Multi-City Profiles & Custom CSV Upload**:
   - Switch between diverse climate profiles: **New York**, **London**, **Tokyo**, **Mumbai (Monsoon dynamics)**, **San Francisco**, and **Sydney**.
   - **Upload your own weather CSV** via the dashboard modal with automatic column normalization and immediate analysis.
   - **Export CSV** button to download date-filtered datasets.

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.9+

### 2. Activate Virtual Environment & Run Backend

```bash
cd /Users/yadnesh/.gemini/antigravity-ide/scratch/weather-analysis-app

# Activate the virtual environment
source venv/bin/activate

# Run the FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Then open your browser at:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Interactive API documentation (Swagger UI) is also available at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/weather/analysis` | Date-wise time series, KPIs, correlation matrix & insights |
| `GET` | `/api/weather/date/{date}` | 24-hour diurnal breakdown & baseline anomaly for a single day |
| `GET` | `/api/weather/cities` | List of supported climate profiles and locations |
| `POST` | `/api/weather/upload` | Upload and analyze a custom daily weather CSV |
| `GET` | `/api/weather/export` | Export filtered date-range data as a CSV file |

---

## 📁 Project Structure

```
weather-analysis-app/
├── main.py              # FastAPI server & route handlers
├── weather_data.py      # Meteorological data generator & multi-city models
├── analytics.py         # Pandas/NumPy statistical engine & insights generator
├── requirements.txt     # Python dependencies
├── README.md            # Documentation & setup guide
├── static/
│   └── index.html       # Full frontend dashboard with date controls & Chart.js
└── venv/                # Python virtual environment
```
