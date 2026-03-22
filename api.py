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
                timeout=3
            )

            if response.status_code != 200:
                return None

            data = response.json()

            return {
                "city": data.get("name", "Unknown"),
                "temperature": round(data["main"]["temp"], 1),
                "humidity": data["main"]["humidity"],
                "rainfall": data.get("rain", {}).get("1h", 0.0),
                "condition": data["weather"][0]["description"]
            }

        except Exception as e:
            print("WEATHER ERROR:", e)
            return None

    # ---------------- WEEKLY WEATHER ----------------
    def get_weekly_weather(lat, lon):
        try:
            response = requests.get(
                f"{config.WEATHER_BASE_URL}/onecall",
                params={
                    "lat": lat,
                    "lon": lon,
                    "exclude": "current,minutely,hourly,alerts",
                    "appid": config.WEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=5
            )

            if response.status_code != 200:
                return None

            data = response.json()
            daily = data.get("daily", [])[:7]

            forecast = []

            for day in daily:
                forecast.append({
                    "date": datetime.fromtimestamp(day["dt"]).strftime("%Y-%m-%d"),
                    "day": datetime.fromtimestamp(day["dt"]).strftime("%A"),
                    "temp_day": round(day["temp"]["day"], 1),
                    "temp_night": round(day["temp"]["night"], 1),
                    "humidity": day["humidity"],
                    "condition": day["weather"][0]["description"]
                })

            return forecast

        except Exception as e:
            print("WEEKLY WEATHER ERROR:", e)
            return None

    # ---------------- ROUTES ----------------

    @app.route("/", methods=["GET"])
    def home():
        return success({"message": "AgriTech API Running"})

    # 🌱 SOIL PREDICTION
    @app.route("/predict", methods=["POST"])
    def predict_soil():
        if model is None:
            return error("Model not loaded")

        data = request.json or {}

        try:
            input_df = pd.DataFrame([{
                "ph": float(data.get("ph")),
                "n": float(data.get("n")),
                "p": float(data.get("p")),
                "k": float(data.get("k")),
                "temperature": float(data.get("temperature"))
            }])

            score = float(model.predict(input_df)[0])

            return success({
                "microbial_score": round(score, 3)
            })

        except Exception as e:
            return error(f"Prediction failed: {str(e)}")

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

    # 📅 WEEKLY FORECAST (NEW)
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
                {"day": "Today", "temp_day": 30, "condition": "clear sky"},
                {"day": "Tomorrow", "temp_day": 31, "condition": "cloudy"}
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

        except:
            return success({"reply": "AI error"})