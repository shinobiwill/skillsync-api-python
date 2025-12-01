from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, List
from fastapi import HTTPException, status
import json
from datetime import datetime

from app.models.models import Job
from app.schemas.job_schemas import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobListResponse,
    JobFilterRequest
)

class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def criar_vaga(
        self,
        user_id: int,
        dados: JobCreateRequest
    ) -> JobResponse:
        nova_vaga = Job(
            user_id=user_id,
            title=dados.title,
            company=dados.company,
            location=dados.location,
            description=dados.description,
            requirements=dados.requirements,
            stack=json.dumps(dados.stack) if dados.stack else None,
            level=dados.level,
            salary_range=dados.salary_range,
            is_active=dados.is_active
        )
        
        self.db.add(nova_vaga)
        await self.db.commit()
        await self.db.refresh(nova_vaga)
        
        return JobResponse.from_orm(nova_vaga)
    
    async def buscar_por_id(self, job_id: int) -> Optional[JobResponse]:
        result = await self.db.execute(
            select(Job).where(Job.job_id == job_id)
        )
        vaga = result.scalar_one_or_none()
        
        if not vaga:
            return None
        
        return JobResponse.from_orm(vaga)
    
    async def atualizar_vaga(
        self,
        job_id: int,
        user_id: int,
        dados: JobUpdateRequest
    ) -> JobResponse:
        result = await self.db.execute(
            select(Job).where(
                and_(Job.job_id == job_id, Job.user_id == user_id)
            )
        )
        vaga = result.scalar_one_or_none()
        
        if not vaga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vaga não encontrada"
            )
        
        if dados.title is not None:
            vaga.title = dados.title
        if dados.company is not None:
            vaga.company = dados.company
        if dados.location is not None:
            vaga.location = dados.location
        if dados.description is not None:
            vaga.description = dados.description
        if dados.requirements is not None:
            vaga.requirements = dados.requirements
        if dados.stack is not None:
            vaga.stack = json.dumps(dados.stack)
        if dados.level is not None:
            vaga.level = dados.level
        if dados.salary_range is not None:
            vaga.salary_range = dados.salary_range
        if dados.is_active is not None:
            vaga.is_active = dados.is_active
        
        vaga.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(vaga)
        
        return JobResponse.from_orm(vaga)
    
    async def excluir_vaga(self, job_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Job).where(
                and_(Job.job_id == job_id, Job.user_id == user_id)
            )
        )
        vaga = result.scalar_one_or_none()
        
        if not vaga:
            return False
        
        await self.db.delete(vaga)
        await self.db.commit()
        return True
    
    async def listar_vagas(self, filtros: JobFilterRequest) -> JobListResponse:
        query = select(Job).where(Job.is_active == True)
        
        if filtros.stack:
            query = query.where(Job.stack.contains(filtros.stack))
        
        if filtros.level:
            query = query.where(Job.level == filtros.level)
        
        query = query.order_by(Job.created_at.desc())
        query = query.offset(filtros.offset).limit(filtros.limit)
        
        result = await self.db.execute(query)
        vagas = result.scalars().all()
        
        count_query = select(Job).where(Job.is_active == True)
        if filtros.stack:
            count_query = count_query.where(Job.stack.contains(filtros.stack))
        if filtros.level:
            count_query = count_query.where(Job.level == filtros.level)
        
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        
        vagas_response = [JobResponse.from_orm(v) for v in vagas]
        
        return JobListResponse(jobs=vagas_response, total=total)
