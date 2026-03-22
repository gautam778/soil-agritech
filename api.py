from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import requests
from datetime import datetime
import os
import joblib

# ---------------- INIT ----------------
app = FastAPI(title="AgriTech API", version="1.0")

# ---------------- LOAD MODEL ----------------
model = None
try:
    BASE_DIR = os.path.dirname(__file__)
    model_path = os.path.join(BASE_DIR, "model", "microbial_model.pkl")

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print("✅ Model loaded")
    else:
        print("⚠️ Model not found:", model_path)

except Exception as e:
    print("❌ MODEL ERROR:", e)

# ---------------- CONFIG ----------------
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

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

# ---------------- RESPONSE HELPER ----------------
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
            print("⚠️ Model not loaded, using fallback")
            return success({"microbial_score": 0.5})

        # Convert to DataFrame
        input_df = pd.DataFrame([data.dict()])

        # Predict
        score = float(model.predict(input_df)[0])

        return success({
            "microbial_score": round(score, 3)
        })

    except Exception as e:
        print("❌ PREDICT ERROR:", e)
        return success({"microbial_score": 0.5})

# ---------------- WEATHER ----------------
@app.post("/weather-location")
def weather_today(data: WeatherInput):
    try:
        if not WEATHER_API_KEY:
            return success({"weather": {}, "error": "API key missing"})

        res = requests.get(
            f"{WEATHER_BASE_URL}/weather",
            params={
                "lat": data.latitude,
                "lon": data.longitude,
                "appid": WEATHER_API_KEY,
                "units": "metric"
            },
            timeout=5
        )

        if res.status_code != 200:
            return success({"weather": {}, "error": "Weather API failed"})

        d = res.json()

        weather = {
            "city": d.get("name", "Unknown"),
            "temperature": d.get("main", {}).get("temp", 25),
            "humidity": d.get("main", {}).get("humidity", 60),
            "rainfall": d.get("rain", {}).get("1h", 0.0),
            "condition": d.get("weather", [{}])[0].get("description", "clear sky")
        }

        return success({"weather": weather})

    except Exception as e:
        print("❌ WEATHER ERROR:", e)
        return success({"weather": {}})

# ---------------- CHAT ----------------
@app.post("/chat-ai")
def chat_ai(data: ChatInput):
    try:
        return success({
            "reply": f"You said: {data.message}"
        })
    except Exception as e:
        print("❌ CHAT ERROR:", e)
        return success({"reply": "Error processing request"})
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import requests
from datetime import datetime
import os
import joblib

# ---------------- INIT ----------------
app = FastAPI(title="AgriTech API", version="1.0")

# ---------------- LOAD MODEL ----------------
model = None
try:
    BASE_DIR = os.path.dirname(__file__)
    model_path = os.path.join(BASE_DIR, "model", "microbial_model.pkl")

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print("✅ Model loaded")
    else:
        print("⚠️ Model not found:", model_path)

except Exception as e:
    print("❌ MODEL ERROR:", e)

# ---------------- CONFIG ----------------
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

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

# ---------------- RESPONSE HELPER ----------------
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
            print("⚠️ Model not loaded, using fallback")
            return success({"microbial_score": 0.5})

        # Convert to DataFrame
        input_df = pd.DataFrame([data.dict()])

        # Predict
        score = float(model.predict(input_df)[0])

        return success({
            "microbial_score": round(score, 3)
        })

    except Exception as e:
        print("❌ PREDICT ERROR:", e)
        return success({"microbial_score": 0.5})

# ---------------- WEATHER ----------------
@app.post("/weather-location")
def weather_today(data: WeatherInput):
    try:
        if not WEATHER_API_KEY:
            return success({"weather": {}, "error": "API key missing"})

        res = requests.get(
            f"{WEATHER_BASE_URL}/weather",
            params={
                "lat": data.latitude,
                "lon": data.longitude,
                "appid": WEATHER_API_KEY,
                "units": "metric"
            },
            timeout=5
        )

        if res.status_code != 200:
            return success({"weather": {}, "error": "Weather API failed"})

        d = res.json()

        weather = {
            "city": d.get("name", "Unknown"),
            "temperature": d.get("main", {}).get("temp", 25),
            "humidity": d.get("main", {}).get("humidity", 60),
            "rainfall": d.get("rain", {}).get("1h", 0.0),
            "condition": d.get("weather", [{}])[0].get("description", "clear sky")
        }

        return success({"weather": weather})

    except Exception as e:
        print("❌ WEATHER ERROR:", e)
        return success({"weather": {}})

# ---------------- CHAT ----------------
@app.post("/chat-ai")
def chat_ai(data: ChatInput):
    try:
        return success({
            "reply": f"You said: {data.message}"
        })
    except Exception as e:
        print("❌ CHAT ERROR:", e)
        return success({"reply": "Error processing request"})