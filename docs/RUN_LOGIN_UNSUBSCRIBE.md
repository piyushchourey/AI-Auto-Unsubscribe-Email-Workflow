# How to Run: Login → Unsubscribe Process

All unsubscribe-related endpoints require authentication. You can use either the **Streamlit UI** or the **API (curl/PowerShell)**.

---

## Option 1: Using the Streamlit UI (recommended)

1. **One-time:** In `.env`, set `ADMIN_SEED_EMAIL`, `ADMIN_SEED_PASSWORD`, and `JWT_SECRET_KEY` (see below).
2. **Start the API:** `python main.py` (creates the admin user on first run if none exist).
3. **Start the UI:** `streamlit run streamlit_app.py`
4. **In the app:** Log in with your admin email and password in the **sidebar**.
5. After login you can use **Dashboard**, **Test Intent**, **Test Brevo**, **Blocklist**, and **Worker** (start/stop, check now) from the UI.

If the session expires, log in again from the sidebar.

---

## 1. One-time setup

### 1.1 Auth and seed admin in `.env`

Add (or update) these in your `.env`:

```env
# JWT (use a long random secret in production)
JWT_SECRET_KEY=your-secret-key-at-least-32-chars-long

# First admin user – used to seed the DB (see 1.2)
ADMIN_SEED_EMAIL=admin@example.com
ADMIN_SEED_PASSWORD=YourSecurePassword123
```

### 1.2 Seed the admin user in the database

You can seed the admin credential in either of these ways:

**Option A – When the API starts (automatic)**  
- Set `ADMIN_SEED_EMAIL` and `ADMIN_SEED_PASSWORD` in `.env`.  
- Run `python main.py`.  
- On startup, if the `users` table is **empty**, the app creates one admin user with that email and password.  
- If any user already exists, no new user is created.

**Option B – Manual seed (CLI)**  
- Set `ADMIN_SEED_EMAIL` and `ADMIN_SEED_PASSWORD` in `.env`.  
- From the project root, run:
  ```bash
  python seed_admin.py
  ```
- This creates the `users` table (if needed) and adds the admin user **only if no users exist**.  
- Use this to seed the DB without starting the API, or to re-seed after clearing the DB (if you delete all users first).

### 1.2 Install and start the API

```bash
# From project root
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On first run, if the database has no users, the app creates an admin user with `ADMIN_SEED_EMAIL` and `ADMIN_SEED_PASSWORD`.  
Server is at **http://localhost:8000**.

---

## 2. Login (get token)

Call the login endpoint with the same email and password you used for the seed admin.

**PowerShell:**

```powershell
$body = @{ email = "admin@example.com"; password = "YourSecurePassword123" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post -Body $body -ContentType "application/json"
$token = $response.access_token
Write-Host "Token: $token"
```

**curl (Windows cmd or Git Bash):**

```bash
curl -X POST http://localhost:8000/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"YourSecurePassword123\"}"
```

**Example response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Copy the `access_token` value and use it in the next step.

---

## 3. Unsubscribe process (with token)

Send the token in the **Authorization** header as: `Bearer <access_token>`.

### Option A – Process inbound email (full flow)

Simulates receiving an email and runs intent detection + Brevo unsubscribe if intent is detected:

```bash
curl -X POST http://localhost:8000/inbound-email ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" ^
  -H "Content-Type: application/json" ^
  -d "{\"sender_email\":\"user@example.com\",\"message_text\":\"Please remove me from your mailing list.\",\"subject\":\"Unsubscribe request\"}"
```

**PowerShell:**

```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"
$headers = @{
  "Authorization" = "Bearer $token"
  "Content-Type"  = "application/json"
}
$body = @{
  sender_email = "user@example.com"
  message_text = "Please remove me from your mailing list."
  subject      = "Unsubscribe request"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/inbound-email" -Method Post -Headers $headers -Body $body
```

### Option B – Test intent only (no Brevo)

Check how the LLM classifies the message, without calling Brevo:

```bash
curl -X POST http://localhost:8000/test-intent ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" ^
  -H "Content-Type: application/json" ^
  -d "{\"sender_email\":\"x@y.com\",\"message_text\":\"Stop sending me emails.\"}"
```

### Option C – Test Brevo blacklist only

Add an email to Brevo’s blacklist directly (no intent detection):

```bash
curl -X POST http://localhost:8000/test-brevo ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\"}"
```

---

## 4. Other protected endpoints (same token)

- **Current user:**  
  `GET http://localhost:8000/auth/me`  
  Header: `Authorization: Bearer <token>`

- **Blocklist (viewer+):**  
  - Stats: `GET /blocklist/stats`  
  - Recent logs: `GET /blocklist/recent?limit=50`  
  - Search: `GET /blocklist/search/user@example.com`  
  All with: `Authorization: Bearer <token>`

- **Worker (admin for start/stop):**  
  - Status: `GET /worker/status`  
  - Check now: `POST /worker/check-now`  
  - Start: `POST /worker/start`  
  - Stop: `POST /worker/stop`  
  All with: `Authorization: Bearer <token>`

---

## 5. Quick checklist

| Step | Action |
|------|--------|
| 1 | Set `ADMIN_SEED_EMAIL` and `ADMIN_SEED_PASSWORD` in `.env` |
| 2 | Run `python main.py` |
| 3 | `POST /auth/login` with that email and password → get `access_token` |
| 4 | Call `POST /inbound-email` (or other endpoints) with `Authorization: Bearer <access_token>` |

If you get **401 Unauthorized**, the token is missing, wrong, or expired. Log in again to get a new token.
