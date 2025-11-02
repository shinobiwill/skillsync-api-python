# storage.py
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import hashlib, os
from datetime import datetime, timedelta

BLOB_CONN_STR = "AZURE_STORAGE_CONNECTION_STRING"  # via .env
CONTAINER = "skillsync-resumes"

blob_service = BlobServiceClient.from_connection_string(BLOB_CONN_STR)


def upload_file(file_bytes: bytes, container: str, dest_path: str):
    client = blob_service.get_container_client(container)
    blob = client.get_blob_client(dest_path)
    blob.upload_blob(file_bytes, overwrite=True)
    return blob.url


def generate_sas_for_blob(container, blob_name, expiry_minutes=60):
    sas_token = generate_blob_sas(
        account_name=blob_service.account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=blob_service.credential.account_key,  # cuidado: em ambientes dev
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )
    return f"https://{blob_service.account_name}.blob.core.windows.net/{container}/{blob_name}?{sas_token}"
