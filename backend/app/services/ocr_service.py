import logging

import cv2

from app.services.plate_validator import find_indian_plate


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OCR Reader
# ---------------------------------------------------------------------------
# EasyOCR is loaded lazily only when OCR is actually enabled and requested.
#
# This keeps the application lightweight when OCR is disabled, which is
# useful for deployment environments where the EasyOCR/PyTorch dependency
# footprint is too large.
# ---------------------------------------------------------------------------

_reader = None


def _get_reader():
    global _reader

    if _reader is None:
        import easyocr

        _reader = easyocr.Reader(
            ["en"],
            gpu=False,
            verbose=False,
        )

    return _reader


# ---------------------------------------------------------------------------
# OCR Helpers
# ---------------------------------------------------------------------------

def _run_ocr(image):
    """
    Run OCR using characters that can appear on an Indian vehicle
    registration plate.
    """

    return _get_reader().readtext(
        image,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        detail=1,
        paragraph=False,
    )


def _prepare_images(file_path: str):
    """
    Create OCR-friendly image variants.

    The original image is retained because it may contain useful
    plate information that preprocessing could remove.
    """

    image = cv2.imread(file_path)

    if image is None:
        raise ValueError("Unable to read image")

    variants = [image]

    # Grayscale + upscale can help with small plate characters.
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    enlarged = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC,
    )

    variants.append(enlarged)

    return variants


def _find_plate_from_rows(rows):
    """
    Search OCR output for a valid Indian registration number.

    OCR may split a plate into multiple pieces, so we test:
    - individual OCR results
    - neighbouring OCR results
    - all OCR results together
    """

    parts = []

    for row in rows:
        if len(row) < 3:
            continue

        text = str(row[1]).strip().upper()

        if text:
            parts.append(text)

    candidates = []

    # Individual OCR detections.
    candidates.extend(parts)

    # Combine neighbouring OCR detections.
    for index in range(len(parts) - 1):
        candidates.append(
            parts[index] + parts[index + 1]
        )

    # Combine all OCR detections.
    if parts:
        candidates.append("".join(parts))

    for candidate in candidates:
        plate, valid = find_indian_plate(candidate)

        if plate and valid:
            return plate

    return None


# ---------------------------------------------------------------------------
# Main OCR Analysis
# ---------------------------------------------------------------------------

def analyze_ocr(file_path: str, enabled: bool) -> dict:
    """
    Run OCR and attempt to identify an Indian vehicle registration number.

    OCR output is probabilistic and should be reviewed before being treated
    as authoritative.
    """

    if not enabled:
        return {
            "extracted_text": "",
            "detected": False,
            "text": None,
            "format_valid": False,
            "confidence": None,
            "message": "OCR is disabled by configuration",
        }

    try:
        variants = _prepare_images(file_path)

        best_plate = None
        best_confidence = 0.0

        for image in variants:
            rows = _run_ocr(image)

            plate = _find_plate_from_rows(rows)

            confidence = max(
                (
                    float(row[2])
                    for row in rows
                    if len(row) >= 3
                ),
                default=0.0,
            )

            if plate and confidence > best_confidence:
                best_plate = plate
                best_confidence = confidence

        if best_plate:
            return {
                "extracted_text": best_plate,
                "detected": True,
                "text": best_plate,
                "format_valid": True,
                "confidence": round(best_confidence, 3),
                "message": (
                    "Possible Indian vehicle registration "
                    "number detected"
                ),
            }

        return {
            "extracted_text": "",
            "detected": False,
            "text": None,
            "format_valid": False,
            "confidence": None,
            "message": (
                "No valid Indian vehicle registration "
                "format detected"
            ),
        }

    except Exception as exc:
        logger.warning(
            "OCR unavailable or failed: %s",
            exc,
        )

        return {
            "extracted_text": "",
            "detected": False,
            "text": None,
            "format_valid": False,
            "confidence": None,
            "message": (
                "OCR could not be completed; "
                "other analyses are available"
            ),
        }