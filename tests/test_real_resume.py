import pytest
from httpx import AsyncClient
from app.main import app
import os


@pytest.mark.asyncio
async def test_full_workflow_with_real_resume():
    """Teste completo: upload currículo Vinícios, criar vaga, busca e matching"""

    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Criar vaga de Cybersecurity
        vaga_data = {
            "title": "Analista de Segurança da Informação Sênior",
            "company": "TechSec Brasil",
            "description": "Buscamos profissional com experiência em Cibersegurança, SIEM (QRadar), análise de vulnerabilidades e compliance (ISO 27001, LGPD). Conhecimentos em Python, Linux e ferramentas de pentesting são essenciais.",
            "requirements": "Experiência com QRadar, Wireshark, Nmap, Nessus, Python, ISO 27001, LGPD",
            "location": "São Paulo - SP",
            "salary_range": "R$ 8.000 - R$ 12.000",
            "level": "senior",
            "employment_type": "CLT",
            "tags": [
                "Cybersecurity",
                "SIEM",
                "QRadar",
                "Python",
                "ISO27001",
                "LGPD",
                "Pentesting",
            ],
        }

        response = await client.post(
            "/api/trpc/jobs.create",
            json=vaga_data,
            headers={"Authorization": "Bearer fake_token"},
        )
        assert response.status_code == 200
        vaga_id = response.json()["data"]["id"]

        # 2. Upload currículo do Vinícios
        curriculo_path = r"c:\Users\User\Desktop\Curriculo_Vinicios_2025.pdf"

        if os.path.exists(curriculo_path):
            with open(curriculo_path, "rb") as f:
                files = {"file": ("Curriculo_Vinicios_2025.pdf", f, "application/pdf")}
                data = {
                    "summary": "Supervisor de Segurança da Informação com expertise em Cibersegurança, GRC, SIEM (QRadar), análise de vulnerabilidades e compliance ISO 27001/LGPD"
                }

                response = await client.post(
                    "/api/trpc/resumes.create",
                    files=files,
                    data=data,
                    headers={"Authorization": "Bearer fake_token"},
                )
                assert response.status_code == 200
                resume_id = response.json()["data"]["id"]

        # 3. Buscar currículos por "QRadar"
        response = await client.get(
            "/api/trpc/search.resumes",
            params={"keywords": "QRadar,Python,Cybersecurity"},
            headers={"Authorization": "Bearer fake_token"},
        )
        assert response.status_code == 200
        results = response.json()["data"]["results"]
        assert len(results) > 0
        assert results[0]["relevance_score"] > 0.5

        # 4. Testar matching currículo x vaga
        response = await client.post(
            "/api/trpc/matching.analyze",
            json={"resume_id": resume_id, "job_id": vaga_id},
            headers={"Authorization": "Bearer fake_token"},
        )
        assert response.status_code == 200
        match_result = response.json()["data"]

        # Validações do score
        assert match_result["total_score"] >= 0.70  # Esperado: alta compatibilidade
        assert match_result["skills_score"] >= 0.75  # Skills match
        assert match_result["level_score"] >= 0.80  # Nível compatível

        print(f"\n✅ TESTE COMPLETO - Score: {match_result['total_score']:.2%}")
        print(f"   Skills: {match_result['skills_score']:.2%}")
        print(f"   Experiência: {match_result['experience_score']:.2%}")
        print(f"   Nível: {match_result['level_score']:.2%}")
        print(f"   Formação: {match_result['education_score']:.2%}")
