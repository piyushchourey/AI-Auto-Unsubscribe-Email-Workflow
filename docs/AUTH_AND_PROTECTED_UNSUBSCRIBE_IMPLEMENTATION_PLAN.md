# Implementation Plan: Authenticated Access & Protected Unsubscribe Feature

**Document version:** 1.0  
**Scope:** Extend the unsubscribe workflow so it is accessible only to authenticated users; add login with strong UX and security; role-based access; activity logging; validation and error-handling architecture.

---

## 1. Executive Summary

| Goal | Approach |
|------|----------|
| **Auth** | JWT-based API auth; login as a separate, reusable component (router + service). |
| **Users & roles** | New `User` table with roles (e.g. `admin`, `operator`, `viewer`). |
| **Protected feature** | Unsubscribe and blocklist APIs require valid JWT; role checks where needed. |
| **Activity** | New `activity_log` table to record who did what and when. |
| **Quality** | Centralized validation, error handling, and logging; keep existing FastAPI structure. |

---

## 2. Current Architecture (Baseline)

- **App:** Single FastAPI app in `main.py`; no routers.
- **DB:** SQLAlchemy + SQLite; one table `unsubscribe_logs` (no users).
- **Endpoints:** All public: `/inbound-email`, `/test-brevo`, `/test-intent`, `/worker/*`, `/blocklist/*`.
- **Logging:** `DatabaseService` logs unsubscribe actions (email, intent, Brevo result, `source`: webhook/worker/manual); no user attribution.

**In scope for protection (post-login):** Unsubscribe processing, blocklist management, worker control.  
**Optional to keep public:** Health/read-only status (e.g. `/`, `/health`) and webhook `/inbound-email` if it is called by Power Automate without user context (see Section 6).

---

## 3. Target Architecture

### 3.1 High-Level Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Application                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Public (no auth)     │  Auth Component        │  Protected (JWT)       │
│  ├─ GET  /            │  ├─ POST /auth/login   │  ├─ POST /inbound-email │
│  ├─ GET  /health      │  ├─ POST /auth/refresh│  ├─ POST /test-brevo    │
│  └─ (optional)        │  └─ GET  /auth/me      │  ├─ POST /test-intent   │
│     /inbound-email    │                        │  ├─ /worker/*           │
│  (if webhook stays)   │  Auth Router           │  ├─ /blocklist/*       │
│                       │  Auth Service          │  └─ (all need JWT +    │
│                       │  JWT dependency        │     optional role)     │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Database                                                                │
│  ├─ users (new)          – id, email, hashed_password, role, ...        │
│  ├─ activity_log (new)   – user_id, action, resource, details, ...      │
│  └─ unsubscribe_logs     – add optional performed_by_user_id (FK)      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Boundaries

- **Auth component (separate):**  
  - **Router:** `routers/auth.py` – login, refresh, me.  
  - **Service:** `services/auth_service.py` – password verification, token creation.  
  - **Security:** `core/security.py` – password hashing, JWT encode/decode.  
  - **Dependencies:** `core/dependencies.py` – `get_current_user`, optional `require_role(role)`.  
  No business logic for unsubscribe; only identity and tokens.

- **Protected API:**  
  - Option A: Keep routes in `main.py` and add `Depends(get_current_user)` (and optional `require_role`) to each.  
  - Option B: Move blocklist + worker + unsubscribe endpoints into `routers/` (e.g. `routers/unsubscribe.py`, `routers/blocklist.py`, `routers/worker.py`) and protect at router level.  
  Recommended: **Option B** for clarity and to keep “login feature” and “unsubscribe feature” as separate components.

- **Framework:** Stay on FastAPI; add `APIRouter` and `include_router`; keep existing services (e.g. `DatabaseService`, `IntentDetector`, `BrevoService`) unchanged in interface; extend DB and add new services (auth, activity) only where needed.

---

## 4. Data Model Updates

### 4.1 New Table: `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, auto | User ID. |
| `email` | String(255) | Unique, NOT NULL, index | Login identifier. |
| `hashed_password` | String(255) | NOT NULL | bcrypt/argon2 hash. |
| `role` | String(50) | NOT NULL, default `operator` | `admin`, `operator`, `viewer`. |
| `is_active` | Boolean | NOT NULL, default True | Soft disable. |
| `created_at` | DateTime | NOT NULL | Registration time. |
| `updated_at` | DateTime | NOT NULL | Last profile/role update. |

- **Roles (minimal set):**  
  - **admin:** Full access (blocklist clear, export, worker control, all unsubscribe endpoints).  
  - **operator:** Process emails, test intent/Brevo, view/search blocklist and logs; no clear/export or worker start/stop if you want to restrict those.  
  - **viewer:** Read-only (blocklist stats, recent, search; no POSTs, no worker control).  
  Role names and permissions can be refined later; the plan is to enforce them in dependencies and activity logging.

### 4.2 New Table: `activity_log`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, auto | Log entry ID. |
| `user_id` | Integer | FK(users.id), nullable | Who performed the action (null if system/webhook). |
| `action` | String(100) | NOT NULL | e.g. `login`, `logout`, `process_inbound_email`, `test_brevo`, `blocklist_export`, `blocklist_clear`, `worker_start`, `worker_stop`. |
| `resource` | String(100) | nullable | e.g. `inbound_email`, `blocklist`, `worker`. |
| `details` | Text | nullable | JSON or short text (e.g. target email, result). |
| `ip_address` | String(45) | nullable | Client IP for security audit. |
| `created_at` | DateTime | NOT NULL | Event time. |

- **Purpose:** Track who used the protected feature (and optionally login/logout), for audit and support.

### 4.3 Change to Existing Table: `unsubscribe_logs`

| Change | Description |
|--------|-------------|
| Add `performed_by_user_id` | Integer, nullable, FK(users.id). Null for webhook/worker; set when a logged-in user triggers the action (e.g. via API). |
| Keep `source` | Continue to distinguish `webhook` / `worker` / `manual`; when request is from a user, still set `source` (e.g. `manual`) and set `performed_by_user_id` to the current user. |

This keeps existing logging semantics and adds “who did it” for human-initiated actions.

---

## 5. Authentication & Login Design

### 5.1 Security Measures

- **Passwords:** Hash with **bcrypt** (or Argon2); never store or log plain text. Use a fixed cost factor (e.g. 12).  
- **Tokens:** **JWT** (RS256 or HS256); short-lived access token (e.g. 15–60 min); optional refresh token (longer-lived, stored or signed) for better UX.  
- **Login:**  
  - Rate limiting on login endpoint (e.g. 5 attempts per IP per 15 min) to mitigate brute force.  
  - Return generic “Invalid credentials” on failure; do not reveal whether email exists.  
- **Transport:** Enforce HTTPS in production; set secure cookie flags if using cookie-based refresh.  
- **Sessions:** Stateless JWT only, or stateful refresh tokens in DB; avoid storing access token server-side.

### 5.2 User Experience (UX)

- **Login API:**  
  - `POST /auth/login`: body `{ "email": "...", "password": "..." }`.  
  - Response: `{ "access_token": "...", "token_type": "bearer", "expires_in": 3600 }` (and optionally `refresh_token`).  
- **Usage:** Client sends `Authorization: Bearer <access_token>` on every protected request.  
- **Refresh (optional):** `POST /auth/refresh` with refresh token in body or cookie to get a new access token without re-entering password.  
- **Me:** `GET /auth/me`: returns current user (id, email, role) for UI to show identity and role.

### 5.3 Auth Component Structure (Separate)

- **`routers/auth.py`**  
  - `POST /auth/login`  
  - `POST /auth/refresh` (if implemented)  
  - `GET /auth/me` (protected by `get_current_user`)  

- **`services/auth_service.py`**  
  - `authenticate_user(email, password) -> User | None`  
  - `create_access_token(user) -> str` (and optional refresh)  
  - No dependency on unsubscribe or blocklist logic  

- **`core/security.py`**  
  - `hash_password(plain: str) -> str`  
  - `verify_password(plain, hashed) -> bool`  
  - `create_token(data, expires_delta) -> str`  
  - `decode_token(token) -> dict`  

- **`core/dependencies.py`**  
  - `get_current_user(token: str = Depends(oauth2_scheme)) -> User`  
  - `require_role(role: str)` returning a dependency that checks `current_user.role`  

- **`core/config.py`** (or extend existing `config.py`)  
  - JWT secret/key, algorithm, access (and refresh) expiry  

Auth is self-contained; the rest of the app only depends on `get_current_user` and optional role dependency.

---

## 6. API Design

### 6.1 Public Endpoints (No Auth)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health/info. |
| GET | `/health` | Detailed health (optional: keep public for load balancers). |

**Webhook:**  
- **Option A (recommended for “feature only for logged-in users”):** Move `POST /inbound-email` behind auth. Power Automate (or other callers) must send a fixed API key or a service JWT in a header; validate in a dedicated dependency so the “user” is a system account or the request is tied to a technical user.  
- **Option B:** Keep `POST /inbound-email` public but document that “dashboard and manual use” are protected; then only blocklist/worker and manual-test endpoints require login.  

For a strict “unsubscribe feature only after login,” treat the webhook as a special client: either protect it with a shared secret/API key (no user session) or a dedicated system user and log it in `activity_log` with that user.

### 6.2 Auth Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | No | Email + password → access_token (and optionally refresh_token). |
| POST | `/auth/refresh` | Refresh token | Issue new access_token. |
| GET | `/auth/me` | Bearer | Return current user (id, email, role). |

### 6.3 Protected Endpoints (Require JWT)

All of the following require `Depends(get_current_user)`. Add `require_role(...)` where needed.

| Method | Path | Min role | Description |
|--------|------|----------|-------------|
| POST | `/inbound-email` | operator | Process inbound email (unsubscribe workflow). |
| POST | `/test-brevo` | operator | Test Brevo blacklist. |
| POST | `/test-intent` | operator | Test intent detection. |
| GET | `/worker/status` | viewer | Worker status. |
| POST | `/worker/check-now` | operator | Trigger email check. |
| POST | `/worker/start` | admin | Start worker. |
| POST | `/worker/stop` | admin | Stop worker. |
| GET | `/blocklist/stats` | viewer | Stats. |
| GET | `/blocklist/all` | viewer | List blocklist. |
| GET | `/blocklist/search/{email}` | viewer | Search. |
| GET | `/blocklist/recent` | viewer | Recent logs. |
| GET | `/blocklist/export` | admin | Export CSV. |
| POST | `/blocklist/clear` | admin | Clear all logs. |

Use a single dependency that enforces both “authenticated” and “has required role” so that 403 is returned when role is insufficient.

### 6.4 Error Responses (Consistent)

- **401 Unauthorized:** Missing or invalid token.  
- **403 Forbidden:** Valid token but insufficient role.  
- **422 Unprocessable Entity:** Validation error (Pydantic).  
- **429 Too Many Requests:** Rate limit (e.g. login).  
- **500 Internal Server Error:** Unexpected error; message generic; details only in server logs.

Use a single exception handler or dependency chain so that auth failures return the same structure across the app.

---

## 7. Activity Logging Requirements

- **Log at least:**  
  - Login success/failure (e.g. `login_success`, `login_failed`); optional logout.  
  - Each protected unsubscribe/blocklist/worker action with `user_id`, `action`, `resource`, and minimal `details` (e.g. `{"email": "...", "success": true}`).  
- **Where:** Insert into `activity_log` from:  
  - Auth service (login).  
  - Protected route handlers or a middleware/dependency that runs after `get_current_user` and records request method, path, user_id, and optionally IP.  
- **Do not log:** Passwords or tokens; only metadata (email for login attempt is acceptable if you need to audit by email; consider logging only after successful login to avoid storing failed-attempt emails if policy forbids it).  
- **Retention:** Define policy (e.g. 90 days); implement later with a scheduled job or manual cleanup.

---

## 8. Validation and Error-Handling Architecture

- **Request validation:** Keep using Pydantic models for body/query; add validators for email format, password strength (e.g. min length, complexity) on registration/change-password if you add those later.  
- **Centralized HTTP exceptions:**  
  - Define a small set of exception classes (e.g. `AuthError`, `ForbiddenError`, `ValidationError`) and map them to status codes and response bodies in a single exception handler.  
- **Service layer:** Services (auth, unsubscribe, blocklist) raise domain exceptions or return Result types; routers catch and translate to HTTP. Avoid raising raw HTTPException deep in services.  
- **Logging:** Use a single logger (or structured logging); log at boundary (router): request id, user id (if any), endpoint, and outcome (success/failure); do not log sensitive data.  
- **Idempotency:** For actions like “process inbound email,” consider idempotency keys in the future if the same webhook can be retried; not required for first version.

---

## 9. Implementation Phases

### Phase 1 – Foundation (Auth + Users + DB)

1. Add dependencies: `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`.  
2. Create `core/` package: `security.py`, `dependencies.py`; extend `config` with JWT and auth settings.  
3. Add DB models: `User`, `ActivityLog`; add `performed_by_user_id` to `UnsubscribeLog`; create migrations or `init_db` updates.  
4. Implement `services/auth_service.py` and `routers/auth.py` (login, optional refresh, me).  
5. Seed one admin user (script or migration) for initial access.  
6. Add login rate limiting (in-memory or Redis) and activity log for login success/failure.

**Deliverable:** Working login and `/auth/me`; no protection on other endpoints yet.

### Phase 2 – Protect Unsubscribe and Blocklist

1. Add `get_current_user` and `require_role` to `core/dependencies.py` and wire OAuth2 scheme.  
2. Move (or duplicate) unsubscribe, blocklist, and worker routes into routers; attach `Depends(get_current_user)` and optional `require_role`.  
3. Update `DatabaseService.log_unsubscribe_action` to accept optional `performed_by_user_id`; pass current user from route.  
4. Add activity logging middleware or dependency that records user_id, action, resource, and timestamp for each protected call.  
5. Return 401/403 consistently from dependencies.  
6. Update Streamlit (or any UI) to call login, store token, and send `Authorization: Bearer <token>` on all relevant requests.

**Deliverable:** Unsubscribe and blocklist features are only usable after login; role-based access enforced; activity log populated.

### Phase 3 – Hardening and Observability

1. Add request validation and centralized exception handlers.  
2. Enforce HTTPS and secure headers in production.  
3. Optional: refresh token flow and token revocation.  
4. Document API (OpenAPI) with security scheme and role requirements.  
5. Define and implement activity log retention; add an admin-only endpoint to query activity log if needed.

**Deliverable:** Production-ready auth, clear errors, and audit trail.

---

## 10. File and Folder Layout (Suggested)

```
project/
├── main.py                    # App factory; include_router(auth_router, prefix="/auth")
├── config.py                  # Add JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
├── database.py                # Add User, ActivityLog; add column to UnsubscribeLog
├── models/                    # (optional) Pydantic request/response models
│   └── auth_models.py         # LoginRequest, TokenResponse, UserResponse
├── core/
│   ├── __init__.py
│   ├── security.py           # Password hash/verify; JWT create/decode
│   ├── dependencies.py       # get_current_user, require_role
│   └── exceptions.py         # AuthError, ForbiddenError; handlers in main
├── routers/
│   ├── __init__.py
│   ├── auth.py               # Login, refresh, me
│   ├── unsubscribe.py        # inbound-email, test-brevo, test-intent (protected)
│   ├── blocklist.py          # blocklist/* (protected)
│   └── worker.py             # worker/* (protected)
├── services/
│   ├── auth_service.py       # authenticate_user, create_token, log_activity
│   ├── activity_service.py   # log_activity(user_id, action, resource, details)
│   └── ... (existing)
└── docs/
    └── AUTH_AND_PROTECTED_UNSUBSCRIBE_IMPLEMENTATION_PLAN.md  # this file
```

---

## 11. Summary Checklist

- [ ] **Auth component:** Separate router + service + core (security, dependencies); JWT + password hashing; rate-limited login.  
- [ ] **User table:** email, hashed_password, role (admin/operator/viewer), is_active.  
- [ ] **Activity log:** user_id, action, resource, details, ip_address, created_at; log login and all protected actions.  
- [ ] **Unsubscribe logs:** Add `performed_by_user_id`; set when action is triggered by a logged-in user.  
- [ ] **APIs:** Public health; auth login/refresh/me; all unsubscribe/blocklist/worker behind JWT and role checks.  
- [ ] **Validation & errors:** Centralized exception handling; consistent 401/403/422/429/500.  
- [ ] **UX:** Bearer token in header; optional refresh; `/auth/me` for client state.  
- [ ] **Framework:** FastAPI with routers; auth and unsubscribe as separate components; existing services extended, not replaced.

This plan keeps the login feature as a separate component, maintains the current framework architecture, adds role-based access and activity logging, and ensures the unsubscribe feature is available only after user login with proper validation and error handling.
