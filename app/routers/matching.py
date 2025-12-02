from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core.dependencies import get_current_user
from app.services.matching_service import MatchingService
from app.schemas.matching_schemas import (
    MatchingResult,
    RecommendResumesResponse,
    RecommendJobsResponse
)

router = APIRouter(prefix="/api/trpc", tags=["matching"])

@router.post("/matching.analyze", response_model=MatchingResult)
async def analisar_compatibilidade(
    resume_id: int,
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = MatchingService(db)
    try:
        return await service.calculate_match(resume_id, job_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/matching.recommendResumes", response_model=RecommendResumesResponse)
async def recomendar_curriculos(
    job_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    min_score: float = Query(default=0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    service = MatchingService(db)
    try:
        return await service.recommend_resumes_for_job(job_id, limit, min_score)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/matching.recommendJobs", response_model=RecommendJobsResponse)
async def recomendar_vagas(
    resume_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    min_score: float = Query(default=0.5, ge=0.0, le=1.0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = MatchingService(db)
    try:
        return await service.recommend_jobs_for_resume(resume_id, limit, min_score)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
