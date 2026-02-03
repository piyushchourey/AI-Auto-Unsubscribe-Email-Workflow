# Streamlit UI Guide

## Overview
The Streamlit UI provides a visual interface for managing your unsubscribe email workflow with dynamic configuration for multiple email accounts.

## Features

### 📊 Dashboard
- Real-time API and worker status
- System health monitoring
- Manual email check trigger
- View system configuration

### ⚙️ Configuration Sidebar
- **Multiple Email Accounts**: Switch between:
  - Cloudchillies (Rediff Mail)
  - Lending Logic (Microsoft 365)
  - Gmail
- **LLM Provider Selection**: Choose between Ollama (local) or Gemini (cloud)
- **IMAP Settings**: Configure email monitoring
- **Brevo API**: Manage unsubscribe API key

### 🧪 Test Intent Detection
- Test the LLM's unsubscribe detection
- Pre-loaded sample messages
- Custom message testing
- View confidence scores and reasoning

### ✉️ Test Brevo API
- Directly test email blacklisting
- Verify Brevo API integration
- See detailed API responses

## Installation

1. **Install Streamlit**:
```powershell
D:/Projects/Unsuscribe-Email-workflow/venv/Scripts/activate
pip install streamlit requests
```

2. **Start the API** (in one terminal):
```powershell
python main.py
```

3. **Start the UI** (in another terminal):
```powershell
streamlit run streamlit_app.py
```

Or use the batch file:
```powershell
run_ui.bat
```

## Usage

### Setting Up Email Account

1. **Select Account** from sidebar dropdown:
   - Cloudchillies (Rediff)
   - Lending Logic (Microsoft 365)
   - Gmail

2. **Configure Settings**:
   - Enable/disable IMAP worker
   - Enter email and password
   - Set check interval

3. **Select LLM Provider**:
   - Ollama (local) - requires Ollama installed
   - Gemini (cloud) - requires API key

4. **Add Brevo API Key**

5. **Click "💾 Save Configuration"**

6. **Restart the API** to apply changes:
```powershell
# Stop current API (Ctrl+C)
python main.py
```

### Switching Between Accounts

Simply select a different account in the sidebar and update the email/password. No need to edit `.env` files manually!

### Testing

**Test Intent Detection**:
1. Go to "🧪 Test Intent" tab
2. Select a sample message or write custom text
3. Click "🤖 Analyze Intent"
4. View results and LLM reasoning

**Test Brevo API**:
1. Go to "✉️ Test Brevo" tab
2. Enter an email to blacklist
3. Click "🚫 Blacklist Email"
4. View API response

### Monitoring

**Dashboard Tab**:
- Check API/Worker status
- View next scheduled check time
- Manually trigger email check
- View system configuration

## Configuration Files

The UI manages your `.env` file automatically:

**Before**: Edit `.env` manually
```
IMAP_PROVIDER=outlook
IMAP_EMAIL=user@example.com
```

**After**: Use UI sidebar
- Select account from dropdown
- Enter credentials
- Click save

## Multiple Account Workflow

### Scenario 1: Cloudchillies Monitoring
1. Select "Cloudchillies (Rediff)" in sidebar
2. Enter `user1@cloudchillies.com` and password
3. Enable IMAP worker
4. Save configuration
5. Restart API

### Scenario 2: Lending Logic Monitoring
1. Select "Lending Logic (Microsoft 365)" in sidebar
2. Enter `user2@lendinglogic.com` and app password
3. Enable IMAP worker
4. Save configuration
5. Restart API

### Switching Accounts
- Change selection in sidebar
- Update credentials
- Save and restart API
- No manual `.env` editing needed!

## LLM Provider Switching

### Using Ollama (Local)
1. Install Ollama: https://ollama.ai
2. Pull model: `ollama pull llama3.2`
3. Select "Ollama (Local)" in UI
4. Verify base URL (default: `http://localhost:11434`)
5. Save configuration

### Using Gemini (Cloud)
1. Get API key from Google AI Studio
2. Select "Gemini (Cloud)" in UI
3. Enter API key
4. Choose model (default: `gemini-2.0-flash-exp`)
5. Save configuration

## Troubleshooting

### UI Won't Start
```powershell
# Install dependencies
pip install streamlit requests

# Run directly
streamlit run streamlit_app.py
```

### API Not Connected
- Check if API is running: `http://localhost:8000/health`
- Start API: `python main.py`
- Verify port 8000 is free

### Configuration Not Saving
- Check file permissions on `.env`
- Ensure working directory is correct
- Restart API after saving

### Worker Not Running
- Verify IMAP is enabled in UI
- Check credentials are correct
- View errors in API terminal
- Test with diagnostic: `python test_imap.py`

## Tips

1. **Always restart API** after saving configuration
2. **Test IMAP connection** with diagnostic tool first
3. **Use App Passwords** for Gmail/Outlook (not regular password)
4. **Monitor API terminal** for detailed logs
5. **Check intervals**: Longer = fewer checks, shorter = more frequent

## Ports

- API: `http://localhost:8000`
- UI: `http://localhost:8501` (Streamlit default)

## Security Notes

- Passwords stored in `.env` (plain text)
- Use App Passwords when possible
- Keep `.env` in `.gitignore`
- Don't share `.env` or screenshots with passwords
- Consider using environment variables on production

## Next Steps

1. Start both API and UI
2. Configure your first email account
3. Test intent detection
4. Test Brevo API
5. Enable worker and monitor dashboard
6. Switch accounts as needed

Enjoy the visual workflow! 🚀
