# Rediff Mail Setup Guide

Complete guide to configure the email worker with Rediff Mail.

## 🔧 Quick Setup for Rediff Mail

### Step 1: Configure `.env` File

Edit your `.env` file with these settings:

```env
# Email Provider
IMAP_PROVIDER=rediff

# Your Rediff Mail Credentials
IMAP_EMAIL=your_username@rediffmail.com
IMAP_PASSWORD=your_regular_password

# Worker Settings
IMAP_ENABLED=true
IMAP_CHECK_INTERVAL=3600
IMAP_FOLDER=INBOX
```

**Important Notes:**
- ✅ Rediff uses your **regular password** (not an App Password)
- ✅ IMAP Host: `mail.rediff.com` (auto-configured)
- ✅ IMAP Port: `993` (SSL enabled)
- ⚠️ **Note:** Rediff Mail IMAP support may be limited or unavailable for some accounts

### Step 2: Enable IMAP in Rediff Mail

1. **Log in to Rediffmail:**
   - Go to https://mail.rediff.com
   - Log in with your credentials

2. **Enable IMAP Access:**
   - Click on "Settings" (gear icon)
   - Go to "Accounts" or "Mail Settings"
   - Look for "IMAP Access" or "POP/IMAP Settings"
   - **Enable IMAP** if not already enabled
   - Save changes

3. **Verify IMAP is enabled:**
   - Some older Rediff accounts might have IMAP disabled
   - If you can't find IMAP settings, it may be enabled by default

### Step 3: Test Connection

Run the diagnostic tool:

```powershell
python test_imap.py
```

**Expected output:**
```
📋 Configuration:
  Provider: REDIFF
  Host: mail.rediff.com
  Port: 993
  Email: your_username@rediffmail.com
  
✅ ALL TESTS PASSED! Your IMAP configuration is working!
```

### Important: Rediff Mail IMAP Limitations

⚠️ **Rediff Mail may have limited or no IMAP support** depending on your account type:

- Some Rediff accounts don't support IMAP at all
- IMAP may only be available for paid/premium accounts
- Free accounts might be limited to webmail only

**If IMAP doesn't work, use Webhook Mode instead:**

1. Set in `.env`:
   ```env
   IMAP_ENABLED=false
   ```

2. Use Power Automate to forward emails to the API (see main README.md)

3. This works perfectly without needing IMAP access!

### Step 4: Start the Server

```powershell
python main.py
```

**Expected startup output:**
```
🚀 Starting email worker...
📧 Provider: REDIFF
📬 Connecting to IMAP server: imap.rediffmail.com
✅ Logged in as: your_username@rediffmail.com
✅ Email worker started successfully!
```

## 🔍 Troubleshooting Rediff Mail

### Issue: "Login failed" Error

**Possible causes:**

1. **Incorrect Password**
   - ✅ Double-check your password
   - ✅ Try logging in at mail.rediff.com with same credentials
   - ✅ No spaces before/after password in `.env`

2. **IMAP Not Enabled**
   - ✅ Enable IMAP in Rediff Mail settings
   - ✅ Wait 5-10 minutes after enabling
   - ✅ Some accounts need verification before IMAP works

3. **Account Locked/Suspended**
   - ✅ Verify you can log in to webmail
   - ✅ Check for any security alerts
   - ✅ Complete any pending verifications

### Issue: "Connection timeout"

**Solutions:**
- Check internet connection
- Verify firewall isn't blocking port 993
- Try from a different network
- Rediff servers might be temporarily down

### Issue: "Certificate verification failed"

**This is rare but possible:**
- Update Python certificates: `pip install --upgrade certifi`
- Check system date/time is correct

## 📧 Supported Rediff Mail Domains

The worker supports all Rediff email domains:
- `@rediffmail.com`
- `@rediff.com`
- Any custom domain configured with Rediff

## ⚙️ Advanced Configuration

### Check Emails More Frequently

For busier mailboxes, check every 15 minutes:

```env
IMAP_CHECK_INTERVAL=900  # 15 minutes in seconds
```

### Monitor a Specific Folder

If you have campaign replies in a subfolder:

```env
IMAP_FOLDER=Campaigns
```

### Use Custom IMAP Settings

If Rediff changes their server (unlikely):

```env
IMAP_PROVIDER=custom
IMAP_HOST=imap.rediffmail.com
IMAP_PORT=993
```

## 🎯 Testing with Real Emails

1. **Send a test email to your Rediff inbox:**
   ```
   Subject: Test Unsubscribe
   Body: Please unsubscribe me from this list
   ```

2. **Leave it unread**

3. **Trigger manual check:**
   ```powershell
   curl -X POST http://localhost:8000/worker/check-now
   ```

4. **Watch the console:**
   ```
   📧 Found 1 unread emails
   🤖 Analyzing intent with LLM...
   🎯 Intent detected: True
   ✅ Successfully unsubscribed from Brevo
   ```

## 🔐 Security Notes

**Rediff Mail Security:**
- Rediff uses regular passwords (no separate App Passwords)
- Keep your `.env` file secure and never commit it to git
- Use environment variables in production
- Enable two-factor auth on Rediff if available

**Best Practices:**
- Use a dedicated Rediff account for email campaigns
- Don't use your personal Rediff account
- Regularly monitor the worker logs
- Set up alerts for processing errors

## 🆚 Rediff vs Other Providers

| Feature | Rediff | Gmail | Outlook |
|---------|--------|-------|---------|
| IMAP Support | ✅ Yes | ✅ Yes | ✅ Yes |
| App Password Required | ❌ No | ✅ Yes | ✅ Yes (personal) |
| 2FA Required | ❌ No | ✅ Recommended | ✅ Recommended |
| Setup Difficulty | 🟢 Easy | 🟡 Medium | 🟡 Medium |
| Works with Work Email | ❌ Personal only | ✅ Yes | ⚠️ Depends |

## 📊 Common Rediff Mail Limits

- **IMAP connections:** Usually 10-15 simultaneous connections
- **Email storage:** Varies by account type
- **Rate limits:** Check frequently but not excessively (1 hour interval is safe)

## 🚀 Multiple Email Providers

You can also switch providers easily:

**For Gmail:**
```env
IMAP_PROVIDER=gmail
IMAP_EMAIL=you@gmail.com
IMAP_PASSWORD=your_app_password
```

**For Outlook:**
```env
IMAP_PROVIDER=outlook
IMAP_EMAIL=you@outlook.com
IMAP_PASSWORD=your_app_password
```

**For Yahoo:**
```env
IMAP_PROVIDER=yahoo
IMAP_EMAIL=you@yahoo.com
IMAP_PASSWORD=your_app_password
```

All provider configurations are pre-loaded - just change `IMAP_PROVIDER`!

## ❓ Need Help?

1. Run diagnostics: `python test_imap.py`
2. Check Rediff webmail works: https://mail.rediff.com
3. Verify IMAP is enabled in settings
4. Check console logs for detailed errors
5. Try webhook mode if IMAP doesn't work

## 📝 Example `.env` for Rediff

```env
# LLM Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-pro

# Brevo API
BREVO_API_KEY=your_brevo_key

# Server
HOST=0.0.0.0
PORT=8000

# Rediff Mail Configuration
IMAP_ENABLED=true
IMAP_PROVIDER=rediff
IMAP_EMAIL=campaigns@rediffmail.com
IMAP_PASSWORD=your_password_here
IMAP_CHECK_INTERVAL=3600
IMAP_FOLDER=INBOX
```

That's it! Your Rediff Mail account is now ready to automatically process unsubscribe requests! 🎉
