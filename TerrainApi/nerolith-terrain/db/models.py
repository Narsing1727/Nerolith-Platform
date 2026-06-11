from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    key_hash = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    tier = Column(String, default="free")
    calls_this_month = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=True)
    status = Column(String, default="queued")
    stage = Column(String, nullable=True)
    percent = Column(Integer, default=0)
    bbox = Column(String, nullable=True)
    layers = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    confidence_mean = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class WaitlistEmail(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    use_case = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)