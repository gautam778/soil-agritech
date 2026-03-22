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

    # ---------------- WEATHER (CURRENT) ----------------
    def get_weather_data(lat, lon):
        if not config.WEATHER_API_KEY:
            print("⚠️ WEATHER API KEY MISSING")
            return None

        try:
            res = requests.get(
                f"{config.WEATHER_BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": config.WEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=5
            )

            if res.status_code != 200:
                print("Weather API error:", res.text)
                return None

            data = res.json()

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

    # ---------------- WEATHER (WEEKLY) ----------------
    def get_weekly_weather(lat, lon):
        if not config.WEATHER_API_KEY:
            print("⚠️ WEATHER API KEY MISSING")
            return []

        try:
            res = requests.get(
                f"{config.WEATHER_BASE_URL}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": config.WEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=5
            )

            if res.status_code != 200:
                print("Forecast API error:", res.text)
                return []

            data = res.json()
            if "list" not in data:
                return []

            daily_map = {}

            for item in data["list"]:
                try:
                    date = item.get("dt_txt", "").split(" ")[0]
                    temp = item.get("main", {}).get("temp")

                    if not date or temp is None:
                        continue

                    condition = item.get("weather", [{}])[0].get("description", "")

                    if date not in daily_map:
                        daily_map[date] = {"temps": [], "conditions": []}

                    daily_map[date]["temps"].append(temp)
                    daily_map[date]["conditions"].append(condition)

                except:
                    continue

            forecast = []
            for date, values in list(daily_map.items())[:7]:
                try:
                    avg_temp = sum(values["temps"]) / len(values["temps"])
                    forecast.append({
                        "date": date,
                        "day": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                        "temp_day": round(avg_temp, 1),
                        "condition": values["conditions"][0] if values["conditions"] else "clear sky"
                    })
                except:
                    continue

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
        data = request.json or {}

        if model is None:
            print("⚠️ Model not loaded")
            return success({"microbial_score": 0.5})

        try:
            input_df = pd.DataFrame([{
                "ph": float(data.get("ph", 0)),
                "n": float(data.get("n", 0)),
                "p": float(data.get("p", 0)),
                "k": float(data.get("k", 0)),
                "temperature": float(data.get("temperature", 0))
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

        weather = get_weather_data(lat, lon) or {
            "city": "Unknown",
            "temperature": 25,
            "humidity": 60,
            "rainfall": 0.0,
            "condition": "clear sky"
        }

        return success({"weather": weather})

    # 📅 WEEKLY WEATHER
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
        msg = data.get("message", "").strip()

        if not msg:
            return error("Message required")

        if not groq_client:
            return success({"reply": "AI unavailable"})

        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": msg}]
            )

            reply = res.choices[0].message.content.strip()

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