from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db import get_db
from app.services.search_service import SearchService
from app.schemas.search_schemas import (
    SearchResumeRequest,
    SearchJobRequest,
    SearchResumeResponse,
    SearchJobResponse,
)

router = APIRouter(prefix="/api/trpc", tags=["search"])


@router.get("/search.resumes", response_model=SearchResumeResponse)
async def buscar_curriculos(
    q: str = Query(..., description="Palavra-chave para busca"),
    skills: Optional[str] = Query(
        None, description="Habilidades (separadas por vírgula)"
    ),
    experience_level: Optional[str] = Query(None, description="Nível de experiência"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    skills_list = None
    if skills:
        skills_list = [s.strip() for s in skills.split(",")]

    search_request = SearchResumeRequest(
        q=q,
        skills=skills_list,
        experience_level=experience_level,
        limit=limit,
        offset=offset,
    )

    service = SearchService(db)
    return await service.search_resumes(search_request)


@router.get("/search.jobs", response_model=SearchJobResponse)
async def buscar_vagas(
    q: str = Query(..., description="Palavra-chave para busca"),
    stack: Optional[str] = Query(None, description="Stack (separadas por vírgula)"),
    level: Optional[str] = Query(None, description="Nível da vaga"),
    location: Optional[str] = Query(None, description="Localização"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stack_list = None
    if stack:
        stack_list = [s.strip() for s in stack.split(",")]

    search_request = SearchJobRequest(
        q=q,
        stack=stack_list,
        level=level,
        location=location,
        limit=limit,
        offset=offset,
    )

    service = SearchService(db)
    return await service.search_jobs(search_request)
