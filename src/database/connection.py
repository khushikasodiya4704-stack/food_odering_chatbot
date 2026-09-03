"""
Database connection and session management using SQLAlchemy.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import settings
from src.database.models import Base

# Engine configuration with thread safety for SQLite
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

# Set expire_on_commit=False to prevent DetachedInstanceError when objects are accessed outside the session scope
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
SessionLocal = scoped_session(SessionFactory)


def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Provide a transactional database session scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
