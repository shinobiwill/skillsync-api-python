from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core.dependencies import get_current_user
from app.services.job_service import JobService
from app.schemas.job_schemas import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobListResponse,
    JobFilterRequest
)

router = APIRouter(prefix="/api/trpc", tags=["jobs"])

@router.post("/jobs.create", response_model=JobResponse)
async def criar_vaga(
    dados: JobCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JobService(db)
    return await service.criar_vaga(
        user_id=current_user["user_id"],
        dados=dados
    )

@router.get("/jobs.get", response_model=JobResponse)
async def buscar_vaga(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = JobService(db)
    vaga = await service.buscar_por_id(job_id)
    
    if not vaga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vaga não encontrada"
        )
    
    return vaga

@router.put("/jobs.update", response_model=JobResponse)
async def atualizar_vaga(
    job_id: int,
    dados: JobUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JobService(db)
    return await service.atualizar_vaga(
        job_id=job_id,
        user_id=current_user["user_id"],
        dados=dados
    )

@router.delete("/jobs.delete")
async def excluir_vaga(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JobService(db)
    sucesso = await service.excluir_vaga(job_id, current_user["user_id"])
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vaga não encontrada"
        )
    
    return {"success": True, "message": "Vaga excluída com sucesso"}

@router.get("/jobs.list", response_model=JobListResponse)
async def listar_vagas(
    stack: str = None,
    level: str = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    filtros = JobFilterRequest(
        stack=stack,
        level=level,
        limit=limit,
        offset=offset
    )
    
    service = JobService(db)
    return await service.listar_vagas(filtros)
