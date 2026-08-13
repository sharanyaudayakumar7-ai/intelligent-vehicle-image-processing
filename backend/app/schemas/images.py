from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.database.models import JobStatus
class UploadResponse(BaseModel): job_id: UUID; status: JobStatus
class StatusResponse(BaseModel):
    job_id: UUID; status: JobStatus; created_at: datetime; updated_at: datetime; completed_at: datetime|None; error_message: str|None
class ResultsResponse(BaseModel):
    job_id: UUID; status: JobStatus; message: str|None=None; image: dict|None=None; analysis: dict|None=None; error_message: str|None=None
