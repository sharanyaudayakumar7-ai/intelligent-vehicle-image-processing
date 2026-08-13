import uuid
import pytest
from fastapi import HTTPException
from app.api.images import load_job
class FakeDb:
    def __init__(self,value): self.value=value
    def get(self,*_): return self.value
def test_missing_job_returns_404():
    with pytest.raises(HTTPException) as err: load_job(uuid.uuid4(),FakeDb(None))
    assert err.value.status_code==404
def test_job_is_returned():
    job=object(); assert load_job(uuid.uuid4(),FakeDb(job)) is job
