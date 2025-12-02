from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MatchingAnalyzeRequest(BaseModel):
    resume_id: int
    job_id: int

class SkillMatch(BaseModel):
    skill: str
    matched: bool
    importance: str

class MatchingResult(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Score geral (0-1)")
    skills_score: float = Field(..., ge=0.0, le=1.0)
    experience_score: float = Field(..., ge=0.0, le=1.0)
    level_score: float = Field(..., ge=0.0, le=1.0)
    education_score: float = Field(..., ge=0.0, le=1.0)
    
    matched_skills: List[str]
    missing_skills: List[str]
    extra_skills: List[str]
    
    recommendations: List[str]
    strengths: List[str]
    weaknesses: List[str]
    
    resume_id: int
    job_id: int
    analyzed_at: datetime

class ResumeMatchItem(BaseModel):
    resume_id: int
    resume_title: str
    score: float
    matched_skills: List[str]
    missing_skills: List[str]
    summary: Optional[str]

class JobMatchItem(BaseModel):
    job_id: int
    job_title: str
    company: Optional[str]
    score: float
    matched_skills: List[str]
    missing_skills: List[str]
    description_preview: str

class RecommendResumesResponse(BaseModel):
    job_id: int
    job_title: str
    matches: List[ResumeMatchItem]
    total: int

class RecommendJobsResponse(BaseModel):
    resume_id: int
    resume_title: str
    matches: List[JobMatchItem]
    total: int
