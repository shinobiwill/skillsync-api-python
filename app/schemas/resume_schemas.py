from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ResumeCreateRequest(BaseModel):
    resume_title: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False

class ResumeUpdateRequest(BaseModel):
    resume_title: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

class ResumeVersionResponse(BaseModel):
    version_id: int
    version_number: int
    storage_key: str
    storage_url: str
    content_hash: str
    summary: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True
    
    @validator("tags", pre=True)
    def parse_tags(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return []
        return v or []

class ResumeResponse(BaseModel):
    resume_id: int
    resume_uuid: str
    user_id: int
    resume_title: str
    resume_hash: Optional[str]
    blob_url: Optional[str]
    blob_file_name: Optional[str]
    blob_file_size_kb: Optional[int]
    is_public: bool
    created_at: datetime
    current_version: Optional[ResumeVersionResponse] = None

    class Config:
        from_attributes = True

class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total: int

class ResumeVersionsListResponse(BaseModel):
    versions: List[ResumeVersionResponse]
    total: int
