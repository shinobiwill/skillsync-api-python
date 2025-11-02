from fastapi import FastAPI
from app.api.resume import router as resume_router

app = FastAPI(
    title="SkillSync API",
    description="Gerenciamento de currículos e usuários",
    version="1.0.0",
)

app.include_router(resume_router, prefix="/api")
