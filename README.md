# WhatsApp AI Chatbot 🤖

A Flask-based WhatsApp chatbot that integrates with Google's Gemini AI to provide intelligent responses to user messages. The bot maintains conversation history and provides contextual responses.

## Features ✨

- **AI-Powered Responses**: Uses Google's Gemini AI for intelligent conversation
- **Speech-to-Text**: Audio message processing with automatic format conversion
- **Vision Support**: Image analysis using Gemini Vision models
- **Conversation Memory**: Maintains chat history for contextual responses
- **WhatsApp Integration**: Seamless integration with WhatsApp Business API
- **Secure Webhooks**: Signature verification for secure communication
- **Multiple AI Options**: Support for both Gemini and OpenAI (configurable)
- **Message Processing**: Handles text formatting for WhatsApp compatibility
- **Debug Tools**: Built-in troubleshooting utilities for API testing

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
│   │   ├── openai_service.py    # OpenAI integration
│   │   └── speech_service.py    # Speech-to-text processing
│   └── utils/
│       └── whatsapp_utils.py    # WhatsApp utilities
├── start/                       # Quickstart examples
├── data/                        # Data storage
├── debug_whatsapp.py            # API troubleshooting tool
├── run.py                       # Application entry point
├── requirements.txt             # Dependencies
├── .env.sample                  # Environment template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Setup Instructions 🚀

### Prerequisites

- Python 3.7+
- WhatsApp Business API account
- Google Gemini API key (or OpenAI API key)
- ngrok (for local development)
- ffmpeg (for audio processing) - [Download here](https://ffmpeg.org/download.html)

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
   Copy the sample environment file and configure it:
   ```bash
   cp .env.sample .env
   ```
   
   Edit the `.env` file with your credentials:
   ```env
   # WhatsApp Business API
   ACCESS_TOKEN=your_whatsapp_access_token
   PHONE_NUMBER_ID=your_phone_number_id
   VERIFY_TOKEN=your_verify_token
   VERSION=v18.0
   
   # AI Configuration
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-pro
   GEMINI_VISION_MODEL=gemini-pro-vision
   
   # Optional: OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_ASSISTANT_ID=your_assistant_id
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Test your setup**
   Use the debugging tool to verify your WhatsApp API configuration:
   ```bash
   python debug_whatsapp.py
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
4. For image processing, set `GEMINI_VISION_MODEL` (default: `gemini-pro-vision`)

### OpenAI (Alternative)
To use OpenAI instead:

1. Uncomment the OpenAI import in `whatsapp_utils.py`
2. Comment out the Gemini import
3. Set up OpenAI credentials in `.env`

### Speech-to-Text Configuration
The bot supports audio message processing with automatic format conversion:

1. **Google Cloud Speech** (recommended for best quality):
   - Enable Google Cloud Speech-to-Text API
   - Set up service account credentials
   - Supports OGG, WAV, FLAC formats directly

2. **SpeechRecognition** (free tier fallback):
   - Uses Google's free speech recognition service
   - Automatically converts audio formats using ffmpeg

3. **Audio Format Support**:
   - OGG (WhatsApp's default format)
   - WAV, FLAC, MP3
   - Automatic conversion for unsupported formats

## Debugging & Troubleshooting 🔧

### API Troubleshooting Tool
Use the built-in debugging script to test your WhatsApp API setup:

```bash
python debug_whatsapp.py
```

This tool will:
- ✅ Test API connectivity and permissions
- 🔑 Validate access tokens and scopes
- 📱 Verify phone number configuration
- 📤 Send test messages (optional)
- 🔍 Provide detailed error diagnostics

### Common Issues and Solutions
- **401 Unauthorized**: Token expired or invalid - generate new token
- **Missing scopes**: Ensure token has `whatsapp_business_messaging` permission
- **Audio processing errors**: Install ffmpeg for audio format conversion
- **Rate limiting**: Implement proper request throttling

## Features in Detail 🔍

### Conversation Memory
- Stores conversation history using Python's `shelve` module
- Maintains last 10 message exchanges per user
- Provides context for more natural conversations

### Speech-to-Text Processing
- **Multi-format support**: OGG (WhatsApp), WAV, FLAC, MP3
- **Automatic conversion**: Uses ffmpeg for format compatibility
- **Dual service support**: Google Cloud Speech (premium) and SpeechRecognition (free)
- **Error handling**: Graceful fallbacks and detailed error messages

### Image Analysis
- **Vision AI**: Processes images using Gemini Vision models
- **Context awareness**: Combines image analysis with conversation history
- **Format support**: JPEG, PNG, WebP, and other common formats

### Message Processing
- Converts markdown-style formatting to WhatsApp format
- Removes unwanted characters and brackets
- Handles emoji integration for engaging conversations
- Processes both text and multimedia messages

### Security
- HMAC signature verification for webhook security
- Request timeout handling
- Error logging and graceful error handling
- Environment variable protection for sensitive data

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

Use the debugging tool for comprehensive API testing:
```bash
python debug_whatsapp.py
```

## Deployment 🚀

### Production Considerations
- Use environment variables for all sensitive data
- Enable HTTPS for webhook endpoints
- Configure proper logging and monitoring
- Set up error tracking and alerting
- Use a production WSGI server (e.g., Gunicorn)
- Implement rate limiting for API calls
- Set up proper audio file cleanup for speech processing

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
