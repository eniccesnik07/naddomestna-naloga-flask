from flask import Flask, request, session, jsonify, render_template
import os, requests
from datetime import datetime
from tinydb import TinyDB, Query

app = Flask(__name__, template_folder="templates3", static_folder="static3")
app.secret_key = "m1n2b3"

os.makedirs("db", exist_ok=True)
db           = TinyDB(os.path.join("db", "weather.json"), indent=4)
searches_tb  = db.table("searches")
favorites_tb = db.table("favorites")
Fav    = Query()

WMO_CODES = {
    0:"Jasno", 1:"Pretežno jasno", 2:"Delno oblačno",
    3:"Oblačno", 45:"Megla", 51:"Rosenje", 61:"Dež",
    63:"Zmeren dež", 65:"Ploha", 71:"Sneg", 73:"Zmeren sneg",
    80:"Nalivi", 95:"Nevihta", 99:"Huda nevihta"
}

def wmo_desc(code):
    return WMO_CODES.get(code, f"Koda {code}")

# ── Sinhroni klici – Flask vrne HTML stran ────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ── Asinhroni klici – AJAX API ────────────────────────────────────────────────

@app.route("/api/geocode")
def geocode():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": q, "count": 5, "language": "sl", "format": "json"},
            timeout=5
        )
        data = r.json().get("results", [])
        return jsonify([{
            "city":    d.get("name"),
            "country": d.get("country", ""),
            "lat":     d.get("latitude"),
            "lon":     d.get("longitude")
        } for d in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/weather")
def get_weather():
    try:
        lat     = float(request.args.get("lat"))
        lon     = float(request.args.get("lon"))
        city    = request.args.get("city", "")
        country = request.args.get("country", "")
    except (TypeError, ValueError):
        return jsonify({"error": "Manjkajoči parametri"}), 400
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current":  "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation",
                "daily":    "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum",
                "timezone": "auto", "forecast_days": 7
            },
            timeout=5
        )
        data = r.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    searches_tb.insert({
        "city": city, "country": country, "lat": lat, "lon": lon,
        "searched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    session["last_city"] = city

    cur   = data["current"]
    daily = data["daily"]
    return jsonify({
        "city": city, "country": country,
        "current": {
            "temp":       cur["temperature_2m"],
            "feels_like": cur["apparent_temperature"],
            "humidity":   cur["relative_humidity_2m"],
            "wind":       cur["wind_speed_10m"],
            "precip":     cur["precipitation"],
            "desc":       wmo_desc(cur["weather_code"])
        },
        "daily": [
            {"date": daily["time"][i], "max": daily["temperature_2m_max"][i],
             "min": daily["temperature_2m_min"][i], "desc": wmo_desc(daily["weather_code"][i]),
             "precip": daily["precipitation_sum"][i]}
            for i in range(len(daily["time"]))
        ]
    })

@app.route("/api/favorites")
def get_favorites():
    return jsonify(favorites_tb.all())

@app.route("/api/favorite", methods=["POST"])
def toggle_favorite():
    data = request.get_json()
    city = data.get("city", "")
    if favorites_tb.search(Fav.city == city):
        favorites_tb.remove(Fav.city == city)
        return jsonify({"status": "removed"})
    favorites_tb.insert({
        "city": city, "country": data.get("country", ""),
        "lat": data.get("lat"), "lon": data.get("lon")
    })
    return jsonify({"status": "added"})

@app.route("/api/recent")
def get_recent():
    all_s = sorted(searches_tb.all(), key=lambda s: s.get("searched_at", ""), reverse=True)
    seen, result = set(), []
    for s in all_s:
        if s["city"] not in seen:
            seen.add(s["city"])
            result.append(s)
        if len(result) >= 8:
            break
    return jsonify(result)

@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    searches_tb.truncate()
    session.pop("last_city", None)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True, port=5002)
