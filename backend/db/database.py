"""
ETPS Database Configuration

SQLite database setup for Phase 1-2.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL - stored in project root
DATABASE_URL = "sqlite:///./etps.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI endpoints to get a database session.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.

    Imports models to register them with SQLAlchemy metadata,
    then creates all tables in the database.
    """
    # Import models to register them with Base.metadata
    # Import inside function to avoid circular dependencies
    from db import models

    # Create all tables
    Base.metadata.create_all(bind=engine)
