# Unsubscribe Email Workflow API

Automated unsubscribe processing system with LLM-based intent detection, built with FastAPI, LangChain, and Brevo integration.

## 🚀 Features

- **Inbound Email Webhook**: Receive emails from Outlook Power Automate
- **Background Email Worker**: Automatically checks mailbox via IMAP every hour
- **Multiple Email Providers**: Support for Outlook, Gmail, Rediff Mail, Yahoo, and custom IMAP servers
- **LLM Intent Detection**: Uses LangChain with Ollama (local) or Gemini (cloud) to detect unsubscribe requests
- **Automatic Unsubscribe**: Integrates with Brevo Contacts API to blacklist/unsubscribe users
- **Dual Processing Modes**: 
  - **Webhook Mode**: Real-time processing via Power Automate
  - **Worker Mode**: Scheduled IMAP polling (every 1 hour)
- **Ngrok Support**: Easily expose local API for webhook integration
- **Multiple LLM Options**: Switch between local Ollama or cloud-based Gemini

## 📋 Prerequisites

- Python 3.9+
- Ollama (if using local LLM)
- Brevo account and API key
- Email account with IMAP access:
  - **Outlook** (personal accounts)
  - **Gmail** (with App Password)
  - **Rediff Mail** (Indian email provider)
  - **Yahoo Mail** (with App Password)
  - **Custom IMAP server**
- ngrok account (for webhook exposure)

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd d:\Projects\Unsuscribe-Email-workflow
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 2. Install Ollama (for local LLM)

Download and install Ollama from [ollama.ai](https://ollama.ai)

```bash
# Pull a model (recommended: llama2, mistral, or llama3)
ollama pull llama2
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
copy .env.example .env
```

Edit `.env`:

```env
# LLM Configuration
LLM_PROVIDER=ollama  # Options: ollama, gemini
OLLAMA_MODEL=llama2  # For local Ollama
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-pro

# Brevo Configuration
BREVO_API_KEY=your_actual_brevo_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8000

# IMAP Configuration (for Background Worker)
IMAP_ENABLED=true  # Set to false to disable worker

# Choose Email Provider: outlook, gmail, rediff, yahoo, custom
IMAP_PROVIDER=outlook

# Your Email Credentials
IMAP_EMAIL=your_email@outlook.com
IMAP_PASSWORD=your_password_or_app_password

# Advanced Settings (optional)
IMAP_CHECK_INTERVAL=3600  # Check every hour (in seconds)
IMAP_FOLDER=INBOX  # Folder to monitor
```

### 4. Configure for Your Email Provider

#### **Rediff Mail** (Easy Setup - No App Password needed!)

```env
IMAP_PROVIDER=rediff
IMAP_EMAIL=your_username@rediffmail.com
IMAP_PASSWORD=your_regular_password  # Use regular password
```

📘 See [REDIFF_SETUP.md](REDIFF_SETUP.md) for detailed Rediff Mail instructions

#### **Gmail**

```env
IMAP_PROVIDER=gmail
IMAP_EMAIL=your_username@gmail.com
IMAP_PASSWORD=your_16_char_app_password  # Generate at myaccount.google.com/apppasswords
```

Enable IMAP: Gmail Settings → Forwarding and POP/IMAP → Enable IMAP

#### **Outlook (Personal)**

```env
IMAP_PROVIDER=outlook
IMAP_EMAIL=your_email@outlook.com
IMAP_PASSWORD=your_app_password  # Generate at account.microsoft.com/security
```

#### **Yahoo Mail**

```env
IMAP_PROVIDER=yahoo
IMAP_EMAIL=your_email@yahoo.com
IMAP_PASSWORD=your_app_password  # Generate at login.yahoo.com/account/security
```

#### **Custom IMAP Server**

```env
IMAP_PROVIDER=custom
IMAP_HOST=imap.yourserver.com
IMAP_PORT=993
IMAP_EMAIL=your@email.com
IMAP_PASSWORD=your_password
```

### 5. Get API Keys

**Brevo API Key:**
1. Go to [Brevo](https://www.brevo.com/)
2. Sign up or log in
3. Navigate to Settings → API Keys
4. Create a new API key

**Gemini API Key (if using Gemini):**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key

**Outlook App Password (for IMAP Worker):**
1. Go to your [Microsoft Account Security](https://account.microsoft.com/security)
2. Enable two-factor authentication if not already enabled
3. Generate an "App Password" for email access
4. Use this app password in `IMAP_PASSWORD` (not your regular password)

## 🎯 Running the Application

### Start the API Server

```bash
# Activate virtual environment
venv\Scripts\activate

# Run with uvicorn
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

**What happens on startup:**
- ✅ Services initialize (Intent Detector + Brevo API)
- ✅ If `IMAP_ENABLED=true`, the background worker starts
- ✅ Worker connects to your Outlook mailbox via IMAP
- ✅ First email check runs immediately
- ⏰ Subsequent checks run every hour (configurable)

### Expose with ngrok

In a new terminal:

```bash
ngrok http 8000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.io`) - you'll use this in Outlook Power Automate.

## 📡 API Endpoints

### 1. Health Check

```bash
GET /
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "intent_detector": "initialized",
    "brevo_service": "initialized",
    "email_worker": {
      "running": true,
      "enabled": true,
      "check_interval_seconds": 3600,
      "next_run": "2026-02-02T15:30:00",
      "monitoring_email": "your@email.com",
      "monitoring_folder": "INBOX"
    }
  },
  "config": {
    "llm_provider": "gemini",
    "model": "gemini-pro"
  }
}
```

### 2. Worker Status

```bash
GET /worker/status
```

Check the current status of the background email worker.

### 3. Manual Worker Trigger

```bash
POST /worker/check-now
```

Manually trigger an immediate email check (useful for testing).

**Response:**
```json
{
  "success": true,
  "message": "Email check completed successfully"
}
```

### 4. Inbound Email Processing (Webhook)

```bash
POST /inbound-email
```

**Request Body:**
```json
{
  "sender_email": "user@example.com",
  "message_text": "Please unsubscribe me from your mailing list",
  "subject": "RE: Your Newsletter"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email processed successfully",
  "sender_email": "user@example.com",
  "unsubscribe_intent_detected": true,
  "unsubscribed_from_brevo": true,
  "details": {
    "intent_confidence": "high",
    "intent_reasoning": "Message explicitly requests unsubscribe",
    "brevo_result": {
      "success": true,
      "message": "Contact user@example.com has been blacklisted in Brevo",
      "action": "updated"
    }
  }
}
```

### 3. Test Intent Detection

Test LLM intent detection without triggering Brevo:

```bash
POST /test-intent
```

**Request Body:**
```json
{
  "sender_email": "test@example.com",
  "message_text": "I don't want to receive any more emails"
}
```

## � Email Processing Modes

### Mode 1: Background Worker (IMAP Polling)

**How it works:**
```
Outlook Mailbox (IMAP)
        ↓
Python Worker (every 1 hour)
        ↓
Fetch unread emails
        ↓
Detect unsubscribe intent (LLM)
        ↓
Unsubscribe via Brevo API
```

**Configuration:**
- Set `IMAP_ENABLED=true` in `.env`
- Configure your Outlook credentials
- Worker starts automatically with the API
- Checks mailbox every hour (configurable via `IMAP_CHECK_INTERVAL`)

**Advantages:**
- ✅ No need for Power Automate or webhooks
- ✅ Works with any IMAP-compatible email provider
- ✅ Processes emails in batches
- ✅ Can process historical unread emails

### Mode 2: Webhook (Real-time via Power Automate)

**How it works:**
```
Email arrives → Power Automate → Webhook → API → LLM → Brevo
```

**Advantages:**
- ✅ Real-time processing
- ✅ No polling overhead
- ✅ Works with Power Automate workflows

**Both modes can run simultaneously!**

## 🔗 Outlook Power Automate Integration (Webhook Mode)

### Setup Steps:

1. **Create a new Flow in Power Automate:**
   - Trigger: "When a new email arrives" (in a specific folder or all emails)
   - Filter for replies to campaign emails

2. **Add HTTP Action:**
   - Method: `POST`
   - URI: `https://your-ngrok-url.ngrok.io/inbound-email`
   - Headers:
     ```
     Content-Type: application/json
     ```
   - Body:
     ```json
     {
       "sender_email": "@{triggerBody()?['from']}",
       "message_text": "@{triggerBody()?['body']}",
       "subject": "@{triggerBody()?['subject']}"
     }
     ```

3. **Test the Flow:**
   - Send a test email with unsubscribe keywords
   - Verify the flow triggers and calls your API

## 🧪 Testing

### Test Background Worker:

```bash
# Check worker status
curl http://localhost:8000/worker/status

# Manually trigger an email check
curl -X POST http://localhost:8000/worker/check-now

# Check health including worker status
curl http://localhost:8000/health
```

### Test Webhook Endpoint with curl:

```bash
# Test intent detection
curl -X POST http://localhost:8000/test-intent \
  -H "Content-Type: application/json" \
  -d "{\"sender_email\":\"test@example.com\",\"message_text\":\"Please unsubscribe me\"}"

# Test full flow (will trigger Brevo)
curl -X POST http://localhost:8000/inbound-email \
  -H "Content-Type: application/json" \
  -d "{\"sender_email\":\"test@example.com\",\"message_text\":\"Remove me from this list\"}"
```

### Test with Python:

```python
import requests

url = "http://localhost:8000/test-intent"
payload = {
    "sender_email": "test@example.com",
    "message_text": "I want to unsubscribe from your emails"
}

response = requests.post(url, json=payload)
print(response.json())
```

## 🔧 Configuration Options

### Switch Between Ollama and Gemini

**Using Ollama (Local):**
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
```

**Using Gemini (Cloud):**
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-pro
```

### Available Ollama Models

Popular models you can use:
- `llama2` - Good balance of speed and accuracy
- `llama3` - Latest Llama model
- `mistral` - Fast and efficient
- `phi3` - Lightweight and fast

Pull a model:
```bash
ollama pull mistral
```

## 📊 Unsubscribe Detection Examples

The LLM will detect various unsubscribe phrases:

✅ **Detected:**
- "unsubscribe"
- "remove me from this list"
- "stop sending me emails"
- "I don't want to receive these anymore"
- "take me off your mailing list"
- "opt out"
- "cancel my subscription"

❌ **Not Detected:**
- "Thanks for the information"
- "Can you tell me more?"
- "I'm interested in your products"

## 🐛 Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve
```

### Brevo API Errors

- Verify your API key is correct
- Check API key permissions in Brevo dashboard
- Ensure your Brevo account is active

### ngrok Issues

```bash
# If ngrok URL expires, restart ngrok
ngrok http 8000

# For persistent URLs, upgrade to ngrok paid plan
```

## 📝 Project Structure

```
Unsuscribe-Email-workflow/
├── main.py                  # FastAPI application and endpoints
├── config.py                # Configuration and settings
├── models.py                # Pydantic models
├── services/
│   ├── __init__.py
│   ├── intent_detector.py   # LLM intent detection service
│   └── brevo_service.py     # Brevo API integration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your actual configuration (not in git)
├── .gitignore
└── README.md
```

## 🚀 Production Deployment

For production:

1. **Use a proper domain** instead of ngrok
2. **Add authentication** to your endpoints
3. **Use environment-specific configs**
4. **Add logging and monitoring**
5. **Consider using Gemini** for better reliability than local Ollama
6. **Set up proper error handling and retries**

### Example Production Run:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📄 License

MIT

## 🤝 Support

For issues or questions, please check the logs and ensure:
- Environment variables are set correctly
- Ollama is running (if using local LLM)
- Brevo API key is valid
- ngrok is exposing the correct port
