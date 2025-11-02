from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from storage import upload_file, generate_sas_for_blob
from auth import create_access_token

router = APIRouter()

@router.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...), current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    data = await file.read()
    # calular hash
    import hashlib
    h = hashlib.sha256(data).hexdigest()
    dest = f"{current_user.user_id}/{str(uuid.uuid4())}/{file.filename}"
    blob_url = upload_file(data, CONTAINER, dest)
    # criar registro no DB (Resume)
    resume = Resume(user_id=current_user.user_id, resume_hash=h, blob_url=blob_url, blob_file_name=file.filename, blob_file_size_kb=len(data)//1024)
    db.add(resume); db.commit(); db.refresh(resume)
    return {"resume_uuid": resume.resume_uuid, "blob_url": blob_url}

