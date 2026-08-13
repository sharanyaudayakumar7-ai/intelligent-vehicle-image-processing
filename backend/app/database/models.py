import enum, uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
class JobStatus(str, enum.Enum): pending="pending"; processing="processing"; completed="completed"; failed="failed"
class Job(Base):
    __tablename__="jobs"
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str]=mapped_column(String(255)); file_path: Mapped[str]=mapped_column(String(1024))
    status: Mapped[JobStatus]=mapped_column(Enum(JobStatus), default=JobStatus.pending, index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str|None]=mapped_column(Text, nullable=True)
    metadata_record: Mapped["ImageMetadata"]=relationship(back_populates="job", uselist=False, cascade="all, delete-orphan")
    analysis_result: Mapped["AnalysisResult"]=relationship(back_populates="job", uselist=False, cascade="all, delete-orphan")
class ImageMetadata(Base):
    __tablename__="image_metadata"
    id: Mapped[int]=mapped_column(primary_key=True); job_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("jobs.id"), unique=True, index=True)
    width: Mapped[int]=mapped_column(Integer); height: Mapped[int]=mapped_column(Integer); file_size: Mapped[int]=mapped_column(Integer); mime_type: Mapped[str]=mapped_column(String(100))
    uploaded_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    job: Mapped[Job]=relationship(back_populates="metadata_record")
class AnalysisResult(Base):
    __tablename__="analysis_results"
    id: Mapped[int]=mapped_column(primary_key=True); job_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("jobs.id"), unique=True, index=True)
    perceptual_hash: Mapped[str]=mapped_column(String(64), index=True)
    blur: Mapped[dict]=mapped_column(JSONB); brightness: Mapped[dict]=mapped_column(JSONB); duplicate: Mapped[dict]=mapped_column(JSONB); number_plate: Mapped[dict]=mapped_column(JSONB); dimensions: Mapped[dict]=mapped_column(JSONB)
    job: Mapped[Job]=relationship(back_populates="analysis_result")
