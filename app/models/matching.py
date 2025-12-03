from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
import datetime

from app.db import Base


class Match(Base):
    __tablename__ = "tb_matches"

    match_id = Column(BigInteger, primary_key=True, autoincrement=True)
    resume_id = Column(BigInteger, ForeignKey("tb_resumes.resume_id"), nullable=False)
    job_id = Column(BigInteger, ForeignKey("tb_jobs.job_id"), nullable=False)

    overall_score = Column(Float, nullable=False)
    skills_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    level_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)

    matched_skills = Column(Text)
    missing_skills = Column(Text)
    extra_skills = Column(Text)

    recommendations = Column(Text)
    strengths = Column(Text)
    weaknesses = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    resume = relationship("Resume", foreign_keys=[resume_id])
    job = relationship("Job", foreign_keys=[job_id])
