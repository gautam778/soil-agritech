from flask import jsonify, request
import pandas as pd
import requests
from datetime import datetime

def register_routes(app, model, groq_client, config, session_data):

    # ---------------- RESPONSE HELPERS ----------------
    def success(data):
        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **data
        })

    def error(msg):
        return jsonify({
            "status": "failed",
            "error": msg
        }), 400

    # ---------------- CURRENT WEATHER ----------------
    def get_weather_data(lat, lon):
        try:
            response = requests.get(
                f"{config.WEATHER_BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": config.WEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=2
            )

            if response.status_code != 200:
                print("Weather API failed:", response.text)
                return None

            data = response.json()

            return {
                "city": data.get("name", "Unknown"),
                "temperature": round(data.get("main", {}).get("temp", 25), 1),
                "humidity": data.get("main", {}).get("humidity", 60),
                "rainfall": data.get("rain", {}).get("1h", 0.0),
                "condition": data.get("weather", [{}])[0].get("description", "clear sky")
            }

        except Exception as e:
            print("WEATHER ERROR:", e)
            return None

    # ---------------- WEEKLY WEATHER (FIXED) ----------------
    def get_weekly_weather(lat, lon):
        try:
            response = requests.get(
                f"{config.WEATHER_BASE_URL}/forecast",  # ✅ SAFE FREE API
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": config.WEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=3
            )

            print("Forecast status:", response.status_code)

            if response.status_code != 200:
                print("Forecast error:", response.text)
                return []

            data = response.json()

            # 🔥 Convert 3-hour data → daily summary
            daily_map = {}

            for item in data.get("list", []):
                date = item["dt_txt"].split(" ")[0]

                if date not in daily_map:
                    daily_map[date] = {
                        "temps": [],
                        "conditions": []
                    }

                daily_map[date]["temps"].append(item["main"]["temp"])
                daily_map[date]["conditions"].append(item["weather"][0]["description"])

            forecast = []

            for date, values in list(daily_map.items())[:7]:
                forecast.append({
                    "date": date,
                    "day": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                    "temp_day": round(sum(values["temps"]) / len(values["temps"]), 1),
                    "condition": values["conditions"][0]
                })

            return forecast

        except Exception as e:
            print("WEEKLY ERROR:", e)
            return []

    # ---------------- ROUTES ----------------

    @app.route("/health", methods=["GET"])
    def health():
        return success({"message": "API healthy"})

    # 🌱 SOIL PREDICTION
    @app.route("/predict", methods=["POST"])
    def predict_soil():
        if model is None:
            return error("Model not loaded")

        data = request.json or {}

        try:
            ph = float(data.get("ph", 0))
            n = float(data.get("n", 0))
            p = float(data.get("p", 0))
            k = float(data.get("k", 0))
            temp = float(data.get("temperature", 0))

            input_df = pd.DataFrame([{
                "ph": ph,
                "n": n,
                "p": p,
                "k": k,
                "temperature": temp
            }])

            score = float(model.predict(input_df)[0])

            return success({
                "microbial_score": round(score, 3)
            })

        except Exception as e:
            print("PREDICT ERROR:", e)
            return success({"microbial_score": 0.5})

    # 🌦 CURRENT WEATHER
    @app.route("/weather-location", methods=["POST"])
    def weather_today():
        data = request.json or {}

        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat is None or lon is None:
            return error("Latitude & Longitude required")

        weather = get_weather_data(lat, lon)

        if not weather:
            weather = {
                "city": "Unknown",
                "temperature": 25,
                "humidity": 60,
                "rainfall": 0.0,
                "condition": "clear sky"
            }

        return success({"weather": weather})

    # 📅 WEEKLY FORECAST
    @app.route("/weather-weekly", methods=["POST"])
    def weather_weekly():
        data = request.json or {}

        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat is None or lon is None:
            return error("Latitude & Longitude required")

        forecast = get_weekly_weather(lat, lon)

        if not forecast:
            forecast = [
                {"day": "Today", "temp_day": 30, "condition": "clear sky"}
            ]

        return success({"forecast": forecast})

    # 🤖 CHAT AI
    @app.route("/chat-ai", methods=["POST"])
    def chat_ai():
        data = request.json or {}
        msg = data.get("message", "")

        if not msg:
            return error("Message required")

        if not groq_client:
            return success({"reply": "AI unavailable"})

        try:
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": msg}]
            )

            reply = response.choices[0].message.content.strip()

            return success({"reply": reply})

        except Exception as e:
            print("CHAT ERROR:", e)
            return success({"reply": "AI error"})

    # ---------------- GLOBAL ERROR HANDLER ----------------
    @app.errorhandler(Exception)
    def handle_exception(e):
        print("GLOBAL ERROR:", str(e))
        return jsonify({
            "status": "failed",
            "error": "Internal server error"
        }), 500