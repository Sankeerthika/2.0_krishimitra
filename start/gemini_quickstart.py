import google.generativeai as genai
import shelve
from dotenv import load_dotenv
import os
import time

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


# --------------------------------------------------------------
# Simple Gemini chat
# --------------------------------------------------------------
def simple_gemini_chat():
    """Simple example of using Gemini for text generation"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = "Hello! Can you tell me about WhatsApp bots?"
        response = model.generate_content(prompt)
        
        print("Prompt:", prompt)
        print("Response:", response.text)
        return response.text
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Test simple chat
print("=== Simple Gemini Chat ===")
simple_gemini_chat()


# --------------------------------------------------------------
# Conversation with history
# --------------------------------------------------------------
def gemini_conversation():
    """Example of maintaining conversation history with Gemini"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Start a chat
        chat = model.start_chat(history=[])
        
        # Send messages
        messages = [
            "Hello! I'm building a WhatsApp bot.",
            "Can you help me understand how to make it more engaging?",
            "What kind of features should I add?"
        ]
        
        for message in messages:
            print(f"\nUser: {message}")
            response = chat.send_message(message)
            print(f"Gemini: {response.text}")
            
        return chat
        
    except Exception as e:
        print(f"Error in conversation: {str(e)}")
        return None


# Test conversation
print("\n=== Gemini Conversation ===")
gemini_conversation()


# --------------------------------------------------------------
# WhatsApp-style conversation simulation
# --------------------------------------------------------------
def simulate_whatsapp_conversation():
    """Simulate a WhatsApp bot conversation"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # System prompt for WhatsApp assistant
        system_prompt = """You are a helpful WhatsApp assistant. 
        Keep your responses concise and friendly since this is WhatsApp.
        Use emojis appropriately to make conversations more engaging.
        If you don't know something, be honest about it."""
        
        # Start chat with system prompt
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["Hello! I'm your WhatsApp assistant. How can I help you today? 😊"]}
        ])
        
        # Simulate user messages
        user_messages = [
            "Hi there!",
            "What's the weather like?",
            "Can you help me with Python programming?",
            "Thanks for your help!"
        ]
        
        print("\n=== WhatsApp Bot Simulation ===")
        print("Bot: Hello! I'm your WhatsApp assistant. How can I help you today? 😊")
        
        for message in user_messages:
            print(f"\nUser: {message}")
            response = chat.send_message(message)
            print(f"Bot: {response.text}")
            
    except Exception as e:
        print(f"Error in WhatsApp simulation: {str(e)}")


# Test WhatsApp simulation
simulate_whatsapp_conversation()


# --------------------------------------------------------------
# Persistent conversation with shelve
# --------------------------------------------------------------
def test_persistent_conversation():
    """Test persistent conversation storage"""
    try:
        user_id = "test_user_123"
        
        # Simulate conversation storage
        def store_conversation(user_id, history):
            with shelve.open("test_conversations_db", writeback=True) as shelf:
                shelf[user_id] = history
        
        def get_conversation(user_id):
            with shelve.open("test_conversations_db") as shelf:
                return shelf.get(user_id, [])
        
        # Get existing conversation or start new
        conversation_history = get_conversation(user_id)
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        if not conversation_history:
            conversation_history = [
                {"role": "user", "parts": ["You are a helpful WhatsApp assistant."]},
                {"role": "model", "parts": ["Hello! How can I help you today? 😊"]}
            ]
        
        # Start chat with history
        chat = model.start_chat(history=conversation_history)
        
        # Test message
        test_message = "Remember our conversation? What did we talk about?"
        print(f"\n=== Persistent Conversation Test ===")
        print(f"User: {test_message}")
        
        response = chat.send_message(test_message)
        print(f"Bot: {response.text}")
        
        # Update conversation history
        conversation_history.append({"role": "user", "parts": [test_message]})
        conversation_history.append({"role": "model", "parts": [response.text]})
        
        # Store updated conversation
        store_conversation(user_id, conversation_history)
        
        print("Conversation saved!")
        
    except Exception as e:
        print(f"Error in persistent conversation: {str(e)}")


# Test persistent conversation
test_persistent_conversation()

print("\n=== Gemini Quickstart Complete ===")
print("You can now use Gemini in your WhatsApp bot!")
print("Make sure to set your GEMINI_API_KEY in the .env file")
