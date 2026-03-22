from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import requests
import os
import joblib
from groq import Groq

# ---------------- INIT ----------------
app = FastAPI(title="AgriTech API", version="3.0")

# ---------------- LOAD MODEL ----------------
model = None
BASE_DIR = os.path.dirname(__file__)
model_path = os.path.join(BASE_DIR, "model", "microbial_model.pkl")

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ Model loaded")
else:
    print("⚠️ Model not found")

# ---------------- CONFIG ----------------
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# ---------------- GROQ INIT ----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq connected")
else:
    print("⚠️ GROQ_API_KEY missing")

# ---------------- REQUEST MODELS ----------------
class SoilInput(BaseModel):
    ph: float
    n: float
    p: float
    k: float
    temperature: float

class WeatherInput(BaseModel):
    latitude: float
    longitude: float

class ChatInput(BaseModel):
    message: str
    language: str = "en"   # 🔥 added for multilingual

# ---------------- RESPONSE ----------------
def success(data):
    return {
        "status": "success",
        **data
    }

# ---------------- ROOT ----------------
@app.get("/")
def home():
    return {"status": "running", "message": "AgriTech API is live 🚀"}

# ---------------- HEALTH ----------------
@app.get("/health")
def health():
    return success({"message": "API healthy"})

# ---------------- PREDICT ----------------
@app.post("/predict")
def predict_soil(data: SoilInput):
    try:
        if model is None:
            return success({"microbial_score": 0.5})

        input_df = pd.DataFrame([data.dict()])
        score = float(model.predict(input_df)[0])

        return success({"microbial_score": round(score, 3)})

    except Exception as e:
        print("❌ PREDICT ERROR:", e)
        return success({"microbial_score": 0.5})

# ---------------- WEEKLY WEATHER ----------------
@app.post("/weather-location")
def weather_forecast(data: WeatherInput):
    try:
        if not WEATHER_API_KEY:
            return success({"forecast": [], "error": "API key missing"})

        res = requests.get(
            f"{WEATHER_BASE_URL}/forecast",
            params={
                "lat": data.latitude,
                "lon": data.longitude,
                "appid": WEATHER_API_KEY,
                "units": "metric"
            },
            timeout=5
        )

        if res.status_code != 200:
            return success({"forecast": [], "error": "Weather API failed"})

        d = res.json()
        forecast = []

        for item in d.get("list", []):
            if "12:00:00" in item["dt_txt"]:  # pick one per day
                forecast.append({
                    "date": item["dt_txt"].split(" ")[0],
                    "temperature": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "condition": item["weather"][0]["description"]
                })

        return success({"forecast": forecast})

    except Exception as e:
        print("❌ WEATHER ERROR:", e)
        return success({"forecast": []})

# ---------------- CHAT (GROQ AI) ----------------
@app.post("/chat-ai")
def chat_ai(data: ChatInput):
    try:
        if groq_client is None:
            return success({"reply": "Groq not initialized"})

        user_msg = data.message.strip().lower()
        print("📩 USER:", user_msg)

        # 🔥 OPTIONAL: instant reply for greetings (best UX)
        if user_msg in ["hi", "hello", "hey"]:
            return success({"reply": "Hello! 👋 How can I help you today?"})

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # ✅ fast + cheap model
            messages=[
                {
                    "role": "system",
                    "content": """
You are an agriculture assistant.

Rules:
- Keep replies SHORT (max 2–3 lines).
- Be clear, practical, and easy to understand.
- Only give detailed answers if user asks specific questions.
- Focus on soil, crops, fertilizers, irrigation, pests.
"""
                },
                {
                    "role": "user",
                    "content": data.message
                }
            ],
            temperature=0.4,   # 🔥 more consistent replies
            max_tokens=80      # 🔥 shorter output
        )

        reply = completion.choices[0].message.content.strip()

        print("🤖 REPLY:", reply)

        return success({"reply": reply})

    except Exception as e:
        print("❌ GROQ ERROR:", e)
        return success({
            "reply": "AI is temporarily unavailable. Please try again."
        })