from datetime import datetime,timezone
import uuid
import pytest
from fastapi import UploadFile
from app.api import images
from app.database.models import JobStatus

class Job:
    def __init__(self,status):
        self.id=uuid.uuid4(); self.status=status; self.created_at=self.updated_at=datetime.now(timezone.utc); self.completed_at=None; self.error_message=None

class Db:
    def __init__(self,job): self.job=job
    def get(self,*_): return self.job

@pytest.mark.asyncio
async def test_upload_enqueues_job_and_returns_without_processing(monkeypatch):
    job=Job(JobStatus.pending)
    async def fake_create(*_): return job
    monkeypatch.setattr(images,"create_upload_job",fake_create)
    monkeypatch.setattr(images.job_queue,"put",lambda value: __import__('asyncio').sleep(0))
    response=await images.upload_image(UploadFile(filename="car.jpg",file=__import__('io').BytesIO(b"x")),Db(job))
    assert response.job_id==job.id and response.status==JobStatus.pending

def test_results_not_ready():
    job=Job(JobStatus.processing)
    response=images.get_results(job.id,Db(job))
    assert response.message=="Results are not ready yet"

def test_failed_result_surfaces_error():
    job=Job(JobStatus.failed); job.error_message="processing failed"
    assert images.get_results(job.id,Db(job)).error_message=="processing failed"
