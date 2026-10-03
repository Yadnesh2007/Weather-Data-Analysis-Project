// Netlify Serverless Function for Weather Date-Wise Analysis

const CITIES = {
  "New York": { lat: 40.7128, base_temp: 13.0, temp_amp: 14.0, rain_factor: 1.0, wind_base: 14.0 },
  "London": { lat: 51.5074, base_temp: 11.5, temp_amp: 8.0, rain_factor: 0.85, wind_base: 16.0 },
  "Tokyo": { lat: 35.6762, base_temp: 16.0, temp_amp: 12.0, rain_factor: 1.3, wind_base: 11.0 },
  "Mumbai": { lat: 19.0760, base_temp: 27.5, temp_amp: 3.5, rain_factor: 2.2, wind_base: 12.5 },
  "San Francisco": { lat: 37.7749, base_temp: 14.5, temp_amp: 4.0, rain_factor: 0.7, wind_base: 18.0 },
  "Sydney": { lat: -33.8688, base_temp: 18.5, temp_amp: 7.0, rain_factor: 1.1, wind_base: 15.0 }
};

const DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];

// Deterministic Pseudo-Random Generator
function makeRng(seed) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return function() {
    return (s = (s * 16807) % 2147483647) / 2147483647;
  };
}

function generateCityData(cityName, days = 365, endDate = new Date(2024, 11, 31)) {
  const cfg = CITIES[cityName] || CITIES["New York"];
  const rng = makeRng((cityName.charCodeAt(0) * 1000 + cityName.charCodeAt(cityName.length - 1)) & 0x7fffffff);
  const phaseShift = cfg.lat < 0 ? Math.PI : 0;
  const records = [];

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(endDate);
    d.setDate(d.getDate() - i);
    const dayOfYear = Math.floor((d - new Date(d.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
    const seasonAngle = (2 * Math.PI * (dayOfYear - 20) / 365.25) - phaseShift;
    const seasonalTemp = cfg.base_temp + cfg.temp_amp * Math.sin(seasonAngle);

    const tempNoise = (rng() - 0.5) * 5.0;
    const tavg = +(seasonalTemp + tempNoise).toFixed(1);
    const spread = 8.0 + rng() * 4.0;
    const tmax = +(tavg + spread / 2).toFixed(1);
    const tmin = +(tavg - spread / 2).toFixed(1);

    const isRain = rng() < (cityName === "Mumbai" && dayOfYear >= 152 && dayOfYear <= 273 ? 0.75 : 0.28);
    const rain = isRain ? +(rng() * 18 * cfg.rain_factor).toFixed(1) : 0;
    const hum = Math.max(25, Math.min(96, Math.round(62 - (tavg - 15) * 0.7 + (rain > 0 ? 16 : -4) + (rng() - 0.5) * 10)));
    const pres = +(1013 + (rain > 10 ? -10 : 2) + (rng() - 0.5) * 6).toFixed(1);
    const wind = +(cfg.wind_base + 3 * Math.cos(seasonAngle) + rng() * 6).toFixed(1);
    const dirIdx = Math.floor(rng() * DIRS.length);
    const wind_dir = DIRS[dirIdx];

    let condition = "Clear / Sunny";
    if (rain > 15) condition = "Thunderstorm / Heavy Rain";
    else if (rain > 4) condition = "Moderate Rain";
    else if (rain > 0) condition = "Light Rain / Showers";
    else if (hum > 75) condition = "Partly Cloudy";

    records.push({
      date: d.toISOString().split("T")[0],
      day: d.toLocaleDateString("en-US", { weekday: "short" }),
      month: d.toLocaleDateString("en-US", { month: "short" }),
      year: d.getFullYear(),
      tmax, tmin, tavg, rain, wind, wind_dir, hum, pres, condition,
      uv_index: Math.max(1, Math.min(11, Math.round(Math.max(0, Math.sin(seasonAngle + Math.PI / 2)) * 10)))
    });
  }
  return records;
}

function corr(a, b) {
  const n = a.length;
  const meanA = a.reduce((x, y) => x + y, 0) / n;
  const meanB = b.reduce((x, y) => x + y, 0) / n;
  let num = 0, denA = 0, denB = 0;
  for (let i = 0; i < n; i++) {
    const da = a[i] - meanA;
    const db = b[i] - meanB;
    num += da * db;
    denA += da * da;
    denB += db * db;
  }
  return denA && denB ? +(num / Math.sqrt(denA * denB)).toFixed(2) : 0;
}

exports.handler = async function(event, context) {
  const params = event.queryStringParameters || {};
  const city = params.city || "New York";
  const startDate = params.start_date;
  const endDate = params.end_date;
  const granularity = params.granularity || "daily";

  let records = generateCityData(city);
  if (startDate) records = records.filter(r => r.date >= startDate);
  if (endDate) records = records.filter(r => r.date <= endDate);

  if (records.length === 0) {
    return {
      statusCode: 400,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      body: JSON.stringify({ error: "No records found for date range" })
    };
  }

  // KPIs
  let maxTemp = -999, minTemp = 999, maxTempDate = "", minTempDate = "";
  let totalRain = 0, maxRain = 0, maxRainDate = "", rainyDays = 0;
  let peakWind = 0, peakWindDate = "", totalWind = 0;
  let totalHum = 0, minHum = 999, minHumDate = "", totalPres = 0, totalTavg = 0;

  records.forEach(r => {
    if (r.tmax > maxTemp) { maxTemp = r.tmax; maxTempDate = r.date; }
    if (r.tmin < minTemp) { minTemp = r.tmin; minTempDate = r.date; }
    totalTavg += r.tavg;
    totalRain += r.rain;
    if (r.rain > maxRain) { maxRain = r.rain; maxRainDate = r.date; }
    if (r.rain > 0.1) rainyDays++;
    if (r.wind > peakWind) { peakWind = r.wind; peakWindDate = r.date; }
    totalWind += r.wind;
    totalHum += r.hum;
    if (r.hum < minHum) { minHum = r.hum; minHumDate = r.date; }
    totalPres += r.pres;
  });

  const n = records.length;
  const avgTemp = +(totalTavg / n).toFixed(1);
  const avgWind = +(totalWind / n).toFixed(1);
  const avgHum = Math.round(totalHum / n);
  const avgPres = +(totalPres / n).toFixed(1);
  totalRain = +totalRain.toFixed(1);

  // Compass Rose
  const dirCounts = {};
  DIRS.forEach(d => dirCounts[d] = 0);
  records.forEach(r => dirCounts[r.wind_dir] = (dirCounts[r.wind_dir] || 0) + 1);
  const rose = {};
  DIRS.forEach(d => rose[d] = +((dirCounts[d] / n) * 100).toFixed(1));

  // Cumulative rain and series
  let runRain = 0;
  const timeSeries = records.map(r => {
    runRain += r.rain;
    return {
      date: r.date,
      label: new Date(r.date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      tmax: r.tmax,
      tmin: r.tmin,
      tavg: r.tavg,
      rain: r.rain,
      cum_rain: +runRain.toFixed(1),
      cum_rain_pct: totalRain > 0 ? +((runRain / totalRain) * 100).toFixed(1) : 0,
      wind: r.wind,
      hum: r.hum,
      pres: r.pres,
      condition: r.condition
    };
  });

  // Correlation Matrix
  const keys = ["tavg", "rain", "wind", "hum", "pres"];
  const corrMatrix = {};
  keys.forEach(k1 => {
    corrMatrix[k1] = {};
    keys.forEach(k2 => {
      corrMatrix[k1][k2] = corr(records.map(r => r[k1]), records.map(r => r[k2]));
    });
  });

  // Key Findings
  const sortedDirs = Object.entries(rose).sort((a, b) => b[1] - a[1]);
  const insights = [
    `Selected range covers <b>${n} days</b> (${records[0].date} to ${records[records.length - 1].date}). Highest high was <b>${maxTemp}°C on ${maxTempDate}</b>, with lowest at <b>${minTemp}°C on ${minTempDate}</b>.`,
    `Total precipitation of <b>${totalRain} mm</b> recorded across ${rainyDays} wet days. Peak 24h rainfall reached <b>${maxRain} mm on ${maxRainDate}</b>.`,
    `Wind gusts peaked at <b>${peakWind} km/h on ${peakWindDate}</b>. Dominant quadrant winds were <b>${sortedDirs[0][0]} (${sortedDirs[0][1]}%)</b> and <b>${sortedDirs[1][0]} (${sortedDirs[1][1]}%)</b>.`,
    `Temperature and pressure correlation is r = ${corrMatrix.tavg.pres}, indicating seasonal barometric transitions.`
  ];

  const payload = {
    city,
    granularity,
    kpis: {
      avg_temp: avgTemp,
      min_temp: minTemp,
      max_temp: maxTemp,
      max_temp_date: maxTempDate,
      min_temp_date: minTempDate,
      total_rain: totalRain,
      rainy_days: rainyDays,
      max_rain: maxRain,
      max_rain_date: maxRainDate,
      peak_wind: peakWind,
      peak_wind_date: peakWindDate,
      avg_wind: avgWind,
      avg_hum: avgHum,
      min_hum: minHum,
      min_hum_date: minHumDate,
      avg_pres: avgPres,
      total_days: n
    },
    time_series: timeSeries,
    rose,
    scatter: records.map(r => ({ x: r.hum, y: r.rain, date: r.date })),
    correlation: corrMatrix,
    insights,
    date_bounds: {
      min_date: records[0].date,
      max_date: records[records.length - 1].date
    }
  };

  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS"
    },
    body: JSON.stringify(payload)
  };
};
