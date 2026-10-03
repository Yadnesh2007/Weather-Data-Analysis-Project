// Netlify Function for cities list
exports.handler = async function() {
  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    },
    body: JSON.stringify({
      cities: [
        { name: "New York", lat: 40.7128, lon: -74.0060, climate: "Humid Subtropical / Continental" },
        { name: "London", lat: 51.5074, lon: -0.1278, climate: "Temperate Oceanic" },
        { name: "Tokyo", lat: 35.6762, lon: 139.6503, climate: "Humid Subtropical" },
        { name: "Mumbai", lat: 19.0760, lon: 72.8777, climate: "Tropical Wet & Dry (Monsoon)" },
        { name: "San Francisco", lat: 37.7749, lon: -122.4194, climate: "Warm-summer Mediterranean" },
        { name: "Sydney", lat: -33.8688, lon: 151.2093, climate: "Humid Subtropical" }
      ]
    })
  };
};
