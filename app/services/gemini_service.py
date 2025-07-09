"""
Simple Gemini AI Service - Clean and efficient implementation
"""

import google.generativeai as genai
import shelve
import os
import logging
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Get models from environment
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_image(image_path):
    """Process image for Gemini analysis"""
    try:
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return None


def get_conversation_history(wa_id):
    """Get conversation history for a WhatsApp ID"""
    try:
        with shelve.open("conversations_db") as shelf:
            return shelf.get(wa_id, [])
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []


def save_conversation_history(wa_id, history):
    """Save conversation history for a WhatsApp ID"""
    try:
        with shelve.open("conversations_db", writeback=True) as shelf:
            # Keep only last 10 exchanges (20 messages)
            if len(history) > 20:
                history = history[-20:]
            shelf[wa_id] = history
    except Exception as e:
        logger.error(f"Error saving conversation history: {e}")


def generate_response(message_body, wa_id, name):
    """Generate a simple text response"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Get conversation history
        history = get_conversation_history(wa_id)
        
        # Create system prompt
        system_prompt = f"You are a helpful WhatsApp assistant chatting with {name}. Keep responses concise and friendly."
        
        # If no history, start fresh
        if not history:
            history = [
                {"role": "user", "parts": [system_prompt]},
                {"role": "model", "parts": ["Hello! How can I help you today? 😊"]}
            ]
        
        # Start chat with history
        chat = model.start_chat(history=history)
        
        # Generate response
        response = chat.send_message(message_body)
        bot_response = response.text
        
        # Update history
        history.append({"role": "user", "parts": [message_body]})
        history.append({"role": "model", "parts": [bot_response]})
        
        # Save updated history
        save_conversation_history(wa_id, history)
        
        logger.info(f"Generated response for {name}")
        return bot_response
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Sorry, I'm having trouble responding right now. Please try again later."


def generate_response_with_context(message_body, wa_id, name, context_file=None):
    """Generate response with file context"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Get conversation history
        history = get_conversation_history(wa_id)
        
        # Create system prompt with context
        system_prompt = f"You are a helpful WhatsApp assistant chatting with {name}. Keep responses concise and friendly."
        
        # Add file context if provided
        if context_file and os.path.exists(context_file):
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()[:2000]  # Limit context
                system_prompt += f"\n\nContext from file:\n{file_content}"
            except Exception as e:
                logger.warning(f"Could not read context file: {e}")
        
        # If no history, start fresh
        if not history:
            history = [
                {"role": "user", "parts": [system_prompt]},
                {"role": "model", "parts": ["Hello! How can I help you today? 😊"]}
            ]
        
        # Start chat with history
        chat = model.start_chat(history=history)
        
        # Generate response
        response = chat.send_message(message_body)
        bot_response = response.text
        
        # Update history
        history.append({"role": "user", "parts": [message_body]})
        history.append({"role": "model", "parts": [bot_response]})
        
        # Save updated history
        save_conversation_history(wa_id, history)
        
        logger.info(f"Generated response with context for {name}")
        return bot_response
        
    except Exception as e:
        logger.error(f"Error generating response with context: {e}")
        return "Sorry, I'm having trouble responding right now. Please try again later."


def generate_response_with_image(message_body, wa_id, name, image_path=None):
    """Generate response with image analysis"""
    try:
        # Use vision model for images
        model_name = GEMINI_VISION_MODEL if image_path else GEMINI_MODEL
        model = genai.GenerativeModel(model_name)
        
        # Get conversation history
        history = get_conversation_history(wa_id)
        
        # Prepare content
        content_parts = []
        if message_body:
            content_parts.append(message_body)
        
        # Add image if provided
        if image_path and os.path.exists(image_path):
            image = process_image(image_path)
            if image:
                content_parts.append(image)
                logger.info(f"Added image to analysis: {image_path}")
        
        if not content_parts:
            return "I couldn't process your message. Please try again."
        
        # For image analysis, use direct generation
        if image_path:
            response = model.generate_content(content_parts)
            bot_response = response.text
        else:
            # Use chat for text-only
            if not history:
                system_prompt = f"You are a helpful WhatsApp assistant chatting with {name}. Keep responses concise and friendly."
                history = [
                    {"role": "user", "parts": [system_prompt]},
                    {"role": "model", "parts": ["Hello! How can I help you today? 😊"]}
                ]
            
            chat = model.start_chat(history=history)
            response = chat.send_message(message_body)
            bot_response = response.text
        
        # Update history
        history.append({"role": "user", "parts": [message_body]})
        history.append({"role": "model", "parts": [bot_response]})
        
        # Save updated history
        save_conversation_history(wa_id, history)
        
        logger.info(f"Generated response for {name}")
        return bot_response
        
    except Exception as e:
        logger.error(f"Error generating response with image: {e}")
        return "Sorry, I'm having trouble analyzing the image. Please try again later."


def clear_conversation_history(wa_id):
    """Clear conversation history for a user"""
    try:
        with shelve.open("conversations_db", writeback=True) as shelf:
            if wa_id in shelf:
                del shelf[wa_id]
                logger.info(f"Cleared conversation history for {wa_id}")
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")


def check_if_conversation_exists(wa_id):
    """Check if conversation exists for a user"""
    try:
        with shelve.open("conversations_db") as shelf:
            return wa_id in shelf
    except Exception as e:
        logger.error(f"Error checking conversation existence: {e}")
        return False
