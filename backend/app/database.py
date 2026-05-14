import logging

from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine
# In production, this reads from DATABASE_URL in settings
engine = None


def get_engine():
    global engine
    if engine is None:
        try:
            engine = create_engine(
                settings.DATABASE_URL,
                pool_size=settings.DATABASE_POOL_SIZE,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                echo=settings.DATABASE_ECHO,
            )
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            # Fallback to SQLite for development/testing
            if settings.DEBUG:
                engine = create_engine(
                    "sqlite:///./test.db", connect_args={"check_same_thread": False}, echo=False
                )
            else:
                raise
    return engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

# Import all models to ensure they are registered before metadata operations
from app.models import BaseModel  # noqa: E402

Base = BaseModel


def get_db_session():
    """Dependency that provides a database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def drop_db():
    """Drop all database tables (use with caution)"""
    get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.info("All database tables dropped")
