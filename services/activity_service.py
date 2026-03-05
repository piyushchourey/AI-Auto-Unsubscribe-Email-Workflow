"""Service for recording user activity (audit log)."""
from datetime import datetime
from typing import Any, Optional

from database import ActivityLog, SessionLocal


class ActivityService:
    """Logs who performed which action for audit trail."""

    def log(
        self,
        user_id: Optional[int],
        action: str,
        resource: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> ActivityLog:
        """Record an activity entry."""
        db = SessionLocal()
        try:
            import json
            details_str = json.dumps(details) if details is not None else None
            entry = ActivityLog(
                user_id=user_id,
                action=action,
                resource=resource,
                details=details_str,
                ip_address=ip_address,
                created_at=datetime.utcnow(),
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
