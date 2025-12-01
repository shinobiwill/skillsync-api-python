# models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, BigInteger, Text
from sqlalchemy.orm import relationship, declarative_base
import datetime, uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "tb_users"
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    display_name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # relations
    settings = relationship("UserSettings", back_populates="user", uselist=False)

class UserSettings(Base):
    __tablename__ = "tb_settings"
    settings_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("tb_users.user_id"), nullable=False)
    language_code = Column(String(10))
    timezone = Column(String(50))
    user = relationship("User", back_populates="settings")

class Resume(Base):
    __tablename__ = "tb_resumes"
    resume_id = Column(BigInteger, primary_key=True, autoincrement=True)
    resume_uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("tb_users.user_id"), nullable=False)
    resume_hash = Column(String(128))
    resume_title = Column(String(255))
    blob_url = Column(Text)
    blob_file_name = Column(String(255))
    blob_file_size_kb = Column(Integer)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")

class ResumeVersion(Base):
    __tablename__ = "tb_resume_versions"
    version_id = Column(BigInteger, primary_key=True, autoincrement=True)
    resume_id = Column(BigInteger, ForeignKey("tb_resumes.resume_id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    storage_key = Column(String(255), nullable=False)
    storage_url = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    summary = Column(Text)
    tags = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resume = relationship("Resume", back_populates="versions")

class Job(Base):
    __tablename__ = "tb_jobs"
    job_id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("tb_users.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255))
    location = Column(String(255))
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    stack = Column(Text)
    level = Column(String(50))
    salary_range = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
