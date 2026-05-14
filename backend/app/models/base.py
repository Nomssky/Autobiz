import uuid

from sqlalchemy import JSON, Column, DateTime, String, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# Helper function to generate UUID
def generate_uuid():
    return str(uuid.uuid4())


class JSONB(TypeDecorator):
    """Cross-dialect JSONB that uses JSON on SQLite native JSON."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(JSON())
        from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB

        return dialect.type_descriptor(PG_JSONB())


class GUID(TypeDecorator):
    """Cross-dialect GUID type."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(36))
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID

        return dialect.type_descriptor(PG_UUID(as_uuid=True))

    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name == "sqlite":
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and dialect.name == "sqlite":
            return str(value)
        return value


class BaseModel(Base):
    __abstract__ = True

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
