# WhatsApp AI Chatbot 🤖

A Flask-based WhatsApp chatbot that integrates with Google's Gemini AI to provide intelligent responses to user messages. The bot maintains conversation history and provides contextual responses.

## Features ✨

- **AI-Powered Responses**: Uses Google's Gemini AI for intelligent conversation
- **Conversation Memory**: Maintains chat history for contextual responses
- **WhatsApp Integration**: Seamless integration with WhatsApp Business API
- **Secure Webhooks**: Signature verification for secure communication
- **Multiple AI Options**: Support for both Gemini and OpenAI (configurable)
- **Message Processing**: Handles text formatting for WhatsApp compatibility

## Project Structure 📁

```
AI/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration management
│   ├── views.py                 # Webhook endpoints
│   ├── decorators/
│   │   └── security.py          # Security decorators
│   ├── services/
│   │   ├── gemini_service.py    # Gemini AI integration
│   │   └── openai_service.py    # OpenAI integration
│   └── utils/
│       └── whatsapp_utils.py    # WhatsApp utilities
├── start/                       # Quickstart examples
├── data/                        # Data storage
├── run.py                       # Application entry point
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Setup Instructions 🚀

### Prerequisites

- Python 3.7+
- WhatsApp Business API account
- Google Gemini API key (or OpenAI API key)
- ngrok (for local development)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mandarwagh9/whatsapp-ai.git
   cd whatsapp-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   # WhatsApp Business API
   ACCESS_TOKEN=your_whatsapp_access_token
   YOUR_PHONE_NUMBER=your_phone_number
   APP_ID=your_app_id
   APP_SECRET=your_app_secret
   RECIPIENT_WAID=recipient_whatsapp_id
   VERSION=v18.0
   PHONE_NUMBER_ID=your_phone_number_id
   VERIFY_TOKEN=your_verify_token
   
   # AI Configuration
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-pro
   
   # Optional: OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_ASSISTANT_ID=your_assistant_id
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

## WhatsApp Business API Setup 📱

### 1. Create a Meta Developer Account
- Go to [Meta for Developers](https://developers.facebook.com/)
- Create a new app for WhatsApp Business

### 2. Configure Webhook
- Set webhook URL: `https://your-domain.com/webhook`
- Set verify token (same as in your `.env` file)
- Subscribe to `messages` webhook field

### 3. Get Required Tokens
- **Access Token**: From WhatsApp Business API settings
- **Phone Number ID**: From WhatsApp Business API settings
- **App Secret**: From App Settings > Basic

## AI Service Configuration 🧠

### Gemini AI (Default)
The bot uses Google's Gemini AI by default. To use it:

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add `GEMINI_API_KEY` to your `.env` file
3. Optionally set `GEMINI_MODEL` (default: `gemini-pro`)

### OpenAI (Alternative)
To use OpenAI instead:

1. Uncomment the OpenAI import in `whatsapp_utils.py`
2. Comment out the Gemini import
3. Set up OpenAI credentials in `.env`

## Features in Detail 🔍

### Conversation Memory
- Stores conversation history using Python's `shelve` module
- Maintains last 10 message exchanges per user
- Provides context for more natural conversations

### Message Processing
- Converts markdown-style formatting to WhatsApp format
- Removes unwanted characters and brackets
- Handles emoji integration for engaging conversations

### Security
- HMAC signature verification for webhook security
- Request timeout handling
- Error logging and graceful error handling

## API Endpoints 🔗

### `GET /webhook`
Webhook verification endpoint for WhatsApp Business API

### `POST /webhook`
Receives incoming WhatsApp messages and processes them

## Development 💻

### Local Development with ngrok
```bash
# Install ngrok
# Run your Flask app
python run.py

# In another terminal, expose local server
ngrok http 8000

# Use the ngrok URL as your webhook URL in Meta Developer Console
```

### Testing
The bot includes quickstart examples in the `start/` directory:
- `gemini_quickstart.py` - Test Gemini integration
- `whatsapp_quickstart.py` - Test WhatsApp API
- `assistants_quickstart.py` - Test OpenAI Assistant

## Deployment 🚀

### Production Considerations
- Use environment variables for all sensitive data
- Enable HTTPS for webhook endpoints
- Configure proper logging
- Set up monitoring and error tracking
- Use a production WSGI server (e.g., Gunicorn)

### Example Deployment Commands
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app

# Using Docker (create Dockerfile)
docker build -t whatsapp-ai .
docker run -p 8000:8000 whatsapp-ai
```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For questions and support:
- Create an issue on GitHub
- Check the [WhatsApp Business API documentation](https://developers.facebook.com/docs/whatsapp)
- Review [Google Gemini AI documentation](https://ai.google.dev/docs)

## Acknowledgments 🙏

- Google for the Gemini AI API
- Meta for the WhatsApp Business API
- Flask community for the excellent framework
- OpenAI for alternative AI integration options

---

**Note**: This bot is designed for educational and development purposes. Make sure to comply with WhatsApp's terms of service and your local regulations when deploying to production.
