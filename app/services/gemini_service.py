"""
Enhanced Gemini AI Service with translation support and response validation

This is the main AI service that integrates with Google's Gemini models
to provide intelligent responses to farmers' queries.
"""

import google.generativeai as genai
import os
import logging
import time
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path

# Import our own services
from .translation_service import translation_service
from .knowledge_base_service import knowledge_base
from .conversation_service import conversation_service
from .response_validator import response_validator
from .prompt_manager import prompt_manager

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logging.warning("GEMINI_API_KEY not found in environment variables")

# Get models from environment with defaults
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL")

# Set up logging
logger = logging.getLogger(__name__)


def validate_response_quality(response_text):
    """
    Validate that the response is not corrupted or garbled
    Returns True if response is good, False if corrupted
    """
    if not response_text or len(response_text.strip()) < 10:
        return False
    
    # Check for excessive repetitions
    words = response_text.split()
    if len(words) < 5:
        return True  # Short responses are probably okay
    
    # Count repetitive patterns
    word_counts = {}
    for word in words:
        word_lower = word.lower()
        word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
    
    # If any word appears more than 20% of the time, it's likely corrupted
    max_word_frequency = max(word_counts.values()) / len(words)
    if max_word_frequency > 0.2:
        logger.warning(f"Response rejected: excessive repetition (max freq: {max_word_frequency:.2f})")
        return False
    
    # Check for script mixing corruption (enhanced patterns)
    # Pattern 1: English letters mixed with Devanagari in unnatural ways
    if re.search(r'[a-zA-Z][क-ह्][a-zA-Z]|[क-ह्][a-zA-Z][क-ह्]', response_text):
        logger.warning("Response rejected: corrupted script mixing detected (pattern 1)")
        return False
    
    # Pattern 2: Single English letters inserted randomly in Hindi words
    if re.search(r'[क-ह्][a-zA-Z][क-ह्]|[क-ह्][a-zA-Z]{1,2}[क-ह्]', response_text):
        logger.warning("Response rejected: corrupted script mixing detected (pattern 2)")
        return False
    
    # Pattern 3: Mixed script within words (like "aखीrरे")
    if re.search(r'\b[a-zA-Z]*[क-ह्]+[a-zA-Z]+[क-ह्]*\b|\b[क-ह्]*[a-zA-Z]+[क-ह्]+[a-zA-Z]*\b', response_text):
        logger.warning("Response rejected: corrupted script mixing detected (pattern 3)")
        return False
    
    # Check for excessive uppercase mixing (like "KANTA मंडी KANTA")
    if re.search(r'[A-Z]{3,}.*[क-ह्].*[A-Z]{3,}', response_text):
        logger.warning("Response rejected: excessive uppercase/script mixing detected")
        return False
    
    # Check for excessive punctuation or symbols
    symbol_count = len(re.findall(r'[^\w\s\u0900-\u097F।,!?.\-()]', response_text))
    if symbol_count > len(response_text) * 0.08:  # More than 8% symbols
        logger.warning("Response rejected: excessive symbols detected")
        return False
    
    # Check for corrupted word patterns
    corrupted_words = 0
    for word in words:
        # Count words that look like corruption (random letters)
        if len(word) > 4 and re.search(r'^[a-z]+$', word):
            vowel_count = len(re.findall(r'[aeiou]', word.lower()))
            vowel_ratio = vowel_count / len(word)
            if vowel_ratio < 0.15 or vowel_ratio > 0.7:  # Too few or too many vowels
                corrupted_words += 1
    
    # If more than 30% of words look corrupted, reject
    if corrupted_words > len(words) * 0.3:
        logger.warning(f"Response rejected: too many corrupted words ({corrupted_words}/{len(words)})")
        return False
    
    # Check for excessive consecutive repetition of same word/phrase
    if re.search(r'\b(\w+)(\s+\1){4,}\b', response_text):
        logger.warning("Response rejected: excessive consecutive word repetition detected")
        return False
    
    # Check for extremely fragmented text (too many very short words)
    short_words = sum(1 for word in words if len(word) <= 2)
    if short_words > len(words) * 0.7:  # More than 70% very short words
        logger.warning("Response rejected: text appears too fragmented")
        return False
    
    return True


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


def load_custom_dataset():
    """Load custom knowledge base for Project Kisan"""
    knowledge_base = {}
    
    try:
        # Load main knowledge base
        if os.path.exists(DATASET_PATH):
            with open(DATASET_PATH, 'r', encoding='utf-8') as f:
                knowledge_base['general'] = json.load(f)
        
        # Load crop diseases data
        if os.path.exists(CROP_DISEASES_PATH):
            with open(CROP_DISEASES_PATH, 'r', encoding='utf-8') as f:
                knowledge_base['diseases'] = json.load(f)
        
        # Load market data
        if os.path.exists(MARKET_DATA_PATH):
            with open(MARKET_DATA_PATH, 'r', encoding='utf-8') as f:
                knowledge_base['market'] = json.load(f)
        
        # Load government schemes
        if os.path.exists(SCHEMES_DATA_PATH):
            with open(SCHEMES_DATA_PATH, 'r', encoding='utf-8') as f:
                knowledge_base['schemes'] = json.load(f)
                
        logger.info("Custom dataset loaded successfully")
        return knowledge_base
        
    except Exception as e:
        logger.error(f"Error loading custom dataset: {e}")
        return {}


def generate_kisan_response(message_body, wa_id, farmer_name):
    """Generate Project Kisan response with multi-language support"""
    try:
        # Step 1: Detect language and translate message to English for processing
        translation_result = translation_service.translate_message(message_body)
        english_message = translation_result['english_text']
        detected_language = translation_result['detected_language']
        
        logger.info(f"Processing message from {farmer_name}: '{message_body[:50]}...' (detected: {detected_language})")
        logger.info(f"Translated to English: '{english_message[:50]}...'")
        
        # Handle simple greeting by unified English template and translate
        if english_message.strip().lower() == 'hello':
            english_greeting = f"Hello {farmer_name}! 🙏\nI am Project Kisan, your WhatsApp farming assistant. I can help you with market prices, crop advice, and more. How can I assist you today?"
            final_response = translation_service.translate_response(english_greeting, detected_language)
            # Save greeting in history
            history = get_conversation_history(wa_id)
            history.append({'role': 'user', 'parts': [message_body]})
            history.append({'role': 'model', 'parts': [final_response]})
            save_conversation_history(wa_id, history)
            return final_response
        
        # Custom cucumber price query for Pune
        if 'cucumber' in english_message.lower() and 'pune' in english_message.lower():
            try:
                with open(MARKET_DATA_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                records = data.get('records', [])
                prices = [rec.get('modal_price') for rec in records
                          if rec.get('commodity','').strip().lower() == 'cucumber'
                          and rec.get('market','').strip().lower() == 'pune']
                if prices:
                    latest_price = prices[-1]
                    response_text = f"The latest modal price of cucumbers in Pune is ₹{latest_price} per quintal as of {data.get('updated_date')}."
                else:
                    response_text = "Sorry, I couldn't find the latest cucumber price for Pune in my dataset."
            except Exception as e:
                logger.error(f"Error fetching cucumber price: {e}")
                response_text = "Sorry, I couldn't retrieve the cucumber price right now."
            final_response = response_text if detected_language == 'en' else translation_service.translate_response(response_text, detected_language)
            history = get_conversation_history(wa_id)
            history.append({'role': 'user', 'parts': [message_body]})
            history.append({'role': 'model', 'parts': [final_response]})
            save_conversation_history(wa_id, history)
            return final_response
        # Proceed with normal Kisan logic
        knowledge_base = load_custom_dataset()
        
        # Get conversation history
        history = get_conversation_history(wa_id)
        
        # Create enhanced system prompt
        system_prompt = f"""You are Project Kisan, an AI assistant specifically designed to help Indian farmers. You have access to comprehensive farming knowledge, market prices, crop information, and government schemes.

Core principles:
- Provide accurate, practical farming advice
- Include specific market prices when available
- Mention relevant government schemes when applicable
- Be concise but thorough
- Always respond in a helpful, respectful manner

Context: You are helping farmer {farmer_name} with their query.

Available Knowledge Base:
{json.dumps(knowledge_base, ensure_ascii=False, indent=2)[:3000]}

Query from farmer: {english_message}

Please provide a helpful response in English. Focus on practical farming advice, market information, or relevant agricultural guidance."""
        
        # Clean history to remove any system prompts
        clean_history = []
        if history:
            for msg in history:
                # Only keep messages that look like normal conversation
                msg_text = str(msg["parts"][0]).lower()
                if not any(word in msg_text for word in ["you are project kisan", "context:", "instructions:", "core principles"]):
                    clean_history.append(msg)
        
        # Start chat with clean history
        model = genai.GenerativeModel(GEMINI_MODEL)
        if clean_history:
            chat = model.start_chat(history=clean_history)
            response = chat.send_message(system_prompt)
        else:
            # Fresh conversation
            response = model.generate_content(system_prompt)
        
        # Determine how to handle model response based on its language
        model_response = response.text
        logger.info(f"Generated model response: '{model_response[:100]}...' ")
        # Detect model response language
        try:
            model_resp_lang = translation_service.detect_language(model_response)
        except Exception as e:
            logger.warning(f"Failed to detect model response language: {e}")
            model_resp_lang = 'en'
        # If model responded in user's language, use it directly
        if model_resp_lang == detected_language:
            final_response = model_response
        else:
            # Ensure we have an English version for validation and translation
            if model_resp_lang != 'en':
                english_response = translation_service.translate_to_english(model_response, model_resp_lang)
            else:
                english_response = model_response
            # Validate English response quality
            if not validate_response_quality(english_response):
                logger.warning("English response failed validation or insufficient quality, using fallback")
                english_response = "I can help you with farming questions, market prices, and crop advice. Please let me know what specific information you need."
            # Translate back to user's language
            final_response = translation_service.translate_response(english_response, detected_language)
        logger.info(f"Final response in {detected_language}: '{final_response[:100]}...' ")
        
        # Validate final translated response
        if not validate_response_quality(final_response):
            logger.warning("Translated response failed validation, using fallback")
            # Use a safe fallback response in the detected language
            if detected_language == 'hi':
                final_response = "मैं आपके खेती के सवाल, बाजार के भाव और फसल की सलाह में मदद कर सकता हूं। कृपया बताएं कि आपको क्या जानकारी चाहिए।"
            elif detected_language == 'bn':
                final_response = "আমি আপনার কৃষি প্রশ্ন, বাজার দাম এবং ফসলের পরামর্শে সাহায্য করতে পারি। অনুগ্রহ করে বলুন আপনার কী তথ্য প্রয়োজন।"
            elif detected_language == 'ta':
                final_response = "நான் உங்கள் விவசாய கேள்விகள், சந்தை விலைகள் மற்றும் பயிர் ஆலோசனைகளில் உதவ முடியும். என்ன தகவல் தேவை என்று சொல்லுங்கள்।"
            elif detected_language == 'te':
                final_response = "నేను మీ వ్యవసాయ ప్రశ్నలు, మార్కెట్ ధరలు మరియు పంట సలహాలలో సహాయం చేయగలను. మీకు ఏ సమాచారం కావాలో చెప్పండి।"
            elif detected_language == 'kn':
                final_response = "ನಾನು ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳು, ಮಾರುಕಟ್ಟೆ ಬೆಲೆಗಳು ಮತ್ತು ಬೆಳೆ ಸಲಹೆಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಹುದು. ನಿಮಗೆ ಯಾವ ಮಾಹಿತಿ ಬೇಕು ಎಂದು ತಿಳಿಸಿ।"
            elif detected_language == 'gu':
                final_response = "હું તમારા ખેતીના પ્રશ્નો, બજારના ભાવ અને પાકની સલાહમાં મદદ કરી શકું છું. કૃપા કરીને કહો કે તમને કઈ માહિતી જોઈએ છે।"
            elif detected_language == 'ml':
                final_response = "എനിക്ക് നിങ്ങളുടെ കൃഷി ചോദ്യങ്ങൾ, മാർക്കറ്റ് വിലകൾ, വിള ഉപദേശങ്ങൾ എന്നിവയിൽ സഹായിക്കാം. എന്ത് വിവരമാണ് വേണ്ടതെന്ന് പറയൂ।"
            elif detected_language == 'pa':
                final_response = "ਮੈਂ ਤੁਹਾਡੇ ਖੇਤੀ ਦੇ ਸਵਾਲਾਂ, ਮਾਰਕਿਟ ਦੇ ਭਾਅ ਅਤੇ ਫਸਲ ਦੀ ਸਲਾਹ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਦੱਸੋ ਕਿ ਤੁਹਾਨੂੰ ਕੀ ਜਾਣਕਾਰੀ ਚਾਹੀਦੀ ਹੈ।"
            else:
                final_response = "I can help you with farming questions, market prices, and crop advice. Please let me know what specific information you need."
        
        # Save the new exchange in original language
        clean_history.append({"role": "user", "parts": [message_body]})
        clean_history.append({"role": "model", "parts": [final_response]})
        
        # Keep only last 10 exchanges
        if len(clean_history) > 20:
            clean_history = clean_history[-20:]
            
        save_conversation_history(wa_id, clean_history)
        
        logger.info(f"Generated Kisan response for {farmer_name} in {detected_language}")
        return final_response
        
    except Exception as e:
        logger.error(f"Error generating Kisan response: {e}")
        # Try to return error message in detected language if possible
        try:
            detected_lang = translation_service.detect_language(message_body)
            english_error = "Sorry, I'm having trouble responding right now. Please try again later."
            return translation_service.translate_response(english_error, detected_lang)
        except:
            return "क्षमा करें, मुझे अभी जवाब देने में समस्या हो रही है। कृपया थोड़ी देर बाद कोशिश करें।"
