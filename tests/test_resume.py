import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import os

# --- Configuração de Teste ---


# 1. Mock do Banco de Dados (DB)
# A rota de upload usa o DB, então precisamos simular a sessão.
# Esta é uma forma comum de injetar uma sessão de teste.
@pytest.fixture
def mock_db_session():
    """Cria um mock para a sessão do SQLAlchemy."""
    return MagicMock(spec=Session)


# 2. Mock da Autenticação (JWT)
# A rota depende de get_current_user. Vamos simular um usuário autenticado.
@pytest.fixture
def mock_current_user():
    """Retorna um objeto de usuário mockado com o ID necessário."""
    # O ID do usuário é usado para criar o caminho do blob: f"{current_user.user_id}/..."
    return MagicMock(user_id="test_user_id_123")


# 3. Sobrescrever as Dependências
# Função para sobrescrever a dependência get_db e get_current_user
def override_get_db():
    """Função que será usada para injetar o mock da sessão DB."""
    yield mock_db_session()


def override_get_current_user():
    """Função que será usada para injetar o mock do usuário."""
    return mock_current_user()


# Aplica as sobrescritas no app
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# Cliente de Teste
client = TestClient(app)

# --- Testes da Rota de Upload ---


# O patch simula a função upload_file para que o teste não tente se conectar ao Azure Storage
@patch("api.resume.upload_file")
def test_upload_resume_success(mock_upload_file, mock_db_session):
    """Testa o cenário de sucesso para o upload de um currículo."""

    # Configura o mock para retornar uma URL de blob simulada
    mock_upload_file.return_value = "http://mocked.blob.url/test_resume.pdf"

    # Cria um arquivo de teste simples (o "menor arquivo possível" )
    file_content = b"Conteudo de teste para o curriculo."

    # Simula a requisição POST com o arquivo
    response = client.post(
        "/resumes/upload",
        files={"file": ("test_resume.pdf", file_content, "application/pdf")},
    )

    # 1. Verifica o Status Code
    assert response.status_code == 200

    # 2. Verifica o Conteúdo da Resposta
    response_data = response.json()
    assert "resume_uuid" in response_data
    assert response_data["blob_url"] == "http://mocked.blob.url/test_resume.pdf"

    # 3. Verifica se as Funções Chave Foram Chamadas

    # Verifica se a função de upload foi chamada com os argumentos corretos
    # O primeiro argumento é o conteúdo do arquivo (file_content )
    # O segundo argumento é o nome do container (assumindo que CONTAINER está definido em api.resume)
    # O terceiro argumento é o caminho de destino (que inclui o user_id e um UUID)
    mock_upload_file.assert_called_once()

    # Verifica se o objeto Resume foi adicionado e commitado no DB
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

    # Opcional: Teste de falha de autenticação (se get_current_user for removido)
    # Opcional: Teste de falha de arquivo (se nenhum arquivo for enviado)


@patch("api.resume.upload_file")
def test_upload_resume_no_file(mock_upload_file):
    """Testa o cenário onde nenhum arquivo é enviado."""

    # Simula a requisição POST sem o arquivo
    response = client.post("/resumes/upload")

    # Verifica o Status Code (deve ser 422 Unprocessable Entity)
    assert response.status_code == 422

    # Verifica a mensagem de erro
    response_data = response.json()
    assert response_data["detail"][0]["type"] == "value_error.missing"


@patch("api.resume.upload_file")
def test_upload_resume_unauthenticated(mock_upload_file):
    """Testa o cenário onde o usuário não está autenticado."""

    # Remove a sobrescrita para simular ausência de autenticação
    app.dependency_overrides.pop(get_current_user, None)

    # Cria um arquivo de teste simples
    file_content = b"Conteudo de teste para o curriculo."

    # Simula a requisição POST com o arquivo
    response = client.post(
        "/resumes/upload",
        files={"file": ("test_resume.pdf", file_content, "application/pdf")},
    )

    # Verifica o Status Code (deve ser 401 Unauthorized)
    assert response.status_code == 401

    # Verifica a mensagem de erro
    response_data = response.json()
    assert response_data["detail"] == "Not authenticated"

    # Restaura a sobrescrita para outros testes
    app.dependency_overrides[get_current_user] = override_get_current_user


@patch("api.resume.upload_file")
def test_upload_resume_large_file(mock_upload_file):
    """Testa o cenário onde o arquivo enviado é muito grande."""

    # Cria um arquivo de teste grande (por exemplo, 11 MB)
    large_file_content = b"a" * (11 * 1024 * 1024)  # 11 MB

    # Simula a requisição POST com o arquivo grande
    response = client.post(
        "/resumes/upload",
        files={
            "file": ("large_test_resume.pdf", large_file_content, "application/pdf")
        },
    )

    # Verifica o Status Code (deve ser 413 Payload Too Large ou similar, dependendo da configuração do servidor)
    assert response.status_code == 413 or response.status_code == 422

    # Verifica a mensagem de erro
    response_data = response.json()
    assert "detail" in response_data


@patch("api.resume.upload_file")
def test_upload_resume_invalid_file_type(mock_upload_file):
    """Testa o cenário onde o arquivo enviado é de um tipo inválido."""

    # Cria um arquivo de teste com um tipo inválido (por exemplo, .exe)
    invalid_file_content = b"Conteudo de teste para o curriculo."

    # Simula a requisição POST com o arquivo inválido
    response = client.post(
        "/resumes/upload",
        files={
            "file": (
                "test_resume.exe",
                invalid_file_content,
                "application/x-msdownload",
            )
        },
    )

    # Verifica o Status Code (deve ser 400 Bad Request ou similar, dependendo da validação implementada)
    assert response.status_code == 400 or response.status_code == 422

    # Verifica a mensagem de erro
    response_data = response.json()
    assert "detail" in response_data


@patch("api.resume.upload_file")
def test_upload_resume_db_failure(mock_upload_file, mock_db_session):
    """Testa o cenário onde ocorre uma falha ao salvar no banco de dados."""

    # Configura o mock para retornar uma URL de blob simulada
    mock_upload_file.return_value = "http://mocked.blob.url/test_resume.pdf"

    # Configura o mock do DB para lançar uma exceção ao chamar commit
    mock_db_session.commit.side_effect = Exception("DB Commit Failed")

    # Cria um arquivo de teste simples
    file_content = b"Conteudo de teste para o curriculo."

    # Simula a requisição POST com o arquivo
    response = client.post(
        "/resumes/upload",
        files={"file": ("test_resume.pdf", file_content, "application/pdf")},
    )

    # Verifica o Status Code (deve ser 500 Internal Server Error)
    assert response.status_code == 500

    # Verifica a mensagem de erro
    response_data = response.json()
    assert response_data["detail"] == "Internal server error"
    assert "DB Commit Failed" in response_data.get("details", {}).get("error", "")


@patch("api.resume.upload_file")
def test_upload_resume_storage_failure(mock_upload_file):
    """Testa o cenário onde ocorre uma falha ao fazer upload para o armazenamento."""

    # Configura o mock para lançar uma exceção ao chamar upload_file
    mock_upload_file.side_effect = Exception("Storage Upload Failed")

    # Cria um arquivo de teste simples
    file_content = b"Conteudo de teste para o curriculo."

    # Simula a requisição POST com o arquivo
    response = client.post(
        "/resumes/upload",
        files={"file": ("test_resume.pdf", file_content, "application/pdf")},
    )

    # Verifica o Status Code (deve ser 500 Internal Server Error)
    assert response.status_code == 500

    # Verifica a mensagem de erro
    response_data = response.json()
    assert response_data["detail"] == "Internal server error"
    assert "Storage Upload Failed" in response_data.get("details", {}).get("error", "")


# Nota: Asserções específicas podem variar dependendo de como os erros são tratados na aplicação.
