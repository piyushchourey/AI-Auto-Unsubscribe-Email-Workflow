# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   Unsubscribe Processing System                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│  Mode 1: IMAP Worker │         │ Mode 2: Webhook API  │
│   (Background Job)   │         │    (Real-time)       │
└──────────────────────┘         └──────────────────────┘
         │                                  │
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │            Email Processing Pipeline              │  │
│  │                                                   │  │
│  │  1. Email Fetcher (IMAP) / Webhook Receiver      │  │
│  │  2. Intent Detector (LangChain + LLM)            │  │
│  │  3. Brevo Service (Contact Unsubscribe)          │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                                  │
         ▼                                  ▼
┌──────────────────────┐         ┌──────────────────────┐
│   Ollama (Local)     │         │   Gemini (Cloud)     │
│   LLM Provider       │   OR    │   LLM Provider       │
└──────────────────────┘         └──────────────────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │  Brevo API    │
                │ (Unsubscribe) │
                └───────────────┘
```

## Data Flow

### Mode 1: IMAP Worker (Automated Polling)

```
┌─────────────────┐
│ Outlook Mailbox │
│   (IMAP/993)    │
└────────┬────────┘
         │
         │ Poll every 1 hour
         │
         ▼
┌─────────────────┐
│ Email Fetcher   │
│ - Connect IMAP  │
│ - Fetch UNSEEN  │
│ - Parse emails  │
└────────┬────────┘
         │
         │ {sender, message, subject}
         │
         ▼
┌─────────────────┐
│ Intent Detector │
│ - LangChain     │
│ - Ollama/Gemini │
│ - Analyze text  │
└────────┬────────┘
         │
         │ Unsubscribe intent?
         │
         ▼
┌─────────────────┐
│  Brevo Service  │
│ - Blacklist     │
│ - Update        │
└─────────────────┘
```

### Mode 2: Webhook (Real-time)

```
┌────────────────────┐
│  Outlook Email     │
│    Arrives         │
└─────────┬──────────┘
          │
          │ Trigger
          │
          ▼
┌────────────────────┐
│ Power Automate     │
│  - When email      │
│  - Extract data    │
└─────────┬──────────┘
          │
          │ HTTP POST
          │
          ▼
┌────────────────────┐
│ /inbound-email     │
│   Endpoint         │
└─────────┬──────────┘
          │
          │ {sender, message}
          │
          ▼
┌────────────────────┐
│ Intent Detector    │
│ + Brevo Service    │
└────────────────────┘
```

## API Endpoints

```
GET  /                     - Health check
GET  /health               - Detailed status
GET  /worker/status        - Worker status
POST /worker/check-now     - Manual trigger
POST /inbound-email        - Webhook endpoint
POST /test-intent          - Test LLM only
```

## Configuration Files

```
.env                       - Environment config
config.py                  - Settings management
requirements.txt           - Python dependencies
```

## Services

```
services/
├── intent_detector.py     - LLM-based intent detection
├── brevo_service.py       - Brevo API integration
├── email_fetcher.py       - IMAP email fetching
└── email_worker.py        - Background scheduler
```

## Worker Schedule

```
[Startup] → [Initial Check] → [Wait 1 hour] → [Check] → [Wait 1 hour] → ...
                    ↓               ↓              ↓
             Process emails  Process emails  Process emails
```

## Security Considerations

- ✅ API keys stored in `.env` (not in code)
- ✅ App passwords for IMAP (not main password)
- ✅ SSL/TLS for IMAP connection (port 993)
- ✅ Email content processed locally
- ⚠️ Add authentication for production webhooks
- ⚠️ Use HTTPS for webhook endpoints (ngrok provides this)

## Scaling Options

### Horizontal Scaling
- Run multiple workers for different mailboxes
- Load balance webhook endpoints
- Use message queue for processing

### Vertical Scaling
- Increase `IMAP_CHECK_INTERVAL` for higher volume
- Batch process emails more efficiently
- Cache LLM responses for similar messages

### Cost Optimization
- Use local Ollama instead of Gemini API
- Adjust check interval based on email volume
- Implement smart filtering before LLM analysis
