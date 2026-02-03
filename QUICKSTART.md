# Quick Start Guide - IMAP Worker Mode

This guide will help you set up the background worker to automatically process unsubscribe emails from your Outlook mailbox.

## ⚡ Quick Setup (5 minutes)

### 1. Install Dependencies

```powershell
cd d:\Projects\Unsuscribe-Email-workflow
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

Edit `.env` with your credentials:

```env
# LLM Configuration (Choose one)
LLM_PROVIDER=gemini  # or "ollama" for local
GEMINI_API_KEY=your_gemini_api_key_here

# Brevo API
BREVO_API_KEY=your_brevo_api_key_here

# IMAP Configuration
IMAP_ENABLED=true
IMAP_EMAIL=your_email@outlook.com
IMAP_PASSWORD=your_app_password_here
IMAP_CHECK_INTERVAL=3600  # Check every hour
```

### 3. Get App Password for Outlook

**⚠️ IMPORTANT: You MUST use an App Password, not your regular password!**

#### For Personal Accounts (@outlook.com, @hotmail.com, @live.com):

1. Go to https://account.microsoft.com/security
2. Click "Advanced security options"
3. Enable "Two-step verification" if not already enabled
4. Scroll to "App passwords" section
5. Click "Create a new app password"
6. Name it "Email Worker" or similar
7. **Copy the generated password** (it looks like: `abcd-efgh-ijkl-mnop`)
8. Paste this App Password (not your regular password) into `IMAP_PASSWORD` in `.env`

#### For Work/School Accounts (@company.com):

**⚠️ Work accounts often don't support IMAP or require special setup:**

1. Check with your IT administrator if IMAP is enabled
2. Your organization may require OAuth instead of passwords
3. Some organizations block IMAP entirely for security

**Alternative:** If IMAP doesn't work, use **Webhook Mode** instead:
- Set `IMAP_ENABLED=false` in `.env`
- Use Power Automate to send emails to the API webhook
- See "Outlook Power Automate Integration" section in README.md

#### Enable IMAP in Outlook Settings:

1. Go to https://outlook.live.com/mail/0/options/mail/accounts
2. Click "Sync email" 
3. Under "POP and IMAP", make sure **IMAP** is enabled
4. Save changes

### 4. Test IMAP Connection BEFORE Starting Server

**Run the diagnostic tool first:**

```powershell
python test_imap.py
```

This will:
- ✅ Test server reachability
- ✅ Test SSL connection
- ✅ Test login credentials
- ✅ List available folders
- ✅ Check for unread emails
- ❌ Show detailed error messages if something fails

**Expected successful output:**
```
✅ ALL TESTS PASSED! Your IMAP configuration is working!
```

**If it fails**, the tool will show you exactly what's wrong and how to fix it.

### 5. Start the Server

```powershell
python main.py
```

**Expected output:**
```
🚀 Starting Unsubscribe Email Workflow API...
📡 LLM Provider: gemini
Using Gemini with model: gemini-2.5-flash
✅ Services initialized successfully
🚀 Starting email worker...
⏰ Check interval: 3600 seconds (1.0 hours)
📧 Monitoring: your@email.com
📂 Folder: INBOX
🔍 Testing IMAP connection...
✅ Connection successful!
✅ Email worker started successfully!
```

### 6. Test the Worker

**Check worker status:**
```powershell
curl http://localhost:8000/worker/status
```

**Trigger manual check:**
```powershell
curl -X POST http://localhost:8000/worker/check-now
```

## 📧 Test with a Real Email

1. Send an email to your monitored inbox with text like:
   - "Please unsubscribe me"
   - "Remove me from this list"
   - "Stop sending emails"

2. Trigger a manual check or wait for the hourly run

3. Watch the console output:
```
📬 Connecting to IMAP server: outlook.office365.com
✅ Logged in as: your@email.com
📧 Found 1 unread emails
🤖 Analyzing intent with LLM...
🎯 Intent detected: True
🎲 Confidence: high
✅ Successfully unsubscribed user@example.com from Brevo
```

## 🔧 Troubleshooting

### "Login failed" error (Most Common Issue!)

**❌ Problem:** Using regular password instead of App Password

**✅ Solution:**
1. Run `python test_imap.py` to see detailed error
2. Make sure you generated an **App Password** (not your regular password)
3. App Password looks like: `abcd-efgh-ijkl-mnop` (16 characters with dashes)
4. Copy it EXACTLY (no extra spaces)
5. Paste into `IMAP_PASSWORD=` in `.env` file
6. Test again with `python test_imap.py`

### Work/School Email Not Working

**❌ Problem:** Organization has disabled IMAP or requires OAuth

**✅ Solutions:**
1. Contact your IT admin to enable IMAP for your account
2. **OR** Use Webhook Mode instead:
   ```env
   IMAP_ENABLED=false
   ```
   Then use Power Automate to forward emails to the API

### "IMAP not enabled" error

**✅ Solution:**
1. Go to https://outlook.live.com/mail/0/options/mail/accounts
2. Click "Sync email"
3. Enable "Let devices and apps use POP" → Actually enable **IMAP**
4. Save and wait 5-10 minutes
5. Test with `python test_imap.py`

### Worker not starting
- Check `IMAP_ENABLED=true` in `.env`
- Verify all IMAP credentials are correct
- Look for error messages in console output

### No emails being processed
- Verify emails are marked as "unread" in your mailbox
- Check that `IMAP_FOLDER=INBOX` matches your folder
- Try triggering a manual check: `curl -X POST http://localhost:8000/worker/check-now`

## ⚙️ Configuration Options

### Change Check Interval

To check every 30 minutes instead of 1 hour:
```env
IMAP_CHECK_INTERVAL=1800
```

### Monitor Different Folder

To monitor a subfolder:
```env
IMAP_FOLDER=Campaigns/Replies
```

### Disable Worker (Webhook Only Mode)

```env
IMAP_ENABLED=false
```

## 🎯 Next Steps

- Set up ngrok for webhook mode: `ngrok http 8000`
- Configure Power Automate for real-time processing
- Monitor the worker logs for unsubscribe patterns
- Check Brevo dashboard to verify contacts are being blacklisted

## 📊 Monitoring

**View health status:**
```powershell
curl http://localhost:8000/health | jq
```

**Check next scheduled run:**
```json
{
  "email_worker": {
    "running": true,
    "next_run": "2026-02-02T15:30:00",
    "check_interval_seconds": 3600
  }
}
```

## 🚀 Production Tips

1. **Use a service manager** to keep the worker running:
   - Windows: Use NSSM or Task Scheduler
   - Linux: Use systemd

2. **Set up logging** to file for monitoring

3. **Monitor API health endpoint** from external monitoring service

4. **Use Gemini** for reliability (vs local Ollama)

5. **Set appropriate check interval** based on email volume
