"""
Database module for tracking unsubscribe/blocklist history
Uses SQLite for lightweight, file-based storage
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path

# Create database directory if it doesn't exist
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

# Database file path
DATABASE_URL = f"sqlite:///{DB_DIR}/unsubscribe_history.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class UnsubscribeLog(Base):
    """Model for tracking unsubscribe/blocklist actions"""
    __tablename__ = "unsubscribe_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    
    # Intent detection details
    intent_detected = Column(Boolean, nullable=False)
    intent_confidence = Column(String, nullable=True)
    intent_reasoning = Column(Text, nullable=True)
    
    # Brevo action details
    brevo_success = Column(Boolean, nullable=False)
    brevo_action = Column(String, nullable=True)  # 'created', 'updated', 'failed'
    brevo_message = Column(Text, nullable=True)
    
    # Email metadata
    email_subject = Column(String, nullable=True)
    email_snippet = Column(Text, nullable=True)  # First 200 chars of message
    
    # Source information
    source = Column(String, nullable=False)  # 'webhook', 'worker', 'manual'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "intent_detected": self.intent_detected,
            "intent_confidence": self.intent_confidence,
            "intent_reasoning": self.intent_reasoning,
            "brevo_success": self.brevo_success,
            "brevo_action": self.brevo_action,
            "brevo_message": self.brevo_message,
            "email_subject": self.email_subject,
            "email_snippet": self.email_snippet,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def init_db():
    """Initialize database - create tables if they don't exist"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
