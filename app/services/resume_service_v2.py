from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
import hashlib
import json
import uuid
from datetime import datetime

from app.models.models import Resume, ResumeVersion
from app.schemas.resume_schemas import (
    ResumeCreateRequest,
    ResumeUpdateRequest,
    ResumeResponse,
    ResumeVersionResponse,
    ResumeListResponse,
    ResumeVersionsListResponse
)

class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _gerar_storage_key(self, user_id: int, resume_uuid: str, version: int) -> str:
        return f"resumes/{user_id}/{resume_uuid}/v{version}"
    
    def _gerar_storage_url(self, storage_key: str) -> str:
        return f"https://storage.skillsync.app/{storage_key}"
    
    def _calcular_content_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
    
    async def criar_curriculo(
        self,
        user_id: int,
        dados: ResumeCreateRequest,
        arquivo: UploadFile
    ) -> ResumeResponse:
        conteudo_arquivo = await arquivo.read()
        tamanho_kb = len(conteudo_arquivo) // 1024
        content_hash = self._calcular_content_hash(conteudo_arquivo)
        
        novo_curriculo = Resume(
            user_id=user_id,
            resume_title=dados.resume_title,
            resume_hash=content_hash,
            blob_file_name=arquivo.filename,
            blob_file_size_kb=tamanho_kb,
            is_public=dados.is_public
        )
        
        self.db.add(novo_curriculo)
        await self.db.flush()
        
        storage_key = self._gerar_storage_key(user_id, novo_curriculo.resume_uuid, 1)
        storage_url = self._gerar_storage_url(storage_key)
        
        nova_versao = ResumeVersion(
            resume_id=novo_curriculo.resume_id,
            version_number=1,
            storage_key=storage_key,
            storage_url=storage_url,
            content_hash=content_hash,
            summary=dados.summary,
            tags=json.dumps(dados.tags) if dados.tags else None
        )
        
        self.db.add(nova_versao)
        novo_curriculo.blob_url = storage_url
        
        await self.db.commit()
        await self.db.refresh(novo_curriculo)
        
        result = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == novo_curriculo.resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        versao_atual = result.scalar_one_or_none()
        
        response = ResumeResponse.from_orm(novo_curriculo)
        if versao_atual:
            response.current_version = ResumeVersionResponse.from_orm(versao_atual)
        
        return response
    
    async def buscar_por_id(self, resume_id: int, user_id: int) -> Optional[ResumeResponse]:
        result = await self.db.execute(
            select(Resume)
            .where(
                and_(
                    Resume.resume_id == resume_id,
                    or_(Resume.user_id == user_id, Resume.is_public == True)
                )
            )
        )
        curriculo = result.scalar_one_or_none()
        
        if not curriculo:
            return None
        
        result_versao = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == curriculo.resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        versao_atual = result_versao.scalar_one_or_none()
        
        response = ResumeResponse.from_orm(curriculo)
        if versao_atual:
            response.current_version = ResumeVersionResponse.from_orm(versao_atual)
        
        return response
    
    async def atualizar_curriculo(
        self,
        resume_id: int,
        user_id: int,
        dados: ResumeUpdateRequest,
        arquivo: Optional[UploadFile] = None
    ) -> ResumeResponse:
        result = await self.db.execute(
            select(Resume).where(
                and_(Resume.resume_id == resume_id, Resume.user_id == user_id)
            )
        )
        curriculo = result.scalar_one_or_none()
        
        if not curriculo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currículo não encontrado"
            )
        
        precisa_nova_versao = False
        content_hash_novo = None
        
        if arquivo:
            conteudo_arquivo = await arquivo.read()
            content_hash_novo = self._calcular_content_hash(conteudo_arquivo)
            
            if content_hash_novo != curriculo.resume_hash:
                precisa_nova_versao = True
                curriculo.resume_hash = content_hash_novo
                curriculo.blob_file_name = arquivo.filename
                curriculo.blob_file_size_kb = len(conteudo_arquivo) // 1024
        
        if dados.summary is not None and arquivo is None:
            result_versao_atual = await self.db.execute(
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == curriculo.resume_id)
                .order_by(ResumeVersion.version_number.desc())
                .limit(1)
            )
            versao_atual = result_versao_atual.scalar_one_or_none()
            
            if versao_atual and versao_atual.summary != dados.summary:
                precisa_nova_versao = True
        
        if dados.resume_title is not None:
            curriculo.resume_title = dados.resume_title
        if dados.is_public is not None:
            curriculo.is_public = dados.is_public
        
        if precisa_nova_versao:
            result_ultima_versao = await self.db.execute(
                select(ResumeVersion.version_number)
                .where(ResumeVersion.resume_id == curriculo.resume_id)
                .order_by(ResumeVersion.version_number.desc())
                .limit(1)
            )
            ultima_versao = result_ultima_versao.scalar_one_or_none() or 0
            novo_numero_versao = ultima_versao + 1
            
            storage_key = self._gerar_storage_key(
                user_id,
                curriculo.resume_uuid,
                novo_numero_versao
            )
            storage_url = self._gerar_storage_url(storage_key)
            
            nova_versao = ResumeVersion(
                resume_id=curriculo.resume_id,
                version_number=novo_numero_versao,
                storage_key=storage_key,
                storage_url=storage_url,
                content_hash=content_hash_novo or curriculo.resume_hash,
                summary=dados.summary,
                tags=json.dumps(dados.tags) if dados.tags else None
            )
            
            self.db.add(nova_versao)
            curriculo.blob_url = storage_url
        
        await self.db.commit()
        await self.db.refresh(curriculo)
        
        return await self.buscar_por_id(curriculo.resume_id, user_id)
    
    async def excluir_curriculo(self, resume_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Resume).where(
                and_(Resume.resume_id == resume_id, Resume.user_id == user_id)
            )
        )
        curriculo = result.scalar_one_or_none()
        
        if not curriculo:
            return False
        
        await self.db.delete(curriculo)
        await self.db.commit()
        return True
    
    async def listar_por_usuario(self, user_id: int) -> ResumeListResponse:
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )
        curriculos = result.scalars().all()
        
        respostas = []
        for curriculo in curriculos:
            result_versao = await self.db.execute(
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == curriculo.resume_id)
                .order_by(ResumeVersion.version_number.desc())
                .limit(1)
            )
            versao_atual = result_versao.scalar_one_or_none()
            
            response = ResumeResponse.from_orm(curriculo)
            if versao_atual:
                response.current_version = ResumeVersionResponse.from_orm(versao_atual)
            respostas.append(response)
        
        return ResumeListResponse(resumes=respostas, total=len(respostas))
    
    async def listar_versoes(self, resume_id: int, user_id: int) -> ResumeVersionsListResponse:
        result = await self.db.execute(
            select(Resume).where(
                and_(
                    Resume.resume_id == resume_id,
                    or_(Resume.user_id == user_id, Resume.is_public == True)
                )
            )
        )
        curriculo = result.scalar_one_or_none()
        
        if not curriculo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currículo não encontrado"
            )
        
        result_versoes = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
        )
        versoes = result_versoes.scalars().all()
        
        versoes_response = [ResumeVersionResponse.from_orm(v) for v in versoes]
        
        return ResumeVersionsListResponse(versions=versoes_response, total=len(versoes_response))
