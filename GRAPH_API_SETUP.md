# Microsoft Graph API Setup Guide

## Why Switch to Graph API?

Microsoft has **disabled basic authentication** (username/password) for Outlook/Microsoft 365 IMAP access as of **October 2022**. You must now use **OAuth 2.0 authentication** via Microsoft Graph API.

### Key Benefits:
- ✅ **Secure**: OAuth 2.0 token-based authentication
- ✅ **Compliant**: Meets Microsoft security requirements  
- ✅ **No Password**: No need to store email passwords
- ✅ **Better API**: More features than IMAP
- ✅ **Reliable**: Direct Microsoft integration

---

## Prerequisites

- Microsoft 365 / Outlook.com account
- Azure AD (Active Directory) access
- Administrator permissions (for app registration)

---

## Step 1: Register an Azure AD Application

### 1.1 Go to Azure Portal
Visit: https://portal.azure.com

### 1.2 Navigate to Azure Active Directory
- Click on **Azure Active Directory** from the left menu
- Or search for "Azure Active Directory" in the top search bar

### 1.3 Register New Application
1. Click **App registrations** from the left menu
2. Click **+ New registration**
3. Fill in the details:
   - **Name**: `Unsubscribe Email Workflow` (or your preferred name)
   - **Supported account types**: 
     - Select **"Accounts in this organizational directory only"** (for single tenant)
     - Or **"Accounts in any organizational directory"** (for multi-tenant)
   - **Redirect URI**: Leave blank (not needed for daemon apps)
4. Click **Register**

### 1.4 Note Your Application IDs
After registration, you'll see:
- **Application (client) ID**: `12345678-1234-1234-1234-123456789abc`
- **Directory (tenant) ID**: `87654321-4321-4321-4321-cba987654321`

**📝 Save these values!** You'll need them for configuration.

---

## Step 2: Create Client Secret

### 2.1 Go to Certificates & Secrets
1. In your app registration page, click **Certificates & secrets** from the left menu
2. Click **+ New client secret**
3. Add a description: `Email Workflow Secret`
4. Choose expiration: **24 months** (recommended)
5. Click **Add**

### 2.2 Copy the Secret Value
⚠️ **IMPORTANT**: Copy the **Value** immediately! It won't be shown again.

Example: `abc123~XYZ.789-def456_ghi`

**📝 Save this secret value!**

---

## Step 3: Configure API Permissions

### 3.1 Add Required Permissions
1. Click **API permissions** from the left menu
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions** (not Delegated)

### 3.2 Add These Permissions:
Search and add the following permissions:

1. **Mail.Read** - Read mail in all mailboxes
2. **Mail.ReadWrite** - Read and write mail in all mailboxes (to mark as read)
3. **User.Read.All** - Read all users' profiles (optional, for verification)

### 3.3 Grant Admin Consent
⚠️ **Critical Step**: You must grant admin consent for these permissions.

1. After adding permissions, click **Grant admin consent for [Your Organization]**
2. Click **Yes** to confirm
3. You should see green checkmarks in the "Status" column

---

## Step 4: Configure Application

### 4.1 Update `.env` File

Add these new environment variables to your `.env` file:

```env
# Microsoft Graph API Configuration (for Outlook/Microsoft 365)
USE_GRAPH_API=true
GRAPH_CLIENT_ID=12345678-1234-1234-1234-123456789abc
GRAPH_CLIENT_SECRET=abc123~XYZ.789-def456_ghi
GRAPH_TENANT_ID=87654321-4321-4321-4321-cba987654321

# Email Configuration (keep these)
IMAP_ENABLED=true
IMAP_PROVIDER=outlook
IMAP_EMAIL=your-email@yourdomain.com
IMAP_FOLDER=Inbox
```

**Replace with your actual values:**
- `GRAPH_CLIENT_ID`: Your Application (client) ID
- `GRAPH_CLIENT_SECRET`: Your client secret value
- `GRAPH_TENANT_ID`: Your Directory (tenant) ID
- `IMAP_EMAIL`: The mailbox email address to monitor

### 4.2 Important Settings

- **USE_GRAPH_API=true**: Enables Graph API instead of IMAP
- **IMAP_PASSWORD**: No longer needed when using Graph API! (can be left empty)
- **IMAP_EMAIL**: Still needed to specify which mailbox to access

---

## Step 5: Install Dependencies

Install the Microsoft Authentication Library:

```bash
pip install msal
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

---

## Step 6: Test the Connection

### 6.1 Create Test Script

Create `test_graph.py`:

```python
import asyncio
from services.graph_email_fetcher import GraphEmailFetcher

async def test():
    fetcher = GraphEmailFetcher()
    
    # Test connection
    if fetcher.test_connection():
        print("\n✅ Connection successful!")
        
        # Try fetching emails
        emails = await fetcher.fetch_unread_emails()
        print(f"\nFound {len(emails)} unread emails")
    else:
        print("\n❌ Connection failed!")

if __name__ == "__main__":
    asyncio.run(test())
```

### 6.2 Run Test

```bash
python test_graph.py
```

**Expected Output:**
```
🔍 Testing Microsoft Graph API connection...
📧 User: your-email@yourdomain.com
🔑 Client ID: 12345678...
✅ Successfully acquired access token
✅ Connection successful!
👤 Display Name: Your Name
📧 Email: your-email@yourdomain.com
📁 Available folders: ['Inbox', 'Drafts', 'Sent Items', 'Deleted Items', ...]
```

---

## Step 7: Start the Application

### 7.1 Start the API

```bash
python main.py
```

**Look for these messages:**
```
🚀 Starting Unsubscribe Email Workflow API...
📊 Using Microsoft Graph API for Outlook
✅ Successfully acquired access token
✅ Email worker started successfully!
```

### 7.2 Start Streamlit UI

```bash
streamlit run streamlit_app.py
```

---

## Troubleshooting

### Error: "Failed to acquire token"

**Possible causes:**
1. **Incorrect Client ID/Secret/Tenant ID**
   - Double-check values in `.env`
   - Make sure no extra spaces or quotes

2. **Client Secret Expired**
   - Generate a new secret in Azure Portal
   - Update `.env` with new secret

3. **Insufficient Permissions**
   - Verify API permissions are added
   - Ensure admin consent is granted (green checkmarks)

### Error: "Insufficient privileges"

**Solution:**
- You're missing required API permissions
- Go to Azure Portal → App registrations → API permissions
- Add **Mail.Read** and **Mail.ReadWrite** (Application permissions)
- Grant admin consent

### Error: "Resource not found"

**Possible causes:**
1. **Wrong Email Address**
   - Verify `IMAP_EMAIL` in `.env` is correct
   - Email must exist in your organization

2. **Wrong Tenant ID**
   - Verify `GRAPH_TENANT_ID` is correct
   - Should be from your Azure AD

### Test Connection Fails

**Debug steps:**
```bash
# 1. Check configuration
python -c "from config import settings; print(f'Client ID: {settings.graph_client_id[:8]}...'); print(f'Tenant: {settings.graph_tenant_id[:8]}...'); print(f'Email: {settings.imap_email}')"

# 2. Verify Python packages
pip show msal

# 3. Test token acquisition
python test_graph.py
```

---

## Security Best Practices

### 1. Protect Your Secrets
- ✅ Never commit `.env` to Git
- ✅ Use `.gitignore` to exclude `.env`
- ✅ Rotate secrets regularly (every 6-12 months)
- ✅ Use Azure Key Vault in production

### 2. Limit Permissions
- ✅ Only grant necessary API permissions
- ✅ Use least-privilege principle
- ✅ Review permissions periodically

### 3. Monitor Access
- ✅ Check Azure AD sign-in logs
- ✅ Review API usage in Azure Portal
- ✅ Set up alerts for suspicious activity

---

## Migration from IMAP

### For Existing Users

If you're currently using IMAP (with password):

1. **Complete Steps 1-4** above (Azure AD setup)
2. **Update `.env`**:
   ```env
   USE_GRAPH_API=true
   GRAPH_CLIENT_ID=your-client-id
   GRAPH_CLIENT_SECRET=your-client-secret
   GRAPH_TENANT_ID=your-tenant-id
   # Keep IMAP_EMAIL, remove or keep IMAP_PASSWORD (not used)
   ```
3. **Test**: Run `python test_graph.py`
4. **Restart API**: `python main.py`

### Rollback to IMAP (if needed)

If Graph API isn't working and you need to temporarily use IMAP:

```env
USE_GRAPH_API=false
IMAP_PASSWORD=your-password
```

**Note**: IMAP with basic auth is deprecated and may stop working!

---

## Multi-Tenant Support

If you need to access mailboxes across multiple organizations:

### 1. Change Account Type
When registering the app, select:
- **"Accounts in any organizational directory (Any Azure AD directory - Multitenant)"**

### 2. Update Authority URL
The code automatically uses the tenant ID, but for multi-tenant:
- You might need to use `common` instead of specific tenant ID
- Modify `graph_email_fetcher.py` if needed

---

## Production Deployment

### Recommended Setup

1. **Azure Key Vault**
   - Store secrets in Azure Key Vault
   - Use Managed Identity to access secrets

2. **Managed Identity**
   - Deploy to Azure (App Service, Container, etc.)
   - Use Managed Identity instead of client secret
   - More secure, no secret rotation needed

3. **Certificate Authentication**
   - Use certificate instead of client secret
   - More secure than secrets
   - Upload certificate in Azure Portal

### Example: Using Managed Identity

```python
# In production, modify graph_email_fetcher.py:
from azure.identity import ManagedIdentityCredential

# Instead of client secret:
credential = ManagedIdentityCredential(client_id=self.client_id)
```

---

## FAQ

### Q: Do I need admin rights?
**A**: Yes, to register the app and grant admin consent for API permissions.

### Q: Can I use personal Outlook.com account?
**A**: For personal accounts, you need different setup (delegated permissions with user consent). This guide is for organizational accounts (Microsoft 365).

### Q: How long does the access token last?
**A**: Typically 1 hour. The library automatically handles token refresh.

### Q: Can I use this for multiple mailboxes?
**A**: Yes! Just change `IMAP_EMAIL` to the mailbox you want to monitor. Your app can access any mailbox in the organization (with proper permissions).

### Q: Is this more expensive than IMAP?
**A**: Graph API is included with Microsoft 365 licenses. No additional cost!

---

## Additional Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Azure AD App Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Graph API Mail Reference](https://docs.microsoft.com/en-us/graph/api/resources/mail-api-overview)

---

## Support

If you encounter issues:

1. Check this guide thoroughly
2. Review Azure AD audit logs
3. Test with `test_graph.py`
4. Check application logs in terminal

---

**Made with ❤️ by [Piyush Chourey](https://github.com/piyushchourey11)**
