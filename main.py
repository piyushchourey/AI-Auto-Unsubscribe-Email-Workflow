from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from models import InboundEmailRequest, UnsubscribeResponse, TestBrevoRequest
from services.intent_detector import IntentDetector
from services.brevo_service import BrevoService
from services.email_worker import EmailWorker
from services.email_sender import EmailSender
from services.graph_email_fetcher import GraphEmailFetcher
from services.database_service import DatabaseService
from database import init_db


# Initialize services
intent_detector = None
brevo_service = None
email_worker = None
db_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global intent_detector, brevo_service, email_worker, db_service
    
    print("🚀 Starting Unsubscribe Email Workflow API...")
    print(f"📡 LLM Provider: {settings.llm_provider}")
    
    # Initialize database
    print("🗄️ Initializing database...")
    init_db()
    
    # Initialize services
    intent_detector = IntentDetector()
    brevo_service = BrevoService()
    db_service = DatabaseService()
    
    print("✅ Services initialized successfully")
    
    # Initialize and start email worker
    if settings.imap_enabled:
        # Initialize the worker but do NOT start it automatically.
        # The Streamlit UI will call the /worker/start endpoint to start the worker on demand.
        email_worker = EmailWorker(intent_detector, brevo_service, db_service)
        print("⏸️ IMAP worker initialized but not started. Start via /worker/start endpoint")
    else:
        print("⏭️ IMAP worker disabled in configuration")
    
    yield
    
    # Cleanup on shutdown
    print("🛑 Shutting down...")
    if email_worker:
        await email_worker.stop()


# Create FastAPI app
app = FastAPI(
    title="Unsubscribe Email Workflow API",
    description="Automated unsubscribe processing system with LLM-based intent detection",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Unsubscribe Email Workflow API",
        "llm_provider": settings.llm_provider,
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    worker_status = email_worker.get_status() if email_worker else {'running': False, 'enabled': False}
    
    return {
        "status": "healthy",
        "services": {
            "intent_detector": "initialized" if intent_detector else "not initialized",
            "brevo_service": "initialized" if brevo_service else "not initialized",
            "email_worker": worker_status
        },
        "config": {
            "llm_provider": settings.llm_provider,
            "model": settings.ollama_model if settings.llm_provider == "ollama" else settings.gemini_model
        }
    }


@app.post("/inbound-email", response_model=UnsubscribeResponse, status_code=status.HTTP_200_OK)
async def process_inbound_email(request: InboundEmailRequest):
    """
    Process inbound email from Outlook Power Automate webhook
    
    This endpoint:
    1. Receives email sender and message text
    2. Uses LLM to detect unsubscribe intent
    3. If detected, automatically unsubscribes the contact in Brevo
    
    Args:
        request: InboundEmailRequest with sender_email and message_text
        
    Returns:
        UnsubscribeResponse with processing results
    """
    try:
        print(f"\n📧 Processing email from: {request.sender_email}")
        print(f"📝 Message preview: {request.message_text[:100]}...")
        
        # Step 1: Detect unsubscribe intent using LLM
        print("🤖 Analyzing intent with LLM...")
        intent_result = await intent_detector.detect_intent(request.message_text)
        
        print(f"🎯 Intent detected: {intent_result.has_unsubscribe_intent}")
        print(f"🎲 Confidence: {intent_result.confidence}")
        print(f"💭 Reasoning: {intent_result.reasoning}")

        # Step 2: If unsubscribe intent detected, process with Brevo
        unsubscribed_from_brevo = False
        brevo_details = None
        
        if intent_result.has_unsubscribe_intent:
            print(f"🚫 Unsubscribe intent detected! Processing with Brevo...")
            brevo_result = await brevo_service.unsubscribe_contact(request.sender_email)
            
            unsubscribed_from_brevo = brevo_result["success"]
            brevo_details = brevo_result
            
            if brevo_result["success"]:
                print(f"✅ Successfully unsubscribed {request.sender_email} from Brevo")
                # Optionally send confirmation email if configured
                reply_sent = False
                if settings.send_confirmation_email:
                    try:
                        # Prefer Graph API reply if configured and available; fallback to SMTP
                        if settings.use_graph_api:
                            # The webhook may not include a message_id, so fallback if missing
                            message_id = getattr(request, 'message_id', None)
                            if message_id:
                                fetcher = GraphEmailFetcher()
                                reply_sent = await fetcher.send_reply_email(
                                    message_id=message_id,
                                    recipient_email=request.sender_email,
                                    subject=request.subject or ''
                                )
                            else:
                                sender = EmailSender()
                                reply_sent = await sender.send_unsubscribe_confirmation(
                                    to_email=request.sender_email,
                                    original_subject=request.subject or ''
                                )
                        else:
                            sender = EmailSender()
                            reply_sent = await sender.send_unsubscribe_confirmation(
                                to_email=request.sender_email,
                                original_subject=request.subject or ''
                            )
                    except Exception as e:
                        print(f"❌ Failed to send confirmation email: {e}")
                else:
                    reply_sent = False
            else:
                print(f"⚠️ Failed to unsubscribe from Brevo: {brevo_result['message']}")
        else:
            print(f"ℹ️ No unsubscribe intent detected - no action taken")
        
        # Step 3: Log to database
        try:
            db_service.log_unsubscribe_action(
                email=request.sender_email,
                intent_detected=intent_result.has_unsubscribe_intent,
                brevo_success=unsubscribed_from_brevo,
                intent_confidence=intent_result.confidence,
                intent_reasoning=intent_result.reasoning,
                brevo_action=brevo_details.get("action") if brevo_details else None,
                brevo_message=brevo_details.get("message") if brevo_details else None,
                email_subject=request.subject,
                message_text=request.message_text,
                source="webhook"
            )
        except Exception as db_error:
            print(f"⚠️ Database logging failed: {str(db_error)}")
        
        # Build response
        return UnsubscribeResponse(
            success=True,
            message="Email processed successfully",
            sender_email=request.sender_email,
            unsubscribe_intent_detected=intent_result.has_unsubscribe_intent,
            unsubscribed_from_brevo=unsubscribed_from_brevo,
            details={
                "intent_confidence": intent_result.confidence,
                "intent_reasoning": intent_result.reasoning,
                "brevo_result": brevo_details,
                "reply_sent": reply_sent
            }
        )
        
    except Exception as e:
        print(f"❌ Error processing email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing email: {str(e)}"
        )


@app.post("/test-brevo")
async def test_brevo(request: TestBrevoRequest):
    """
    Test endpoint to blacklist an email in Brevo
    
    This endpoint allows you to test the Brevo API integration
    by directly blacklisting an email address without intent detection.
    
    Args:
        request: TestBrevoRequest with email to blacklist
        
    Returns:
        dict with Brevo API response details
    """
    try:
        print(f"\n🧪 Testing Brevo API for: {request.email}")
        
        # Call Brevo service to blacklist the contact
        result = await brevo_service.unsubscribe_contact(request.email)
        
        if result["success"]:
            print(f"✅ Successfully blacklisted {request.email} in Brevo")
        else:
            print(f"⚠️ Failed to blacklist: {result['message']}")
        
        return {
            "success": result["success"],
            "email": request.email,
            "message": result["message"],
            "action": result.get("action", "unknown"),
            "details": result
        }
        
    except Exception as e:
        print(f"❌ Error testing Brevo API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing Brevo API: {str(e)}"
        )


@app.post("/test-intent")
async def test_intent_detection(request: InboundEmailRequest):
    """
    Test endpoint to check intent detection without triggering Brevo unsubscribe
    Useful for testing the LLM intent detection in isolation
    """
    try:
        print(f"\n🧪 Testing intent detection for message: {request.message_text[:100]}...")
        
        intent_result = await intent_detector.detect_intent(request.message_text)
        
        return {
            "message_text": request.message_text,
            "has_unsubscribe_intent": intent_result.has_unsubscribe_intent,
            "confidence": intent_result.confidence,
            "reasoning": intent_result.reasoning
        }
        
    except Exception as e:
        print(f"❌ Error testing intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing intent: {str(e)}"
        )


@app.get("/worker/status")
async def get_worker_status():
    """
    Get the current status of the email worker
    """
    if not email_worker:
        return {
            "enabled": False,
            "running": False,
            "message": "Email worker not initialized"
        }
    
    return email_worker.get_status()


@app.post("/worker/check-now")
async def trigger_email_check():
    """
    Manually trigger an email check (useful for testing)
    """
    if not email_worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email worker not initialized"
        )
    
    if not settings.imap_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IMAP worker is disabled in configuration"
        )
    
    try:
        print("\n🔄 Manual email check triggered via API")
        await email_worker.check_emails()
        return {
            "success": True,
            "message": "Email check completed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking emails: {str(e)}"
        )


@app.post("/worker/start")
async def start_worker():
    """
    Start the email worker on demand. This does not restart the API server.
    """
    global email_worker

    if not settings.imap_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IMAP worker is disabled in configuration"
        )

    if not email_worker:
        email_worker = EmailWorker(intent_detector, brevo_service, db_service)

    try:
        await email_worker.start()
        return {"success": True, "message": "Email worker started"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting worker: {str(e)}"
        )


@app.post("/worker/stop")
async def stop_worker():
    """
    Stop the running email worker.
    """
    if not email_worker:
        return {"success": False, "message": "Email worker not initialized"}

    try:
        await email_worker.stop()
        return {"success": True, "message": "Email worker stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping worker: {str(e)}"
        )


# ========================================
# Database / Blocklist Endpoints
# ========================================

@app.get("/blocklist/stats")
async def get_blocklist_stats():
    """
    Get statistics about blocklisted emails
    """
    try:
        stats = db_service.get_blocklist_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stats: {str(e)}"
        )


@app.get("/blocklist/all")
async def get_all_blocklisted(successful_only: bool = True):
    """
    Get all blocklisted emails
    
    Query params:
        successful_only: If true, only return successfully blocklisted emails (default: true)
    """
    try:
        emails = db_service.get_all_blocklisted_emails(successful_only=successful_only)
        return {
            "success": True,
            "count": len(emails),
            "emails": emails
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving blocklist: {str(e)}"
        )


@app.get("/blocklist/search/{email}")
async def search_blocklist(email: str):
    """
    Search for a specific email in the blocklist
    """
    try:
        results = db_service.search_by_email(email)
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching: {str(e)}"
        )


@app.get("/blocklist/recent")
async def get_recent_logs(limit: int = 50):
    """
    Get recent unsubscribe logs
    
    Query params:
        limit: Maximum number of logs to return (default: 50, max: 500)
    """
    try:
        if limit > 500:
            limit = 500
        
        logs = db_service.get_recent_logs(limit=limit)
        return {
            "success": True,
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving logs: {str(e)}"
        )


@app.get("/blocklist/export")
async def export_blocklist(successful_only: bool = True):
    """
    Export blocklisted emails to CSV file
    
    Query params:
        successful_only: If true, only export successfully blocklisted emails (default: true)
    """
    try:
        filepath = db_service.export_to_csv(successful_only=successful_only)
        return FileResponse(
            path=filepath,
            media_type='text/csv',
            filename=f"blocklisted_emails.csv"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting: {str(e)}"
        )


@app.post("/blocklist/clear")
async def clear_blocklist():
    """
    Clear all blocklist records from the database (destructive operation)
    WARNING: This will permanently delete all unsubscribe logs!
    """
    try:
        result = db_service.clear_all_logs()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing database: {str(e)}"
        )


if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║     Unsubscribe Email Workflow API                            ║
║     Powered by FastAPI + LangChain + {settings.llm_provider.upper():8s}             ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
