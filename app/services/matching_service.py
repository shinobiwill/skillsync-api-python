from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Set, Tuple
import json
import re
from datetime import datetime

from app.models.models import Resume, ResumeVersion, Job
from app.models.matching import Match
from app.schemas.matching_schemas import (
    MatchingResult,
    ResumeMatchItem,
    JobMatchItem,
    RecommendResumesResponse,
    RecommendJobsResponse,
)


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db

        self.SKILLS_WEIGHT = 0.40
        self.EXPERIENCE_WEIGHT = 0.30
        self.LEVEL_WEIGHT = 0.20
        self.EDUCATION_WEIGHT = 0.10

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        return " ".join(text.split())

    def _extract_skills(self, text: str, tags_json: str = None) -> Set[str]:
        skills = set()

        if tags_json:
            try:
                tags = json.loads(tags_json)
                if isinstance(tags, list):
                    skills.update([self._normalize_text(t) for t in tags])
            except:
                pass

        text_normalized = self._normalize_text(text)

        common_skills = [
            "python",
            "java",
            "javascript",
            "typescript",
            "nodejs",
            "react",
            "angular",
            "vue",
            "fastapi",
            "django",
            "flask",
            "spring",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "git",
            "sql",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "linux",
            "windows",
            "ci/cd",
            "devops",
            "agile",
            "scrum",
            "rest api",
            "graphql",
            "microservices",
            "machine learning",
            "data science",
            "cybersecurity",
            "pentesting",
            "siem",
            "qradar",
            "wireshark",
            "nmap",
            "nessus",
            "iso 27001",
            "lgpd",
            "gdpr",
            "firewall",
            "vpn",
            "criptografia",
            "forense digital",
        ]

        for skill in common_skills:
            if skill in text_normalized:
                skills.add(skill)

        return skills

    def _calculate_skills_score(
        self, resume_skills: Set[str], job_skills: Set[str]
    ) -> Tuple[float, List[str], List[str], List[str]]:
        if not job_skills:
            return 0.5, [], [], list(resume_skills)

        matched = resume_skills & job_skills
        missing = job_skills - resume_skills
        extra = resume_skills - job_skills

        score = len(matched) / len(job_skills) if job_skills else 0.0

        return (min(score, 1.0), list(matched), list(missing), list(extra))

    def _calculate_experience_score(
        self, resume_text: str, job_requirements: str
    ) -> float:
        if not job_requirements:
            return 0.5

        resume_lower = resume_text.lower()
        requirements_lower = job_requirements.lower()

        score = 0.0

        years_match_resume = re.search(r"(\d+)\s*(?:anos?|years?)", resume_lower)
        years_match_job = re.search(r"(\d+)\s*(?:\+|anos?|years?)", requirements_lower)

        if years_match_resume and years_match_job:
            resume_years = int(years_match_resume.group(1))
            job_years = int(years_match_job.group(1))

            if resume_years >= job_years:
                score = 1.0
            else:
                score = resume_years / job_years
        else:
            score = 0.5

        experience_keywords = ["experiência", "experience", "atuação", "trabalho"]
        for keyword in experience_keywords:
            if keyword in resume_lower:
                score += 0.1

        return min(score, 1.0)

    def _calculate_level_score(self, resume_text: str, job_level: str) -> float:
        if not job_level:
            return 0.5

        level_mapping = {
            "junior": ["junior", "júnior", "estagiário", "estagiario", "trainee"],
            "pleno": ["pleno", "mid", "middle", "intermediário", "intermediario"],
            "senior": ["senior", "sênior", "especialista", "líder", "lider", "lead"],
        }

        resume_lower = resume_text.lower()
        job_level_lower = job_level.lower()

        if job_level_lower in level_mapping:
            for keyword in level_mapping[job_level_lower]:
                if keyword in resume_lower:
                    return 1.0

        if "supervisor" in resume_lower or "coordenador" in resume_lower:
            if job_level_lower in ["senior", "pleno"]:
                return 0.8

        return 0.5

    def _calculate_education_score(
        self, resume_text: str, job_requirements: str
    ) -> float:
        if not job_requirements:
            return 0.5

        resume_lower = resume_text.lower()
        requirements_lower = job_requirements.lower()

        education_levels = {
            "doutorado": 5,
            "phd": 5,
            "mestrado": 4,
            "mestre": 4,
            "pós-graduação": 3,
            "pós-graduacao": 3,
            "especialização": 3,
            "especializacao": 3,
            "graduação": 2,
            "graduacao": 2,
            "tecnólogo": 2,
            "tecnologo": 2,
            "bacharelado": 2,
            "técnico": 1,
            "tecnico": 1,
        }

        resume_level = 0
        job_level = 0

        for edu, level in education_levels.items():
            if edu in resume_lower:
                resume_level = max(resume_level, level)
            if edu in requirements_lower:
                job_level = max(job_level, level)

        if job_level == 0:
            return 0.5

        if resume_level >= job_level:
            return 1.0
        elif resume_level == job_level - 1:
            return 0.7
        else:
            return 0.3

    def _generate_recommendations(
        self,
        missing_skills: List[str],
        skills_score: float,
        experience_score: float,
        level_score: float,
    ) -> List[str]:
        recommendations = []

        if skills_score < 0.6 and missing_skills:
            top_missing = missing_skills[:3]
            recommendations.append(
                f"Recomenda-se desenvolver as seguintes habilidades: {', '.join(top_missing)}"
            )

        if experience_score < 0.6:
            recommendations.append(
                "Buscar projetos ou experiências adicionais para fortalecer o perfil"
            )

        if level_score < 0.6:
            recommendations.append(
                "Destacar experiências de liderança e responsabilidades no currículo"
            )

        if not recommendations:
            recommendations.append(
                "Perfil muito bem alinhado com a vaga. Continue aprimorando suas habilidades!"
            )

        return recommendations

    def _identify_strengths(
        self, matched_skills: List[str], skills_score: float, experience_score: float
    ) -> List[str]:
        strengths = []

        if skills_score >= 0.7:
            strengths.append(
                f"Forte alinhamento de habilidades técnicas ({len(matched_skills)} skills compatíveis)"
            )

        if experience_score >= 0.7:
            strengths.append("Experiência profissional adequada para a vaga")

        if matched_skills:
            top_skills = matched_skills[:3]
            strengths.append(f"Domínio em: {', '.join(top_skills)}")

        return strengths if strengths else ["Perfil em desenvolvimento"]

    def _identify_weaknesses(
        self, missing_skills: List[str], skills_score: float, experience_score: float
    ) -> List[str]:
        weaknesses = []

        if skills_score < 0.5 and missing_skills:
            top_missing = missing_skills[:3]
            weaknesses.append(f"Gap de habilidades: {', '.join(top_missing)}")

        if experience_score < 0.5:
            weaknesses.append("Experiência profissional abaixo do esperado")

        return (
            weaknesses
            if weaknesses
            else ["Nenhuma fraqueza significativa identificada"]
        )

    async def calculate_match(self, resume_id: int, job_id: int) -> MatchingResult:
        resume_result = await self.db.execute(
            select(Resume).where(Resume.resume_id == resume_id)
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise ValueError("Currículo não encontrado")

        version_result = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        resume_version = version_result.scalar_one_or_none()

        job_result = await self.db.execute(select(Job).where(Job.job_id == job_id))
        job = job_result.scalar_one_or_none()

        if not job:
            raise ValueError("Vaga não encontrada")

        resume_text = (
            f"{resume.resume_title} {resume_version.summary if resume_version else ''}"
        )
        resume_skills = self._extract_skills(
            resume_text, resume_version.tags if resume_version else None
        )

        job_text = f"{job.title} {job.description} {job.requirements or ''}"
        job_skills = self._extract_skills(job_text, job.stack)

        skills_score, matched, missing, extra = self._calculate_skills_score(
            resume_skills, job_skills
        )

        experience_score = self._calculate_experience_score(
            resume_text, job.requirements or ""
        )

        level_score = self._calculate_level_score(resume_text, job.level or "")

        education_score = self._calculate_education_score(
            resume_text, job.requirements or ""
        )

        overall_score = (
            skills_score * self.SKILLS_WEIGHT
            + experience_score * self.EXPERIENCE_WEIGHT
            + level_score * self.LEVEL_WEIGHT
            + education_score * self.EDUCATION_WEIGHT
        )

        recommendations = self._generate_recommendations(
            missing, skills_score, experience_score, level_score
        )

        strengths = self._identify_strengths(matched, skills_score, experience_score)

        weaknesses = self._identify_weaknesses(missing, skills_score, experience_score)

        match_record = Match(
            resume_id=resume_id,
            job_id=job_id,
            overall_score=overall_score,
            skills_score=skills_score,
            experience_score=experience_score,
            level_score=level_score,
            education_score=education_score,
            matched_skills=json.dumps(matched),
            missing_skills=json.dumps(missing),
            extra_skills=json.dumps(extra),
            recommendations=json.dumps(recommendations),
            strengths=json.dumps(strengths),
            weaknesses=json.dumps(weaknesses),
        )

        self.db.add(match_record)
        await self.db.commit()

        return MatchingResult(
            overall_score=round(overall_score, 2),
            skills_score=round(skills_score, 2),
            experience_score=round(experience_score, 2),
            level_score=round(level_score, 2),
            education_score=round(education_score, 2),
            matched_skills=matched,
            missing_skills=missing,
            extra_skills=extra,
            recommendations=recommendations,
            strengths=strengths,
            weaknesses=weaknesses,
            resume_id=resume_id,
            job_id=job_id,
            analyzed_at=datetime.utcnow(),
        )

    async def recommend_resumes_for_job(
        self, job_id: int, limit: int = 10, min_score: float = 0.5
    ) -> RecommendResumesResponse:
        job_result = await self.db.execute(select(Job).where(Job.job_id == job_id))
        job = job_result.scalar_one_or_none()

        if not job:
            raise ValueError("Vaga não encontrada")

        resumes_result = await self.db.execute(
            select(Resume).where(Resume.is_public == True)
        )
        resumes = resumes_result.scalars().all()

        matches = []
        for resume in resumes:
            try:
                match_result = await self.calculate_match(resume.resume_id, job_id)

                if match_result.overall_score >= min_score:
                    version_result = await self.db.execute(
                        select(ResumeVersion)
                        .where(ResumeVersion.resume_id == resume.resume_id)
                        .order_by(ResumeVersion.version_number.desc())
                        .limit(1)
                    )
                    version = version_result.scalar_one_or_none()

                    matches.append(
                        ResumeMatchItem(
                            resume_id=resume.resume_id,
                            resume_title=resume.resume_title,
                            score=match_result.overall_score,
                            matched_skills=match_result.matched_skills[:5],
                            missing_skills=match_result.missing_skills[:5],
                            summary=version.summary[:200] + "..."
                            if version and version.summary
                            else None,
                        )
                    )
            except Exception as e:
                continue

        matches.sort(key=lambda x: x.score, reverse=True)
        matches = matches[:limit]

        return RecommendResumesResponse(
            job_id=job_id, job_title=job.title, matches=matches, total=len(matches)
        )

    async def recommend_jobs_for_resume(
        self, resume_id: int, limit: int = 10, min_score: float = 0.5
    ) -> RecommendJobsResponse:
        resume_result = await self.db.execute(
            select(Resume).where(Resume.resume_id == resume_id)
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise ValueError("Currículo não encontrado")

        jobs_result = await self.db.execute(select(Job).where(Job.is_active == True))
        jobs = jobs_result.scalars().all()

        matches = []
        for job in jobs:
            try:
                match_result = await self.calculate_match(resume_id, job.job_id)

                if match_result.overall_score >= min_score:
                    matches.append(
                        JobMatchItem(
                            job_id=job.job_id,
                            job_title=job.title,
                            company=job.company,
                            score=match_result.overall_score,
                            matched_skills=match_result.matched_skills[:5],
                            missing_skills=match_result.missing_skills[:5],
                            description_preview=job.description[:200] + "..."
                            if job.description
                            else "",
                        )
                    )
            except Exception as e:
                continue

        matches.sort(key=lambda x: x.score, reverse=True)
        matches = matches[:limit]

        return RecommendJobsResponse(
            resume_id=resume_id,
            resume_title=resume.resume_title,
            matches=matches,
            total=len(matches),
        )
