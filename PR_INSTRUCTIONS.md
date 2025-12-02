# Instruções para Pull Request - Implementa Domínios 2 e 3 da SkillSync API (resumes e jobs)

## Resumo
Implementação completa dos endpoints da API SkillSync para os Domínios 2 (Gestão de Currículos) e 3 (Gestão de Descrições de Vagas) conforme especificação oficial.

## Endpoints Implementados

### Domínio 2: Gestão de Currículos
- `POST /api/trpc/resumes.create` - Upload multipart de currículo com versionamento automático
- `GET /api/trpc/resumes.get` - Busca currículo por ID (próprio ou público)
- `PUT /api/trpc/resumes.update` - Atualiza metadados e/ou cria nova versão
- `DELETE /api/trpc/resumes.delete` - Exclui currículo (somente do proprietário)
- `GET /api/trpc/resumes.listByUser` - Lista todos os currículos do usuário autenticado
- `GET /api/trpc/resumes.getVersions` - Lista todas as versões de um currículo

### Domínio 3: Gestão de Vagas
- `POST /api/trpc/jobs.create` - Cria descrição de vaga
- `GET /api/trpc/jobs.get` - Busca vaga por ID (pública)
- `PUT /api/trpc/jobs.update` - Atualiza vaga (somente do proprietário)
- `DELETE /api/trpc/jobs.delete` - Exclui vaga (somente do proprietário)
- `GET /api/trpc/jobs.list` - Lista vagas com filtros por stack e level

## Arquivos Criados

### Models
- `app/models/models.py` - Adicionados models:
  - `ResumeVersion` - Versionamento de currículos
  - `Job` - Descrições de vagas

### Schemas
- `app/schemas/resume_schemas.py` - Schemas Pydantic para currículos
- `app/schemas/job_schemas.py` - Schemas Pydantic para vagas

### Services
- `app/services/resume_service_v2.py` - ResumeService com lógica de versionamento
- `app/services/job_service.py` - JobService com filtros

### Routers
- `app/routers/resumes_v2.py` - Router de currículos com endpoints tRPC
- `app/routers/jobs.py` - Router de vagas com endpoints tRPC

### Database
- `app/db.py` - Configuração SQLAlchemy async com SQLite/aiosqlite

### Tests
- `tests/test_api_dom2_dom3.py` - Testes básicos com TestClient

## Arquivos Modificados
- `app/main.py` - Integração dos novos routers e lifespan com init_db
- `app/models/models.py` - Adicionado relacionamento `versions` em Resume
- `requirements.txt` - Atualizadas dependências (SQLAlchemy 2.0, aiosqlite, pydantic 2.x)

## Requisitos Técnicos Implementados

### Autenticação
- JWT Bearer Token via `get_current_user` dependency
- Extração de `user_id` do token
- Validação de propriedade de recursos

### Versionamento de Currículos
- Nova versão criada automaticamente quando:
  - Arquivo (`file`) é alterado (hash diferente)
  - Sumário (`summary`) é modificado
- Cada versão possui:
  - `storage_key` único: `resumes/{user_id}/{resume_uuid}/v{version_number}`
  - `storage_url`: URL completa para armazenamento
  - `content_hash`: SHA-256 do conteúdo do arquivo

### Armazenamento
- Tags e stack armazenados como JSON em string
- Conversão automática em schemas Pydantic com `@validator`

### Banco de Dados
- SQLAlchemy async com SQLite (aiosqlite)
- Models com relacionamentos (Resume <-> ResumeVersion)
- Suporte a filtros e paginação

## Como Testar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Rodar a aplicação
```bash
uvicorn app.main:app --reload
```

### 3. Acessar documentação interativa
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Rodar testes
```bash
pytest tests/test_api_dom2_dom3.py -v
```

## Estrutura de Tabelas

### tb_resumes
- `resume_id` (PK)
- `resume_uuid` (unique)
- `user_id` (FK)
- `resume_title`
- `resume_hash`
- `blob_url`
- `blob_file_name`
- `blob_file_size_kb`
- `is_public`
- `created_at`

### tb_resume_versions
- `version_id` (PK)
- `resume_id` (FK)
- `version_number`
- `storage_key`
- `storage_url`
- `content_hash` (SHA-256)
- `summary`
- `tags` (JSON string)
- `created_at`

### tb_jobs
- `job_id` (PK)
- `job_uuid` (unique)
- `user_id` (FK)
- `title`
- `company`
- `location`
- `description`
- `requirements`
- `stack` (JSON string)
- `level`
- `salary_range`
- `is_active`
- `created_at`
- `updated_at`

## Próximos Passos

1. Adicionar integração com Azure Blob Storage real
2. Implementar extração de texto de PDFs/DOCX
3. Adicionar análise de IA para compatibilidade currículo-vaga
4. Implementar busca full-text
5. Adicionar rate limiting
6. Melhorar cobertura de testes

## Observações

- Código formatado com Black
- Validação Pydantic em todos os endpoints
- Tratamento de erros com HTTPException
- Logs estruturados
- Documentação OpenAPI automática
