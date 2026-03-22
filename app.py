from flask import Flask
from flask_cors import CORS
import os
import joblib
import logging

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.DEBUG)

# Safe Groq import
try:
    from groq import Groq
except:
    Groq = None

# Import routes
from api import register_routes

print("🚀 STARTING AGRITECH API")

# ---------------- APP INIT ----------------
app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True
CORS(app)

print("PORT:", os.environ.get("PORT"))

# ---------------- CONFIG ----------------
class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

    BASE_DIR = os.path.dirname(__file__)
    MODEL_PATH = os.path.join(BASE_DIR, "model/microbial_model.pkl")

config = Config()

# ---------------- DEBUG FILES ----------------
try:
    print("📂 FILES:", os.listdir(config.BASE_DIR))
except Exception as e:
    print("FILE LIST ERROR:", e)

# ---------------- LOAD MODEL ----------------
model = None
try:
    if os.path.exists(config.MODEL_PATH):
        model = joblib.load(config.MODEL_PATH)
        print("✅ Model loaded")
    else:
        print("⚠️ Model not found:", config.MODEL_PATH)
except Exception as e:
    print("❌ Model error:", e)

# ---------------- GROQ ----------------
groq_client = None
try:
    if config.GROQ_API_KEY and Groq:
        groq_client = Groq(api_key=config.GROQ_API_KEY)
        print("✅ Groq ready")
    else:
        print("⚠️ Groq not configured")
except Exception as e:
    print("❌ Groq error:", e)

# ---------------- SESSION ----------------
session_data = {}

# ---------------- REGISTER ROUTES ----------------
register_routes(app, model, groq_client, config, session_data)

print("🔥 APP INITIALIZED SUCCESSFULLY")

# ---------------- ROOT ----------------
@app.route("/")
def home():
    return {
        "status": "running",
        "message": "AgriTech API is live 🚀"
    }

# ---------------- TEST ROUTE ----------------
@app.route("/test")
def test():
    return "Test route working 🚀"

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)