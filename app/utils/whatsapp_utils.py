import logging
from flask import current_app, jsonify
import json
import requests
import os
import tempfile

# from app.services.openai_service import generate_response_with_image
from app.services.gemini_service import generate_kisan_response, generate_response_with_image, validate_response_quality
from app.services.translation_service import translation_service
from app.services.speech_service import transcribe_audio
import re


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def generate_response_simple(response):
    # Return text in uppercase (simple demo function)
    return response.upper()


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def download_whatsapp_media(media_id, media_type="image"):
    """Download media file from WhatsApp and return the local file path"""
    try:
        # Get media URL from WhatsApp API
        headers = {
            "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
        }
        
        media_url_endpoint = f"https://graph.facebook.com/{current_app.config['VERSION']}/{media_id}"
        
        response = requests.get(media_url_endpoint, headers=headers)
        response.raise_for_status()
        
        media_data = response.json()
        media_url = media_data.get("url")
        
        if not media_url:
            logging.error("No media URL found in response")
            return None
        
        # Download the actual media file
        media_response = requests.get(media_url, headers=headers)
        media_response.raise_for_status()
        
        # Create temporary file to store the media
        temp_dir = tempfile.gettempdir()
        
        # Set appropriate file extension based on media type
        if media_type == "audio":
            file_extension = ".ogg"  # WhatsApp audio is typically OGG
        else:
            file_extension = ".jpg"  # Default to image
            
        temp_file_path = os.path.join(temp_dir, f"whatsapp_media_{media_id}{file_extension}")
        
        with open(temp_file_path, 'wb') as f:
            f.write(media_response.content)
        
        logging.info(f"Downloaded {media_type} file to: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logging.error(f"Error downloading WhatsApp media: {str(e)}")
        return None


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_type = message.get("type", "text")
    
    message_body = ""
    image_path = None
    
    # Handle different message types
    if message_type == "text":
        message_body = message["text"]["body"]
        logging.info(f"Processing text message from {name}: {message_body}")
        
    elif message_type == "image":
        # Get image media ID and caption
        media_id = message["image"]["id"]
        message_body = message["image"].get("caption", "What do you see in this image?")
        
        # Download the image
        image_path = download_whatsapp_media(media_id, "image")
        
        if not image_path:
            response = "Sorry, I couldn't download the image. Please try sending it again."
            data = get_text_message_input(wa_id, response)
            send_message(data)
            return
            
        logging.info(f"Processing image message from {name}: {message_body}")
        
    elif message_type == "audio":
        # Get audio media ID
        media_id = message["audio"]["id"]
        
        # Download the audio file
        audio_path = download_whatsapp_media(media_id, "audio")
        
        if not audio_path:
            response = "Sorry, I couldn't download the audio file. Please try sending it again."
            data = get_text_message_input(wa_id, response)
            send_message(data)
            return
            
        logging.info(f"Processing audio message from {name}")
        
        # Transcribe audio to text
        try:
            transcribed_text = transcribe_audio(audio_path)
            if transcribed_text:
                message_body = transcribed_text
                logging.info(f"Transcribed audio from {name}: {message_body}")
            else:
                response = "Sorry, I couldn't understand the audio. Please try speaking more clearly or send a text message."
                data = get_text_message_input(wa_id, response)
                send_message(data)
                return
                
        except Exception as e:
            logging.error(f"Error transcribing audio: {str(e)}")
            response = "Sorry, I'm having trouble processing your voice message. Please try again or send a text message."
            data = get_text_message_input(wa_id, response)
            send_message(data)
            return
        finally:
            # Clean up temporary audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logging.info(f"Cleaned up temporary audio file: {audio_path}")
                except Exception as e:
                    logging.warning(f"Could not remove temporary audio file {audio_path}: {str(e)}")
                    
    else:
        # Handle unsupported message types
        response = "Sorry, I can only process text, image, and voice messages right now. 📝📸🎤"
        data = get_text_message_input(wa_id, response)
        send_message(data)
        return

    # AI Integration with appropriate response function
    try:
        if image_path:
            # Use image analysis function for images
            response = generate_response_with_image(message_body, wa_id, name, image_path)
        else:
            # Use Kisan response function for text and audio messages
            response = generate_kisan_response(message_body, wa_id, name)
        
        # Clean up temporary image file
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Cleaned up temporary file: {image_path}")
            except Exception as e:
                logging.warning(f"Could not remove temporary file {image_path}: {str(e)}")
        
    except Exception as e:
        logging.error(f"Error generating AI response: {str(e)}")
        response = "Sorry, I'm having trouble processing your message right now. Please try again later."
    
    # Process text for WhatsApp formatting
    response = process_text_for_whatsapp(response)
    
    # Log that we're sending a text-only response
    logging.info(f"Sending text response to {name}: {response[:50]}...")

    data = get_text_message_input(wa_id, response)
    send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
        and (
            body["entry"][0]["changes"][0]["value"]["messages"][0].get("text")
            or body["entry"][0]["changes"][0]["value"]["messages"][0].get("image")
            or body["entry"][0]["changes"][0]["value"]["messages"][0].get("audio")
        )
    )
