"""Seed default admin user if no users exist."""
from config import settings
from core.security import hash_password
from database import SessionLocal, User, init_db


def seed_admin_if_empty() -> bool:
    """
    If no users exist and ADMIN_SEED_EMAIL + ADMIN_SEED_PASSWORD are set,
    create an admin user. Returns True if a user was created.
    """
    if not settings.admin_seed_email or not settings.admin_seed_password:
        return False
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return False
        user = User(
            email=settings.admin_seed_email.strip().lower(),
            hashed_password=hash_password(settings.admin_seed_password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"✅ Seeded admin user: {user.email}")
        return True
    except Exception as e:
        db.rollback()
        print(f"⚠️ Seed admin failed: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    """Run from CLI to seed admin user (reads from .env)."""
    print("Initializing database...")
    init_db()
    if seed_admin_if_empty():
        print("Done. You can now log in with ADMIN_SEED_EMAIL and ADMIN_SEED_PASSWORD.")
    else:
        if not settings.admin_seed_email or not settings.admin_seed_password:
            print("Set ADMIN_SEED_EMAIL and ADMIN_SEED_PASSWORD in .env and run again.")
        else:
            print("No user created (users already exist or seed failed).")
