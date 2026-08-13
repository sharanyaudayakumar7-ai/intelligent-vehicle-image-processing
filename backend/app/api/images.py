import logging
from uuid import UUID
from fastapi import APIRouter,Depends,File,HTTPException,UploadFile,status
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.database.connection import get_db
from app.database.models import Job,JobStatus
from app.schemas.images import UploadResponse,StatusResponse,ResultsResponse
from app.services.upload_service import create_upload_job
from app.worker.queue import job_queue
router=APIRouter(prefix="/api/v1/images",tags=["images"]); logger=logging.getLogger(__name__)
@router.post("",response_model=UploadResponse,status_code=status.HTTP_202_ACCEPTED)
async def upload_image(file:UploadFile=File(...),db:Session=Depends(get_db)):
    job=await create_upload_job(file,db,get_settings()); await job_queue.put(str(job.id)); logger.info("Job created and queued job_id=%s",job.id); return UploadResponse(job_id=job.id,status=job.status)
def load_job(job_id:UUID,db:Session)->Job:
    job=db.get(Job,job_id)
    if not job: raise HTTPException(status_code=404,detail="Job not found")
    return job
@router.get("/{job_id}/status",response_model=StatusResponse)
def get_status(job_id:UUID,db:Session=Depends(get_db)):
    job=load_job(job_id,db); return StatusResponse(job_id=job.id,status=job.status,created_at=job.created_at,updated_at=job.updated_at,completed_at=job.completed_at,error_message=job.error_message)
@router.get("/{job_id}/results",response_model=ResultsResponse)
def get_results(job_id:UUID,db:Session=Depends(get_db)):
    job=load_job(job_id,db)
    if job.status!=JobStatus.completed:
        return ResultsResponse(job_id=job.id,status=job.status,error_message=job.error_message) if job.status==JobStatus.failed else ResultsResponse(job_id=job.id,status=job.status,message="Results are not ready yet")
    meta,result=job.metadata_record,job.analysis_result
    return ResultsResponse(job_id=job.id,status=job.status,image={"filename":job.filename,"width":meta.width,"height":meta.height,"mime_type":meta.mime_type},analysis={"blur":result.blur,"brightness":result.brightness,"duplicate":result.duplicate,"number_plate":result.number_plate,"dimensions":result.dimensions})
