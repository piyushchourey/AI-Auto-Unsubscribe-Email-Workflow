# Quick Migration Guide: IMAP to Graph API

## The Problem

Microsoft has **disabled basic authentication** (username/password) for Outlook/Microsoft 365 IMAP. If you're getting "Login failed" errors with Outlook, you need to switch to Microsoft Graph API with OAuth.

## Quick Steps

### 1. Azure AD App Registration (5 minutes)

1. Go to https://portal.azure.com
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Name it: `Unsubscribe Email Workflow`
4. Register and note the **Client ID** and **Tenant ID**

### 2. Create Client Secret (2 minutes)

1. In your app → **Certificates & secrets** → **New client secret**
2. Copy the secret value immediately (won't be shown again!)

### 3. Add API Permissions (3 minutes)

1. Go to **API permissions** → **Add a permission**
2. Select **Microsoft Graph** → **Application permissions**
3. Add these permissions:
   - `Mail.Read`
   - `Mail.ReadWrite`
4. Click **Grant admin consent** ⚠️ Important!

### 4. Update Configuration (1 minute)

Add to your `.env` file:

```env
# Enable Graph API
USE_GRAPH_API=true

# Graph API Credentials
GRAPH_CLIENT_ID=your-client-id-here
GRAPH_CLIENT_SECRET=your-client-secret-here
GRAPH_TENANT_ID=your-tenant-id-here

# Email settings (keep these)
IMAP_ENABLED=true
IMAP_PROVIDER=outlook
IMAP_EMAIL=your-email@yourdomain.com
IMAP_FOLDER=Inbox

# Password no longer needed!
# IMAP_PASSWORD can be removed or left empty
```

### 5. Install Dependencies

```bash
pip install msal
```

### 6. Test Connection

```bash
python test_graph.py
```

**Expected output:**
```
✅ Connection successful!
✅ Successfully fetched X unread emails
```

### 7. Start Application

```bash
python main.py
```

Look for: `📊 Using Microsoft Graph API for Outlook`

---

## Complete Details

For full setup instructions, see **[GRAPH_API_SETUP.md](GRAPH_API_SETUP.md)**

---

## Troubleshooting

### "Failed to acquire token"
- Check Client ID, Secret, and Tenant ID are correct
- No extra spaces or quotes in `.env`

### "Insufficient privileges"
- Add **Mail.Read** and **Mail.ReadWrite** permissions
- Grant admin consent (green checkmarks)

### "Resource not found"
- Verify `IMAP_EMAIL` is correct
- Email must exist in your organization

---

## Other Email Providers

**Gmail & Rediff**: Continue using IMAP (no changes needed)

```env
USE_GRAPH_API=false  # Or omit this line
IMAP_PROVIDER=gmail  # or rediff
IMAP_PASSWORD=your-app-password
```

---

**Need help?** Check [GRAPH_API_SETUP.md](GRAPH_API_SETUP.md) for detailed instructions.
