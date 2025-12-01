from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from app.db import get_db
from app.core.dependencies import get_current_user
from app.services.resume_service_v2 import ResumeService
from app.schemas.resume_schemas import (
    ResumeCreateRequest,
    ResumeUpdateRequest,
    ResumeResponse,
    ResumeListResponse,
    ResumeVersionsListResponse
)

router = APIRouter(prefix="/api/trpc", tags=["resumes"])

@router.post("/resumes.create", response_model=ResumeResponse)
async def criar_curriculo(
    file: UploadFile = File(...),
    resume_title: str = Form(...),
    summary: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_public: bool = Form(False),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
        except:
            tags_list = [t.strip() for t in tags.split(",")]
    
    dados = ResumeCreateRequest(
        resume_title=resume_title,
        summary=summary,
        tags=tags_list,
        is_public=is_public
    )
    
    service = ResumeService(db)
    return await service.criar_curriculo(
        user_id=current_user["user_id"],
        dados=dados,
        arquivo=file
    )

@router.get("/resumes.get", response_model=ResumeResponse)
async def buscar_curriculo(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    curriculo = await service.buscar_por_id(resume_id, current_user["user_id"])
    
    if not curriculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currículo não encontrado"
        )
    
    return curriculo

@router.put("/resumes.update", response_model=ResumeResponse)
async def atualizar_curriculo(
    resume_id: int,
    file: Optional[UploadFile] = File(None),
    resume_title: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_public: Optional[bool] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
        except:
            tags_list = [t.strip() for t in tags.split(",")]
    
    dados = ResumeUpdateRequest(
        resume_title=resume_title,
        summary=summary,
        tags=tags_list,
        is_public=is_public
    )
    
    service = ResumeService(db)
    return await service.atualizar_curriculo(
        resume_id=resume_id,
        user_id=current_user["user_id"],
        dados=dados,
        arquivo=file
    )

@router.delete("/resumes.delete")
async def excluir_curriculo(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    sucesso = await service.excluir_curriculo(resume_id, current_user["user_id"])
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currículo não encontrado"
        )
    
    return {"success": True, "message": "Currículo excluído com sucesso"}

@router.get("/resumes.listByUser", response_model=ResumeListResponse)
async def listar_curriculos_usuario(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    return await service.listar_por_usuario(current_user["user_id"])

@router.get("/resumes.getVersions", response_model=ResumeVersionsListResponse)
async def listar_versoes_curriculo(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    return await service.listar_versoes(resume_id, current_user["user_id"])
