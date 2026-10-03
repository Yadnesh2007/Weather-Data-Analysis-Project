// Netlify Function for single date deep dive
exports.handler = async function(event, context) {
  const params = event.queryStringParameters || {};
  const targetDate = params.date || event.path.split("/").pop();
  
  const d = new Date(targetDate + "T12:00:00");
  const dayName = isNaN(d.getTime()) ? "Mon" : d.toLocaleDateString("en-US", { weekday: "short" });

  const hourly = [];
  const tmin = 18.0, tmax = 29.5;
  for (let h = 0; h < 24; h++) {
    const factor = (Math.sin((h - 8) * Math.PI / 12) + 1) / 2;
    hourly.push({
      hour: `${h.toString().padStart(2, "0")}:00`,
      temp: +(tmin + (tmax - tmin) * factor).toFixed(1),
      humidity: Math.round(75 - factor * 25),
      rain: 0,
      wind: +(12 + factor * 5).toFixed(1)
    });
  }

  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    },
    body: JSON.stringify({
      date: targetDate,
      day: dayName,
      condition: "Clear / Sunny",
      tmax: 29.5,
      tmin: 18.0,
      tavg: 24.2,
      rain: 0.0,
      hum: 58,
      wind: 14.5,
      wind_dir: "SW",
      pres: 1014.2,
      uv_index: 6,
      baseline_tavg: 22.8,
      temp_anomaly: 1.4,
      hourly: hourly
    })
  };
};
