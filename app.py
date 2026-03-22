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

# ---------------- DEBUG PORT ----------------
print("PORT:", os.environ.get("PORT"))

# ---------------- CONFIG ----------------
class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

    BASE_DIR = os.path.dirname(__file__)
    MODEL_PATH = os.path.join(BASE_DIR, "model/microbial_model.pkl")

config = Config()

# ---------------- LOAD MODEL (SAFE) ----------------
model = None
try:
    if os.path.exists(config.MODEL_PATH):
        model = joblib.load(config.MODEL_PATH)
        print("✅ Model loaded successfully")
    else:
        print("⚠️ Model file not found at:", config.MODEL_PATH)
except Exception as e:
    print("❌ Model loading failed:", e)

# ---------------- INIT GROQ ----------------
groq_client = None
try:
    if config.GROQ_API_KEY:
        groq_client = Groq(api_key=config.GROQ_API_KEY)
        print("✅ Groq AI ready")
    else:
        print("⚠️ Groq not configured")
except Exception as e:
    print("⚠️ Groq init failed:", e)

# ---------------- SESSION ----------------
session_data = {}

# ---------------- REGISTER ROUTES ----------------
register_routes(app, model, groq_client, config, session_data)

# ---------------- HEALTH CHECK ----------------
@app.route("/", methods=["GET"])
def home():
    return {
        "status": "running",
        "message": "AgriTech API is live 🚀"
    }

# ---------------- RUN (IMPORTANT FOR RENDER) ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)