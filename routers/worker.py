"""Protected worker endpoints: status, check-now, start, stop."""
from fastapi import APIRouter, Request, HTTPException, status

from config import settings
from core.dependencies import RequireAdmin, RequireOperator, RequireViewer
from services.email_worker import EmailWorker
from services.activity_service import ActivityService

router = APIRouter(prefix="/worker", tags=["worker"])


@router.get("/status")
async def get_worker_status(
    request: Request,
    current_user: RequireViewer,
):
    """Get email worker status. Requires viewer or higher."""
    worker = request.app.state.email_worker
    if not worker:
        return {
            "enabled": False,
            "running": False,
            "message": "Email worker not initialized",
        }
    return worker.get_status()


@router.post("/check-now")
async def trigger_email_check(
    request: Request,
    current_user: RequireOperator,
):
    """Manually trigger an email check. Requires operator or admin."""
    worker = request.app.state.email_worker
    activity: ActivityService = request.app.state.activity_service
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email worker not initialized",
        )
    if not settings.imap_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IMAP worker is disabled in configuration",
        )
    try:
        print("\n🔄 Manual email check triggered via API")
        await worker.check_emails()
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="worker_check_now",
            resource="worker",
            ip_address=ip,
        )
        return {"success": True, "message": "Email check completed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking emails",
        )


@router.post("/start")
async def start_worker(
    request: Request,
    current_user: RequireAdmin,
):
    """Start the email worker. Requires admin."""
    activity: ActivityService = request.app.state.activity_service
    if not settings.imap_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IMAP worker is disabled in configuration",
        )
    worker = request.app.state.email_worker
    if not worker:
        worker = EmailWorker(
            request.app.state.intent_detector,
            request.app.state.brevo_service,
            request.app.state.db_service,
        )
        request.app.state.email_worker = worker
    try:
        await worker.start()
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="worker_start",
            resource="worker",
            ip_address=ip,
        )
        return {"success": True, "message": "Email worker started"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting worker",
        )


@router.post("/stop")
async def stop_worker(
    request: Request,
    current_user: RequireAdmin,
):
    """Stop the email worker. Requires admin."""
    worker = request.app.state.email_worker
    activity: ActivityService = request.app.state.activity_service
    if not worker:
        return {"success": False, "message": "Email worker not initialized"}
    try:
        await worker.stop()
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="worker_stop",
            resource="worker",
            ip_address=ip,
        )
        return {"success": True, "message": "Email worker stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error stopping worker",
        )
