from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from core.exceptions import AuthError, ForbiddenError
from database import init_db
from seed_admin import seed_admin_if_empty
from services.intent_detector import IntentDetector
from services.brevo_service import BrevoService
from services.email_worker import EmailWorker
from services.database_service import DatabaseService
from services.activity_service import ActivityService
from routers import auth, unsubscribe, blocklist, worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database, seed admin if empty, and attach services to app.state."""
    print("🚀 Starting Unsubscribe Email Workflow API...")
    print(f"📡 LLM Provider: {settings.llm_provider}")

    print("🗄️ Initializing database...")
    init_db()
    seed_admin_if_empty()

    intent_detector = IntentDetector()
    brevo_service = BrevoService()
    db_service = DatabaseService()
    activity_service = ActivityService()

    app.state.intent_detector = intent_detector
    app.state.brevo_service = brevo_service
    app.state.db_service = db_service
    app.state.activity_service = activity_service
    app.state.email_worker = None

    if settings.imap_enabled:
        app.state.email_worker = EmailWorker(intent_detector, brevo_service, db_service)
        print("⏸️ IMAP worker initialized but not started. Start via /worker/start (requires auth)")
    else:
        print("⏭️ IMAP worker disabled in configuration")

    print("✅ Services initialized successfully")

    yield

    print("🛑 Shutting down...")
    if app.state.email_worker:
        await app.state.email_worker.stop()


app = FastAPI(
    title="Unsubscribe Email Workflow API",
    description="Automated unsubscribe processing with LLM-based intent detection. Protected endpoints require login.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception handlers for auth ---
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
    )


@app.exception_handler(ForbiddenError)
async def forbidden_error_handler(request: Request, exc: ForbiddenError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail},
    )


# --- Public (no auth) ---
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Unsubscribe Email Workflow API",
        "llm_provider": settings.llm_provider,
        "version": "1.0.0",
        "auth": "Login at POST /auth/login; use Bearer token for protected endpoints.",
    }


@app.get("/health")
async def health_check(request: Request):
    """Detailed health check."""
    worker = getattr(request.app.state, "email_worker", None)
    worker_status = worker.get_status() if worker else {"running": False, "enabled": False}
    intent_detector = getattr(request.app.state, "intent_detector", None)
    brevo_service = getattr(request.app.state, "brevo_service", None)
    return {
        "status": "healthy",
        "services": {
            "intent_detector": "initialized" if intent_detector else "not initialized",
            "brevo_service": "initialized" if brevo_service else "not initialized",
            "email_worker": worker_status,
        },
        "config": {
            "llm_provider": settings.llm_provider,
            "model": settings.ollama_model if settings.llm_provider == "ollama" else settings.gemini_model,
        },
    }


# --- Routers (protected) ---
app.include_router(auth.router)
app.include_router(unsubscribe.router)
app.include_router(blocklist.router)
app.include_router(worker.router)


if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║     Unsubscribe Email Workflow API                            ║
║     Powered by FastAPI + LangChain + {settings.llm_provider.upper():8s}             ║
║     Protected: login at POST /auth/login                       ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
