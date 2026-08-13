import asyncio
import logging
import time
from datetime import datetime, timezone

from app.core.config import get_settings
from app.database.connection import SessionLocal
from app.database.models import Job, JobStatus
from app.services.image_processor import process_image
from app.worker.queue import job_queue


logger = logging.getLogger(__name__)


# Maximum number of processing attempts.
MAX_RETRIES = 2


def _process_job_in_thread(job_id: str) -> None:
    """
    Execute image processing using a database session created
    inside the worker thread.

    SQLAlchemy sessions should not be shared across threads.
    """

    db = SessionLocal()

    try:
        job = db.get(Job, job_id)

        if job is None:
            raise ValueError(
                f"Job not found during processing: {job_id}"
            )

        process_image(
            job,
            db,
            get_settings(),
        )

        # Commit the analysis result after the complete
        # processing pipeline succeeds.
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def _is_retryable_error(exc: Exception) -> bool:
    """
    Decide whether a processing failure should be retried.

    Invalid or corrupted input is not retryable because repeating
    the same operation will not make the image valid.

    Other unexpected failures may be transient and are therefore
    eligible for a limited retry.
    """

    if isinstance(exc, ValueError):
        return False

    return True


async def process_job(job_id: str) -> None:
    """
    Process one queued job.

    The job is retried a limited number of times for potentially
    transient failures.

    Every job eventually reaches a terminal state:
    completed or failed.
    """

    start_time = time.perf_counter()

    logger.info(
        "Job picked from queue job_id=%s",
        job_id,
    )

    for attempt in range(1, MAX_RETRIES + 1):

        db = SessionLocal()

        try:
            job = db.get(Job, job_id)

            if job is None:
                logger.warning(
                    "Queued job not found job_id=%s",
                    job_id,
                )
                return

            logger.info(
                "Processing job job_id=%s filename=%s attempt=%s/%s",
                job_id,
                getattr(job, "filename", None),
                attempt,
                MAX_RETRIES,
            )

            # ---------------------------------------------------------
            # Mark job as processing
            # ---------------------------------------------------------

            job.status = JobStatus.processing
            job.error_message = None

            db.commit()

            logger.info(
                "Processing started job_id=%s attempt=%s/%s",
                job_id,
                attempt,
                MAX_RETRIES,
            )

            # ---------------------------------------------------------
            # Run image processing in a background thread.
            #
            # The thread creates and owns its own database session.
            # ---------------------------------------------------------

            await asyncio.to_thread(
                _process_job_in_thread,
                job_id,
            )

            # ---------------------------------------------------------
            # Processing succeeded.
            #
            # The current worker session still owns the Job object,
            # so there is no need to call expire_all() or reload it.
            # ---------------------------------------------------------

            job.status = JobStatus.completed
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = None

            db.commit()

            duration = time.perf_counter() - start_time

            logger.info(
                "Processing completed job_id=%s attempt=%s duration=%.2fs",
                job_id,
                attempt,
                duration,
            )

            return

        except Exception as exc:

            db.rollback()

            duration = time.perf_counter() - start_time
            retryable = _is_retryable_error(exc)

            logger.exception(
                "Processing failed job_id=%s attempt=%s/%s "
                "retryable=%s duration=%.2fs error=%s",
                job_id,
                attempt,
                MAX_RETRIES,
                retryable,
                duration,
                exc,
            )

            # ---------------------------------------------------------
            # Retry transient failures.
            # ---------------------------------------------------------

            if retryable and attempt < MAX_RETRIES:

                logger.warning(
                    "Retrying job job_id=%s next_attempt=%s/%s",
                    job_id,
                    attempt + 1,
                    MAX_RETRIES,
                )

                await asyncio.sleep(1)

                continue

            # ---------------------------------------------------------
            # Permanent failure.
            # ---------------------------------------------------------

            job = db.get(Job, job_id)

            if job is not None:
                job.status = JobStatus.failed
                job.error_message = (
                    "Image processing failed. "
                    "Review server logs for details."
                )
                job.completed_at = datetime.now(timezone.utc)

                db.commit()

            logger.error(
                "Job permanently failed job_id=%s attempts=%s "
                "duration=%.2fs",
                job_id,
                attempt,
                duration,
            )

            return

        finally:
            db.close()


async def process_queue() -> None:
    """
    Continuously consume jobs from the in-memory queue.
    """

    logger.info("Queue consumer started")

    while True:

        job_id = await job_queue.get()

        try:
            await process_job(job_id)

        except Exception:
            # Safety guard so an unexpected worker-level exception
            # does not terminate the queue consumer.
            logger.exception(
                "Unexpected queue worker error job_id=%s",
                job_id,
            )

        finally:
            job_queue.task_done()