import uuid
from pathlib import Path
import cv2,numpy as np
from fastapi import HTTPException,UploadFile,status
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.database.models import ImageMetadata,Job,JobStatus
async def create_upload_job(file:UploadFile,db:Session,settings:Settings)->Job:
    if file.content_type not in settings.allowed_mimes: raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,detail="Unsupported image type")
    payload=await file.read(); image=cv2.imdecode(np.frombuffer(payload,np.uint8),cv2.IMREAD_COLOR) if payload else None
    if image is None: raise HTTPException(status_code=422,detail="File is not a valid decodable image")
    job_id=uuid.uuid4(); settings.upload_dir.mkdir(parents=True,exist_ok=True); target=settings.upload_dir/f"{job_id}{Path(file.filename or 'image').suffix.lower() or '.jpg'}"; target.write_bytes(payload)
    height,width=image.shape[:2]; job=Job(id=job_id,filename=file.filename or target.name,file_path=str(target),status=JobStatus.pending); job.metadata_record=ImageMetadata(width=width,height=height,file_size=len(payload),mime_type=file.content_type); db.add(job); db.commit(); db.refresh(job); return job
