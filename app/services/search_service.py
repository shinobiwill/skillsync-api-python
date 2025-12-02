from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func, text
from typing import List, Optional
import time
import json
import re

from app.models.models import Resume, ResumeVersion, Job
from app.schemas.search_schemas import (
    SearchResumeRequest,
    SearchJobRequest,
    SearchResultItem,
    SearchResumeResponse,
    SearchJobResponse
)

class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _normalize_query(self, query: str) -> str:
        query = query.lower().strip()
        query = re.sub(r'[^\w\s]', ' ', query)
        return ' '.join(query.split())
    
    def _extract_keywords(self, query: str) -> List[str]:
        normalized = self._normalize_query(query)
        keywords = [kw for kw in normalized.split() if len(kw) > 2]
        return keywords
    
    def _calculate_relevance_score(
        self, 
        text: str, 
        keywords: List[str]
    ) -> float:
        if not text or not keywords:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                score += count * (len(keyword) / 10.0)
        
        return min(score, 1.0)
    
    def _generate_highlights(
        self, 
        text: str, 
        keywords: List[str],
        max_highlights: int = 3
    ) -> List[str]:
        if not text or not keywords:
            return []
        
        highlights = []
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            pos = text_lower.find(keyword_lower)
            
            if pos != -1 and len(highlights) < max_highlights:
                start = max(0, pos - 50)
                end = min(len(text), pos + len(keyword) + 50)
                
                snippet = text[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                
                snippet = re.sub(
                    f"({re.escape(keyword)})",
                    r"**\1**",
                    snippet,
                    flags=re.IGNORECASE
                )
                
                highlights.append(snippet)
        
        return highlights
    
    async def search_resumes(
        self, 
        search_request: SearchResumeRequest
    ) -> SearchResumeResponse:
        start_time = time.time()
        
        keywords = self._extract_keywords(search_request.q)
        
        query = select(Resume).join(
            ResumeVersion,
            Resume.resume_id == ResumeVersion.resume_id
        )
        
        conditions = []
        for keyword in keywords:
            keyword_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    Resume.resume_title.ilike(keyword_pattern),
                    ResumeVersion.summary.ilike(keyword_pattern),
                    ResumeVersion.tags.ilike(keyword_pattern)
                )
            )
        
        if conditions:
            query = query.where(or_(*conditions))
        
        if search_request.skills:
            for skill in search_request.skills:
                query = query.where(
                    ResumeVersion.tags.ilike(f"%{skill}%")
                )
        
        query = query.distinct()
        
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(search_request.offset).limit(search_request.limit)
        
        result = await self.db.execute(query)
        resumes = result.scalars().all()
        
        search_results = []
        for resume in resumes:
            version_result = await self.db.execute(
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == resume.resume_id)
                .order_by(ResumeVersion.version_number.desc())
                .limit(1)
            )
            latest_version = version_result.scalar_one_or_none()
            
            full_text = f"{resume.resume_title} {latest_version.summary if latest_version else ''}"
            score = self._calculate_relevance_score(full_text, keywords)
            
            highlights = self._generate_highlights(full_text, keywords)
            
            search_results.append(SearchResultItem(
                id=resume.resume_id,
                title=resume.resume_title,
                summary=(latest_version.summary[:200] + "..." if latest_version and latest_version.summary else ""),
                score=score,
                highlights=highlights
            ))
        
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        execution_time = (time.time() - start_time) * 1000
        
        return SearchResumeResponse(
            results=search_results,
            total=total,
            query=search_request.q,
            execution_time_ms=round(execution_time, 2)
        )
    
    async def search_jobs(
        self, 
        search_request: SearchJobRequest
    ) -> SearchJobResponse:
        start_time = time.time()
        
        keywords = self._extract_keywords(search_request.q)
        
        query = select(Job).where(Job.is_active == True)
        
        conditions = []
        for keyword in keywords:
            keyword_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    Job.title.ilike(keyword_pattern),
                    Job.description.ilike(keyword_pattern),
                    Job.requirements.ilike(keyword_pattern),
                    Job.company.ilike(keyword_pattern)
                )
            )
        
        if conditions:
            query = query.where(or_(*conditions))
        
        if search_request.stack:
            for tech in search_request.stack:
                query = query.where(Job.stack.ilike(f"%{tech}%"))
        
        if search_request.level:
            query = query.where(Job.level == search_request.level)
        
        if search_request.location:
            query = query.where(
                Job.location.ilike(f"%{search_request.location}%")
            )
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(search_request.offset).limit(search_request.limit)
        
        result = await self.db.execute(query)
        jobs = result.scalars().all()
        
        search_results = []
        for job in jobs:
            full_text = f"{job.title} {job.description} {job.requirements or ''} {job.company or ''}"
            score = self._calculate_relevance_score(full_text, keywords)
            
            highlights = self._generate_highlights(full_text, keywords)
            
            search_results.append(SearchResultItem(
                id=job.job_id,
                title=job.title,
                summary=(job.description[:200] + "..." if job.description else ""),
                score=score,
                highlights=highlights
            ))
        
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        execution_time = (time.time() - start_time) * 1000
        
        return SearchJobResponse(
            results=search_results,
            total=total,
            query=search_request.q,
            execution_time_ms=round(execution_time, 2)
        )
