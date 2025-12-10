"""
ETPS Database Configuration

Supports SQLite (development) and PostgreSQL (production).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment, fallback to SQLite for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./etps.db")

# SQLAlchemy engine configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite requires check_same_thread=False for FastAPI
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL - no special connect_args needed
    # Railway uses postgres:// but SQLAlchemy 2.0 requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)

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
