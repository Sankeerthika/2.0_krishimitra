from flask import Blueprint, request
from twilio.rest import Client
from googletrans import Translator
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
import tempfile
import speech_recognition as sr
from pydub import AudioSegment

# -----------------------------
# 🔹 Load environment variables
# -----------------------------
load_dotenv()

# -----------------------------
# 🔹 Create Flask Blueprint
# -----------------------------
webhook_blueprint = Blueprint("webhook", __name__)

# -----------------------------
# 🔹 Configure Gemini API
# -----------------------------
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ No Gemini API key found. Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file.")

genai.configure(api_key=api_key)

# Initialize Translator
translator = Translator()


@webhook_blueprint.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Step 1: Receive incoming WhatsApp message (text or voice)
        from_number = request.form.get("From")
        message_body = request.form.get("Body")

        # If no text, attempt to handle voice media
        if not message_body:
            try:
                num_media = int(request.form.get("NumMedia", "0") or 0)
            except ValueError:
                num_media = 0

            if num_media > 0:
                media_url = request.form.get("MediaUrl0")
                media_type = request.form.get("MediaContentType0", "")

                if media_url and (media_type.startswith("audio/") or media_type in ("video/ogg", "application/ogg")):
                    # Securely download media using Twilio auth
                    sid = os.getenv("TWILIO_ACCOUNT_SID")
                    token = os.getenv("TWILIO_AUTH_TOKEN")

                    ext_map = {
                        "audio/ogg": ".ogg",
                        "application/ogg": ".ogg",
                        "video/ogg": ".ogg",
                        "audio/mpeg": ".mp3",
                        "audio/mp3": ".mp3",
                        "audio/3gpp": ".3gp",
                        "audio/3gpp2": ".3g2",
                        "audio/wav": ".wav",
                        "audio/x-wav": ".wav",
                        "audio/webm": ".webm",
                        "audio/opus": ".ogg",
                    }
                    src_ext = ext_map.get(media_type, ".bin")

                    with tempfile.TemporaryDirectory() as tmpdir:
                        src_path = os.path.join(tmpdir, f"voice{src_ext}")
                        wav_path = os.path.join(tmpdir, "voice.wav")

                        resp = requests.get(media_url, auth=(sid, token), timeout=30)
                        resp.raise_for_status()
                        with open(src_path, "wb") as f:
                            f.write(resp.content)

                        # Convert to WAV via pydub/ffmpeg with proper cleanup
                        try:
                            audio_seg = AudioSegment.from_file(src_path)
                            # Use unique filename to avoid Windows file locking
                            wav_path = os.path.join(tmpdir, f"voice_{os.getpid()}.wav")
                            audio_seg.export(wav_path, format="wav")
                            
                            # Ensure file is closed before transcription
                            del audio_seg
                            
                            # Transcribe using SpeechRecognition
                            recognizer = sr.Recognizer()
                            with sr.AudioFile(wav_path) as source:
                                audio_data = recognizer.record(source)
                            try:
                                message_body = recognizer.recognize_google(audio_data)
                            except Exception as transcribe_err:
                                print(f"❌ Transcription failed: {transcribe_err}")
                                message_body = None
                        except Exception as audio_err:
                            print(f"❌ Audio processing failed: {audio_err}")
                            message_body = None

        if not message_body:
            return "No message received", 400

        # Step 2: Detect language & translate to English if needed
        try:
            detected_lang = translator.detect(message_body).lang
        except Exception:
            detected_lang = "en"

        try:
            translated_text = (
                translator.translate(message_body, src=detected_lang, dest="en").text
                if detected_lang != "en"
                else message_body
            )
        except Exception:
            translated_text = message_body

        # Step 3: Generate Gemini response using current SDK
        prompt = (
            f"Farmer asked: {translated_text}\n\n"
            f"Give a short, clear, and practical agricultural advisory answer. "
            f"Keep it accurate, friendly, and easy to understand."
        )

        # Try available models that support generateContent, preferring flash/pro latest
        result = None
        last_error = None
        try:
            available_models = [
                m.name for m in genai.list_models()
                if "supported_generation_methods" in dir(m)
                and "generateContent" in getattr(m, "supported_generation_methods", [])
            ]
        except Exception:
            available_models = []

        preferred = [
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-flash-002",
            "models/gemini-1.5-pro-latest",
            "models/gemini-1.5-pro-002",
            "models/gemini-1.0-pro",
        ]

        candidates = preferred + [m for m in available_models if m not in preferred]

        for candidate in candidates:
            for variant in (candidate, candidate.replace("models/", "")):
                try:
                    model = genai.GenerativeModel(variant)
                    result = model.generate_content(prompt)
                    if result:
                        break
                except Exception as model_err:
                    last_error = model_err
                    continue
            if result:
                break
        if result is None and last_error:
            raise last_error

        reply_text = (getattr(result, "text", None) or "").strip()
        if not reply_text and hasattr(result, "candidates"):
            for c in (result.candidates or []):
                content = getattr(c, "content", None)
                parts = getattr(content, "parts", []) if content else []
                if parts:
                    part = parts[0]
                    part_text = getattr(part, "text", None)
                    if part_text:
                        reply_text = part_text.strip()
                        break
        if not reply_text:
            reply_text = "I'm sorry, I couldn't process that question."

        # Step 4: Translate back to original language if needed
        if detected_lang != "en":
            reply_text = translator.translate(reply_text, src="en", dest=detected_lang).text

        # Step 5: Send response via Twilio WhatsApp
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        client.messages.create(
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=from_number,
            body=f"🌾 {reply_text}"
        )

        return "OK", 200

    except Exception as e:
        print("❌ Error in webhook:", e)
        try:
            from_number = request.form.get("From")
            client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN")
            )
            client.messages.create(
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=from_number,
                body="⚠️ Sorry! Our Agri assistant faced an issue. Please try again later."
            )
        except Exception as twilio_error:
            print("❌ Twilio send error:", twilio_error)

        return "Internal Server Error", 500

