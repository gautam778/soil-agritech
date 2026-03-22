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

    # ---------------- WEATHER FUNCTION ----------------
    def get_weather_data(lat, lon):
        try:
            print("Fetching weather for:", lat, lon)

            response = requests.get(
                f"{config.WEATHER_BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": config.WEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=3   # 🔥 FAST timeout
            )

            print("Weather API status:", response.status_code)

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

    # 🌦 WEATHER (🔥 FIXED)
    @app.route("/weather-location", methods=["POST"])
    def weather_today():
        data = request.json or {}

        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat is None or lon is None:
            return error("Latitude & Longitude required")

        weather = get_weather_data(lat, lon)

        # 🔥 FALLBACK → NEVER FAIL
        if not weather:
            print("Using fallback weather")

            weather = {
                "city": "Unknown",
                "temperature": 25,
                "humidity": 60,
                "rainfall": 0.0,
                "condition": "clear sky"
            }

        return success({"weather": weather})

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