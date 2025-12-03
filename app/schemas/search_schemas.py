from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SearchResumeRequest(BaseModel):
    q: str = Field(..., min_length=1, description="Palavra-chave para busca")
    skills: Optional[List[str]] = Field(None, description="Filtrar por habilidades")
    experience_level: Optional[str] = Field(None, description="Nível de experiência")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchJobRequest(BaseModel):
    q: str = Field(..., min_length=1, description="Palavra-chave para busca")
    stack: Optional[List[str]] = Field(None, description="Filtrar por stack")
    level: Optional[str] = Field(None, description="Nível da vaga")
    location: Optional[str] = Field(None, description="Localização")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResultItem(BaseModel):
    id: int
    title: str
    summary: str
    score: float
    highlights: List[str]


class SearchResumeResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    query: str
    execution_time_ms: float


class SearchJobResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    query: str
    execution_time_ms: float
