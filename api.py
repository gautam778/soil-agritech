from flask import jsonify, request
import pandas as pd
import requests
from datetime import datetime

def register_routes(app, model, groq_client, config, session_data):

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

    # ---------------- WEATHER ----------------
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

    # ---------------- ROUTES ----------------

    @app.route("/health", methods=["GET"])
    def health():
        return success({"message": "API healthy"})

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

    # ---------------- GLOBAL ERROR ----------------
    @app.errorhandler(Exception)
    def handle_exception(e):
        print("GLOBAL ERROR:", str(e))
        return jsonify({
            "status": "failed",
            "error": "Internal server error"
        }), 500