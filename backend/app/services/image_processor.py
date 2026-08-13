import logging
import time

import cv2
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.models import AnalysisResult, Job
from app.services.blur_detector import analyze_blur
from app.services.brightness_detector import analyze_brightness
from app.services.dimension_checker import analyze_dimensions
from app.services.duplicate_detector import analyze_duplicate
from app.services.ocr_service import analyze_ocr
from app.utils.json_types import to_json_compatible


logger = logging.getLogger(__name__)


def _log_stage(stage: str, job_id, start_time: float) -> None:
    """
    Log the duration of one image-analysis stage.
    """
    duration = time.perf_counter() - start_time

    logger.info(
        "Analysis stage completed job_id=%s stage=%s duration=%.2fs",
        job_id,
        stage,
        duration,
    )


def process_image(
    job: Job,
    db: Session,
    settings: Settings,
) -> None:
    """
    Run all image-analysis checks and persist the structured result.

    Each analysis stage is timed independently so that processing
    bottlenecks can be identified from application logs.

    The caller owns the database transaction and is responsible
    for committing or rolling back the transaction.
    """

    overall_start = time.perf_counter()

    logger.info(
        "Image analysis started job_id=%s filename=%s",
        job.id,
        getattr(job, "filename", None),
    )

    # ---------------------------------------------------------
    # Image loading
    # ---------------------------------------------------------

    stage_start = time.perf_counter()

    image = cv2.imread(job.file_path)

    if image is None:
        raise ValueError(
            "The saved file could not be decoded as an image"
        )

    _log_stage(
        "image_load",
        job.id,
        stage_start,
    )

    # ---------------------------------------------------------
    # Duplicate detection
    # ---------------------------------------------------------

    stage_start = time.perf_counter()

    hash_value, duplicate = analyze_duplicate(
        job.file_path,
        db,
        settings.duplicate_hash_distance,
    )

    _log_stage(
        "duplicate_detection",
        job.id,
        stage_start,
    )

    # ---------------------------------------------------------
    # Blur detection
    # ---------------------------------------------------------

    stage_start = time.perf_counter()

    blur_result = analyze_blur(
        image,
        settings.blur_threshold,
    )

    blur_result = to_json_compatible(
        blur_result
    )

    _log_stage(
        "blur_detection",
        job.id,
        stage_start,
    )

    # ---------------------------------------------------------
    # Brightness detection
    # ---------------------------------------------------------

    stage_start = time.perf_counter()

    brightness_result = analyze_brightness(
        image,
        settings.low_light_threshold,
    )

    brightness_result = to_json_compatible(
        brightness_result
    )

    _log_stage(
        "brightness_detection",
        job.id,
        stage_start,
    )

    # ---------------------------------------------------------
    # OCR / Number plate analysis
    # ---------------------------------------------------------

    stage_start = time.perf_counter()

    number_plate_result = analyze_ocr(
        job.file_path,
        settings.ocr_enabled,
    )

    number_plate_result = to_json_compatible(
        number_plate_result
    )

    _log_stage(
        "ocr",
        job.id,
        stage_start,
    )

    # ---------------------------------------------------------
    # Dimension validation
    # ---------------------------------------------------------

    stage_start = time.perf_counter()

    meta = job.metadata_record

    dimensions_result = analyze_dimensions(
        meta.width,
        meta.height,
        settings.min_image_width,
        settings.min_image_height,
    )

    dimensions_result = to_json_compatible(
        dimensions_result
    )

    _log_stage(
        "dimension_validation",
        job.id,
        stage_start,
    )

    # ---------------------------------------------------------
    # Duplicate result conversion
    # ---------------------------------------------------------

    duplicate_result = to_json_compatible(
        duplicate
    )

    # ---------------------------------------------------------
    # Persist structured analysis result
    # ---------------------------------------------------------

    stage_start = time.perf_counter()

    db.add(
        AnalysisResult(
            job_id=job.id,
            perceptual_hash=hash_value,
            blur=blur_result,
            brightness=brightness_result,
            duplicate=duplicate_result,
            number_plate=number_plate_result,
            dimensions=dimensions_result,
        )
    )

    # Do NOT call db.flush() here.
    # The worker owns the transaction and performs db.commit()
    # after successful image processing.

    _log_stage(
        "result_persistence",
        job.id,
        stage_start,
    )

    # ---------------------------------------------------------
    # Overall timing
    # ---------------------------------------------------------

    total_duration = time.perf_counter() - overall_start

    logger.info(
        "Image analysis completed job_id=%s total_duration=%.2fs",
        job.id,
        total_duration,
    )