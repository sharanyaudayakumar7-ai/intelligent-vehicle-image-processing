import asyncio
import json
import uuid

import numpy as np

from app.database.models import JobStatus
from app.services import image_processor
from app.services.duplicate_detector import analyze_duplicate
from app.utils.json_types import to_json_compatible
from app.worker import processor


def test_json_boundary_converts_nested_numpy_values():
    payload = {
        "flag": np.bool_(True),
        "count": np.int64(7),
        "score": np.float64(4.25),
        "pixels": np.array([np.int32(1), np.bool_(False)]),
        "nested": [{"value": np.float32(2.5)}],
    }
    normalised = to_json_compatible(payload)
    # This is the same JSON serialization requirement psycopg applies to JSONB.
    assert json.loads(json.dumps(normalised)) == {
        "flag": True, "count": 7, "score": 4.25,
        "pixels": [1, False], "nested": [{"value": 2.5}],
    }


def test_process_image_normalises_detector_payloads_before_persistence(monkeypatch):
    class Metadata: width=100; height=50
    class Job: id=uuid.uuid4(); file_path="vehicle.jpg"; metadata_record=Metadata()
    class Db:
        def __init__(self): self.saved=[]
        def add(self, value): self.saved.append(value)
    db = Db()
    monkeypatch.setattr(image_processor.cv2, "imread", lambda _: np.zeros((2, 2, 3), dtype=np.uint8))
    monkeypatch.setattr(image_processor, "analyze_duplicate", lambda *_: ("abc", {"is_duplicate": np.bool_(False), "hash_distance": np.int64(2)}))
    monkeypatch.setattr(image_processor, "analyze_blur", lambda *_: {"score": np.float64(1.5)})
    monkeypatch.setattr(image_processor, "analyze_brightness", lambda *_: {"is_low_light": np.bool_(True)})
    monkeypatch.setattr(image_processor, "analyze_ocr", lambda *_: {"confidence": np.float32(0.5)})
    monkeypatch.setattr(image_processor, "analyze_dimensions", lambda *_: {"samples": np.array([np.int64(3)])})
    settings = type("Settings", (), {"duplicate_hash_distance": 6, "blur_threshold": 1, "low_light_threshold": 1, "ocr_enabled": False, "min_image_width": 1, "min_image_height": 1})()
    image_processor.process_image(Job(), db, settings)
    result = db.saved[0]
    json.dumps({"blur": result.blur, "brightness": result.brightness, "duplicate": result.duplicate, "plate": result.number_plate, "dimensions": result.dimensions})
    assert result.duplicate["is_duplicate"] is False


def test_duplicate_detector_returns_native_boolean(monkeypatch):
    class Query:
        def all(self): return []
    class Db:
        def query(self, *_): return Query()
    monkeypatch.setattr("app.services.duplicate_detector.compute_hash", lambda _: "f" * 16)
    _, result = analyze_duplicate("vehicle.jpg", Db(), 6)
    assert type(result["is_duplicate"]) is bool


def test_worker_marks_successful_job_completed(monkeypatch):
    job = type("Job", (), {"status": JobStatus.pending, "completed_at": None, "error_message": None})()
    class Db:
        def get(self, *_): return job
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    monkeypatch.setattr(processor, "SessionLocal", lambda: Db())
    monkeypatch.setattr(processor, "process_image", lambda *_: None)
    asyncio.run(processor.process_job("job-1"))
    assert job.status is JobStatus.completed and job.completed_at is not None


def test_worker_marks_processing_error_failed(monkeypatch):
    job = type("Job", (), {"status": JobStatus.pending, "completed_at": None, "error_message": None})()
    class Db:
        def get(self, *_): return job
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    def fail(*_): raise TypeError("not JSON serializable")
    monkeypatch.setattr(processor, "SessionLocal", lambda: Db())
    monkeypatch.setattr(processor, "process_image", fail)
    asyncio.run(processor.process_job("job-2"))
    assert job.status is JobStatus.failed and job.error_message
