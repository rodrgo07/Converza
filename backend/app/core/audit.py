import json
from typing import Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import AuditLog

def log_audit(
    db: Session,
    company_id: int,
    user_id: Optional[int],
    action: str,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Any] = None,
    ip_address: Optional[str] = None
):
    try:
        details_str = json.dumps(details, default=str) if isinstance(details, (dict, list)) else (str(details) if details else None)
        entry = AuditLog(
            company_id=company_id,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details_str,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc)
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()
