"""
Database service for logging unsubscribe actions
"""
from sqlalchemy.orm import Session
from database import UnsubscribeLog, SessionLocal
from datetime import datetime
from typing import List, Optional, Dict
import csv
from pathlib import Path


class DatabaseService:
    """Service for managing unsubscribe logs in database"""
    
    def __init__(self):
        """Initialize database service"""
        pass
    
    def log_unsubscribe_action(
        self,
        email: str,
        intent_detected: bool,
        brevo_success: bool,
        intent_confidence: Optional[str] = None,
        intent_reasoning: Optional[str] = None,
        brevo_action: Optional[str] = None,
        brevo_message: Optional[str] = None,
        email_subject: Optional[str] = None,
        message_text: Optional[str] = None,
        source: str = "webhook"
    ) -> UnsubscribeLog:
        """
        Log an unsubscribe action to the database
        
        Args:
            email: Email address that was processed
            intent_detected: Whether unsubscribe intent was detected
            brevo_success: Whether Brevo API call was successful
            intent_confidence: Confidence level (high/medium/low)
            intent_reasoning: LLM reasoning for the decision
            brevo_action: Brevo action taken (created/updated/failed)
            brevo_message: Message from Brevo API
            email_subject: Subject of the email
            message_text: Email message text (will be truncated)
            source: Source of the request (webhook/worker/manual)
            
        Returns:
            UnsubscribeLog: The created log entry
        """
        db = SessionLocal()
        try:
            # Create snippet from message text (first 200 chars)
            email_snippet = None
            if message_text:
                email_snippet = message_text[:200] + "..." if len(message_text) > 200 else message_text
            
            # Create log entry
            log_entry = UnsubscribeLog(
                email=email,
                intent_detected=intent_detected,
                intent_confidence=intent_confidence,
                intent_reasoning=intent_reasoning,
                brevo_success=brevo_success,
                brevo_action=brevo_action,
                brevo_message=brevo_message,
                email_subject=email_subject,
                email_snippet=email_snippet,
                source=source,
                created_at=datetime.utcnow()
            )
            
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            print(f"📝 Logged unsubscribe action for {email} (ID: {log_entry.id})")
            return log_entry
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error logging to database: {str(e)}")
            raise
        finally:
            db.close()
    
    def get_all_blocklisted_emails(self, successful_only: bool = True) -> List[Dict]:
        """
        Get all blocklisted emails from the database
        
        Args:
            successful_only: If True, only return successfully blocklisted emails
            
        Returns:
            List of dictionaries containing email data
        """
        db = SessionLocal()
        try:
            query = db.query(UnsubscribeLog)
            
            if successful_only:
                query = query.filter(
                    UnsubscribeLog.intent_detected == True,
                    UnsubscribeLog.brevo_success == True
                )
            
            logs = query.order_by(UnsubscribeLog.created_at.desc()).all()
            return [log.to_dict() for log in logs]
            
        finally:
            db.close()
    
    def get_blocklist_stats(self) -> Dict:
        """
        Get statistics about blocklisted emails
        
        Returns:
            Dictionary with various statistics
        """
        db = SessionLocal()
        try:
            total_logs = db.query(UnsubscribeLog).count()
            
            intent_detected = db.query(UnsubscribeLog).filter(
                UnsubscribeLog.intent_detected == True
            ).count()
            
            successfully_blocklisted = db.query(UnsubscribeLog).filter(
                UnsubscribeLog.intent_detected == True,
                UnsubscribeLog.brevo_success == True
            ).count()
            
            failed_blocklist = db.query(UnsubscribeLog).filter(
                UnsubscribeLog.intent_detected == True,
                UnsubscribeLog.brevo_success == False
            ).count()
            
            # Get breakdown by source
            from sqlalchemy import func
            source_breakdown = db.query(
                UnsubscribeLog.source,
                func.count(UnsubscribeLog.id)
            ).group_by(UnsubscribeLog.source).all()
            
            return {
                "total_processed": total_logs,
                "intent_detected_count": intent_detected,
                "successfully_blocklisted": successfully_blocklisted,
                "failed_blocklist": failed_blocklist,
                "no_intent_detected": total_logs - intent_detected,
                "source_breakdown": {source: count for source, count in source_breakdown}
            }
            
        finally:
            db.close()
    
    def search_by_email(self, email: str) -> List[Dict]:
        """
        Search for logs by email address
        
        Args:
            email: Email address to search for
            
        Returns:
            List of matching log entries
        """
        db = SessionLocal()
        try:
            logs = db.query(UnsubscribeLog).filter(
                UnsubscribeLog.email.like(f"%{email}%")
            ).order_by(UnsubscribeLog.created_at.desc()).all()
            
            return [log.to_dict() for log in logs]
            
        finally:
            db.close()
    
    def export_to_csv(self, filepath: Optional[str] = None, successful_only: bool = True) -> str:
        """
        Export blocklisted emails to CSV file
        
        Args:
            filepath: Path to save CSV file (auto-generated if None)
            successful_only: If True, only export successfully blocklisted emails
            
        Returns:
            Path to the created CSV file
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            exports_dir = Path("exports")
            exports_dir.mkdir(exist_ok=True)
            filepath = f"exports/blocklisted_emails_{timestamp}.csv"
        
        logs = self.get_all_blocklisted_emails(successful_only=successful_only)
        
        # Define CSV columns
        fieldnames = [
            'id', 'email', 'intent_detected', 'intent_confidence',
            'brevo_success', 'brevo_action', 'email_subject',
            'source', 'created_at'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in logs:
                # Only write selected fields
                row = {k: log.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        print(f"📊 Exported {len(logs)} records to {filepath}")
        return filepath
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """
        Get most recent unsubscribe logs
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of recent log entries
        """
        db = SessionLocal()
        try:
            logs = db.query(UnsubscribeLog).order_by(
                UnsubscribeLog.created_at.desc()
            ).limit(limit).all()
            
            return [log.to_dict() for log in logs]
            
        finally:
            db.close()
