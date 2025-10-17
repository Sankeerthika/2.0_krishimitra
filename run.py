import logging
import os
from dotenv import load_dotenv
from app import create_app

# ==========================================
# 🔹 Load environment variables FIRST
# ==========================================
# Ensures .env values (Gemini, Twilio, Flask secrets) are loaded before app init
load_dotenv()

# ==========================================
# 🔹 Create Flask app
# ==========================================
app = create_app()

# ==========================================
# 🔹 Basic test route
# ==========================================
@app.route("/")
def index():
    return "🌾 KisanAI WhatsApp Bot Server is running successfully!"

# ==========================================
# 🔹 Debug info — check env variables loaded correctly
# ==========================================
print("VERIFY_TOKEN from config:", app.config.get("VERIFY_TOKEN"))
print("TWILIO_ACCOUNT_SID from config:", app.config.get("TWILIO_ACCOUNT_SID"))
print("TWILIO_PHONE_NUMBER from config:", app.config.get("TWILIO_PHONE_NUMBER"))

# Check for both keys (since Gemini SDK accepts GOOGLE_API_KEY)
gemini_key_present = bool(os.getenv("GEMINI_API_KEY")) or bool(os.getenv("GOOGLE_API_KEY"))
print("GEMINI_API_KEY or GOOGLE_API_KEY loaded:", gemini_key_present)

# ==========================================
# 🔹 Run Flask server
# ==========================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("🚀 Starting Flask server on port 8000...")
    
    # Explicitly print a helpful reminder
    if not gemini_key_present:
        logging.warning("⚠️ Gemini API key not found! Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file.")
    if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
        logging.warning("⚠️ Twilio credentials missing. Please verify your .env file.")

    # Run the Flask app
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
