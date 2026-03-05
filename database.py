"""
Database module for tracking unsubscribe/blocklist history and users.
Uses SQLite for lightweight, file-based storage.
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
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


class User(Base):
    """User model for authentication and role-based access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="operator")  # admin, operator, viewer
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(Base):
    """Audit log for who performed which action."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


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
    performed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

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
            "performed_by_user_id": self.performed_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def _migrate_add_performed_by_user_id():
    """Add performed_by_user_id to unsubscribe_logs if missing (for existing DBs)."""
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(unsubscribe_logs)"))
        columns = [row[1] for row in result.fetchall()]
        if "performed_by_user_id" not in columns:
            conn.execute(text(
                "ALTER TABLE unsubscribe_logs ADD COLUMN performed_by_user_id INTEGER"
            ))
            conn.commit()
            print("✅ Migrated: added performed_by_user_id to unsubscribe_logs")


def init_db():
    """Initialize database - create tables if they don't exist, then run migrations."""
    Base.metadata.create_all(bind=engine)
    _migrate_add_performed_by_user_id()
    print("✅ Database initialized successfully")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
