---
> 🧠 **SkillSync API — Projeto liderado por Vinicios Rodrigues Tsatsoulis Silva**  
> 🔧 Contribuição técnica por [Luiz](https://github.com/luizfbs) — implementação em Python com FastAPI, Azure e MongoDB
---

# 🚀 SkillSync API

Backend Python da SkillSync, plataforma de gestão de habilidades, currículos e recrutamento inteligente.  
Desenvolvido com **FastAPI**, **MongoDB**, **SQL Server**, **Azure Blob Storage** e **OpenAI**.

---

## 🧱 Arquitetura

- Modular e escalável
- Separação por domínios: `users`, `skills`, `resumes`, `refs`, `jobs`, `assessments`
- Integração com múltiplos bancos: MongoDB (NoSQL) e SQL Server (relacional)
- Upload seguro de arquivos via Azure Blob Storage
- Autenticação JWT
- Documentação automática via Swagger

---

## 🛠️ Tecnologias

| Camada        | Tecnologia         |
|---------------|--------------------|
| Backend       | FastAPI            |
| Banco NoSQL   | MongoDB Atlas      |
| Banco Relacional | SQL Server       |
| Cloud Storage | Azure Blob Storage |
| IA            | OpenAI GPT         |
| Deploy        | GitHub Actions + Azure Web App |

---

## 📦 Instalação

```bash
git clone https://github.com/shinobiwill/skillsync-api-python.git
cd skillsync-api-python
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
