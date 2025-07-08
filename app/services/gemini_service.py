import google.generativeai as genai
import shelve
from dotenv import load_dotenv
import os
import logging
from PIL import Image
import base64
import io

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-pro-vision")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


def get_gemini_model(use_vision=False):
    """Get the configured Gemini model"""
    # Gemini 1.5 Flash can handle both text and images
    model_name = GEMINI_MODEL
    return genai.GenerativeModel(model_name)


def process_image_for_gemini(image_path):
    """Process image for Gemini analysis"""
    try:
        # Open and process the image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    except Exception as e:
        logging.error(f"Error processing image for Gemini: {str(e)}")
        return None


def get_gemini_model():
    """Get the configured Gemini model"""
    return genai.GenerativeModel(GEMINI_MODEL)


# Use context manager to ensure the shelf file is closed properly
def check_if_conversation_exists(wa_id):
    """Check if a conversation history exists for the given WhatsApp ID"""
    with shelve.open("conversations_db") as conversations_shelf:
        return conversations_shelf.get(wa_id, None)


def store_conversation(wa_id, conversation_history):
    """Store conversation history for the given WhatsApp ID"""
    with shelve.open("conversations_db", writeback=True) as conversations_shelf:
        conversations_shelf[wa_id] = conversation_history


def get_conversation_history(wa_id):
    """Retrieve conversation history for the given WhatsApp ID"""
    with shelve.open("conversations_db") as conversations_shelf:
        return conversations_shelf.get(wa_id, [])


def update_conversation_history(wa_id, user_message, bot_response):
    """Update conversation history with new message and response"""
    conversation_history = get_conversation_history(wa_id)
    
    # Add user message
    conversation_history.append({
        "role": "user",
        "parts": [user_message]
    })
    
    # Add bot response
    conversation_history.append({
        "role": "model",
        "parts": [bot_response]
    })
    
    # Keep only last 10 exchanges to manage memory
    if len(conversation_history) > 20:  # 10 user + 10 bot messages
        conversation_history = conversation_history[-20:]
    
    store_conversation(wa_id, conversation_history)


def generate_response(message_body, wa_id, name):
    """Generate response using Gemini with conversation history"""
    try:
        model = get_gemini_model()
        
        # Get conversation history
        conversation_history = get_conversation_history(wa_id)
        
        # System prompt for WhatsApp assistant
        system_prompt = f"""You are a helpful WhatsApp assistant. 
        You're chatting with {name}. 
        Keep your responses concise and friendly since this is WhatsApp.
        If you don't know something, be honest about it.
        Use emojis appropriately to make conversations more engaging."""
        
        # If no conversation history, start with system prompt
        if not conversation_history:
            conversation_history = [{
                "role": "user",
                "parts": [system_prompt]
            }, {
                "role": "model", 
                "parts": ["Hello! I'm your WhatsApp assistant. How can I help you today? 😊"]
            }]
        
        # Add current message to conversation
        conversation_history.append({
            "role": "user",
            "parts": [message_body]
        })
        
        # Start chat with history
        chat = model.start_chat(history=conversation_history[:-1])  # Exclude the last user message
        
        # Generate response
        response = chat.send_message(message_body)
        bot_response = response.text
        
        # Update conversation history
        update_conversation_history(wa_id, message_body, bot_response)
        
        logging.info(f"Generated Gemini response for {name}: {bot_response}")
        return bot_response
        
    except Exception as e:
        logging.error(f"Error generating Gemini response: {str(e)}")
        return "Sorry, I'm having trouble responding right now. Please try again later."


def generate_response_with_context(message_body, wa_id, name, context_file=None):
    """Generate response using Gemini with optional file context"""
    try:
        model = get_gemini_model()
        
        # Get conversation history
        conversation_history = get_conversation_history(wa_id)
        
        # Enhanced system prompt with context
        system_prompt = f"""You are a helpful WhatsApp assistant chatting with {name}.
        Keep responses concise and friendly for WhatsApp.
        Use emojis appropriately to make conversations engaging."""
        
        # If context file is provided, add it to the prompt
        if context_file and os.path.exists(context_file):
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                system_prompt += f"\n\nContext from uploaded file:\n{file_content[:2000]}..."  # Limit context
            except Exception as e:
                logging.warning(f"Could not read context file: {str(e)}")
        
        # If no conversation history, start with system prompt
        if not conversation_history:
            conversation_history = [{
                "role": "user",
                "parts": [system_prompt]
            }, {
                "role": "model", 
                "parts": ["Hello! I'm your WhatsApp assistant. How can I help you today? 😊"]
            }]
        
        # Add current message to conversation
        conversation_history.append({
            "role": "user",
            "parts": [message_body]
        })
        
        # Start chat with history
        chat = model.start_chat(history=conversation_history[:-1])
        
        # Generate response
        response = chat.send_message(message_body)
        bot_response = response.text
        
        # Update conversation history
        update_conversation_history(wa_id, message_body, bot_response)
        
        logging.info(f"Generated Gemini response with context for {name}: {bot_response}")
        return bot_response
        
    except Exception as e:
        logging.error(f"Error generating Gemini response with context: {str(e)}")
        return "Sorry, I'm having trouble responding right now. Please try again later."


def generate_response_with_image(message_body, wa_id, name, image_path=None):
    """Generate response using Gemini with image analysis"""
    try:
        # Use Gemini 1.5 Flash which handles both text and images
        model = get_gemini_model()
        
        # Get conversation history
        conversation_history = get_conversation_history(wa_id)
        
        # System prompt for image analysis
        if image_path:
            system_prompt = f"""You are a helpful WhatsApp assistant with vision capabilities chatting with {name}.
            You can analyze images and answer questions about them.
            Keep responses concise and friendly for WhatsApp.
            Use emojis appropriately to make conversations engaging.
            When analyzing images, be descriptive and helpful."""
        else:
            system_prompt = f"""You are a helpful WhatsApp assistant chatting with {name}.
            Keep responses concise and friendly for WhatsApp.
            Use emojis appropriately to make conversations engaging."""
        
        # Prepare content for the message
        content_parts = []
        
        # Add text message
        if message_body:
            content_parts.append(message_body)
        
        # Add image if provided
        if image_path and os.path.exists(image_path):
            try:
                image = process_image_for_gemini(image_path)
                if image:
                    content_parts.append(image)
                    logging.info(f"Added image to analysis: {image_path}")
                else:
                    logging.warning(f"Could not process image: {image_path}")
            except Exception as e:
                logging.error(f"Error adding image to content: {str(e)}")
        
        # If no content parts, return error
        if not content_parts:
            return "I couldn't process your message. Please try again."
        
        # For image analysis, we'll use a direct generation instead of chat history
        if image_path:
            response = model.generate_content(content_parts)
            bot_response = response.text
        else:
            # Use regular chat for text-only messages
            if not conversation_history:
                conversation_history = [{
                    "role": "user",
                    "parts": [system_prompt]
                }, {
                    "role": "model", 
                    "parts": ["Hello! I'm your WhatsApp assistant. How can I help you today? 😊"]
                }]
            
            conversation_history.append({
                "role": "user",
                "parts": [message_body]
            })
            
            chat = model.start_chat(history=conversation_history[:-1])
            response = chat.send_message(message_body)
            bot_response = response.text
        
        # Update conversation history
        update_conversation_history(wa_id, message_body, bot_response)
        
        logging.info(f"Generated Gemini response for {name}: {bot_response}")
        return bot_response
        
    except Exception as e:
        logging.error(f"Error generating Gemini response with image: {str(e)}")
        return "Sorry, I'm having trouble analyzing the image or responding right now. Please try again later."


def clear_conversation_history(wa_id):
    """Clear conversation history for a specific user"""
    with shelve.open("conversations_db", writeback=True) as conversations_shelf:
        if wa_id in conversations_shelf:
            del conversations_shelf[wa_id]
            logging.info(f"Cleared conversation history for {wa_id}")
