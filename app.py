from flask import Flask
from flask_cors import CORS
from groq import Groq
import joblib
import os

from api import register_routes

print("🚀 STARTING AGRITECH API")

# ---------------- APP INIT ----------------
app = Flask(__name__)
CORS(app)

# ---------------- CONFIG ----------------
class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    MODEL_PATH = "model/microbial_model.pkl"

config = Config()

# ---------------- LOAD MODEL ----------------
try:
    model = joblib.load(config.MODEL_PATH)
    print("✅ Model loaded successfully")
except Exception as e:
    print("❌ Model loading failed:", e)
    model = None

# ---------------- INIT GROQ ----------------
try:
    groq_client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None
    print("✅ Groq AI ready" if groq_client else "⚠️ Groq not configured")
except:
    groq_client = None
    print("⚠️ Groq init failed")

# ---------------- SESSION ----------------
session_data = {}

# ---------------- REGISTER ROUTES ----------------
register_routes(app, model, groq_client, config, session_data)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)