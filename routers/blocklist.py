"""Protected blocklist endpoints: stats, list, search, recent, export, clear."""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import FileResponse

from core.dependencies import RequireAdmin, RequireViewer
from services.activity_service import ActivityService

router = APIRouter(prefix="/blocklist", tags=["blocklist"])


@router.get("/stats")
async def get_blocklist_stats(
    request: Request,
    current_user: RequireViewer,
):
    """Get blocklist statistics. Requires viewer, operator, or admin."""
    db_service = request.app.state.db_service
    activity: ActivityService = request.app.state.activity_service
    try:
        stats = db_service.get_blocklist_stats()
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="blocklist_stats",
            resource="blocklist",
            ip_address=ip,
        )
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting stats",
        )


@router.get("/all")
async def get_all_blocklisted(
    request: Request,
    current_user: RequireViewer,
    successful_only: bool = True,
):
    """Get all blocklisted emails. Requires viewer or higher."""
    db_service = request.app.state.db_service
    activity: ActivityService = request.app.state.activity_service
    try:
        emails = db_service.get_all_blocklisted_emails(successful_only=successful_only)
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="blocklist_all",
            resource="blocklist",
            details={"count": len(emails)},
            ip_address=ip,
        )
        return {"success": True, "count": len(emails), "emails": emails}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving blocklist",
        )


@router.get("/search/{email}")
async def search_blocklist(
    email: str,
    request: Request,
    current_user: RequireViewer,
):
    """Search blocklist by email. Requires viewer or higher."""
    db_service = request.app.state.db_service
    activity: ActivityService = request.app.state.activity_service
    try:
        results = db_service.search_by_email(email)
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="blocklist_search",
            resource="blocklist",
            details={"query": email, "count": len(results)},
            ip_address=ip,
        )
        return {"success": True, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching",
        )


@router.get("/recent")
async def get_recent_logs(
    request: Request,
    current_user: RequireViewer,
    limit: int = 50,
):
    """Get recent unsubscribe logs. Requires viewer or higher."""
    db_service = request.app.state.db_service
    activity: ActivityService = request.app.state.activity_service
    try:
        if limit > 500:
            limit = 500
        logs = db_service.get_recent_logs(limit=limit)
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="blocklist_recent",
            resource="blocklist",
            details={"limit": limit, "count": len(logs)},
            ip_address=ip,
        )
        return {"success": True, "count": len(logs), "logs": logs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving logs",
        )


@router.get("/export")
async def export_blocklist(
    request: Request,
    current_user: RequireAdmin,
    successful_only: bool = True,
):
    """Export blocklist to CSV. Requires admin."""
    db_service = request.app.state.db_service
    activity: ActivityService = request.app.state.activity_service
    try:
        filepath = db_service.export_to_csv(successful_only=successful_only)
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="blocklist_export",
            resource="blocklist",
            details={"successful_only": successful_only},
            ip_address=ip,
        )
        return FileResponse(
            path=filepath,
            media_type="text/csv",
            filename="blocklisted_emails.csv",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting",
        )


@router.post("/clear")
async def clear_blocklist(
    request: Request,
    current_user: RequireAdmin,
):
    """Clear all blocklist records. Destructive. Requires admin."""
    db_service = request.app.state.db_service
    activity: ActivityService = request.app.state.activity_service
    try:
        result = db_service.clear_all_logs()
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="blocklist_clear",
            resource="blocklist",
            details=result,
            ip_address=ip,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing database",
        )
