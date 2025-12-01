from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    stack: Optional[List[str]] = None
    level: Optional[str] = Field(None, max_length=50)
    salary_range: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class JobUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    stack: Optional[List[str]] = None
    level: Optional[str] = Field(None, max_length=50)
    salary_range: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class JobResponse(BaseModel):
    job_id: int
    job_uuid: str
    user_id: int
    title: str
    company: Optional[str]
    location: Optional[str]
    description: str
    requirements: Optional[str]
    stack: Optional[List[str]]
    level: Optional[str]
    salary_range: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
    @validator("stack", pre=True)
    def parse_stack(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return []
        return v or []

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int

class JobFilterRequest(BaseModel):
    stack: Optional[str] = None
    level: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
