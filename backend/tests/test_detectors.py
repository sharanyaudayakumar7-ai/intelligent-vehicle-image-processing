import numpy as np

from app.services.blur_detector import analyze_blur
from app.services.brightness_detector import analyze_brightness
from app.services.dimension_checker import analyze_dimensions
from app.services.plate_validator import find_indian_plate, normalize_text


def test_brightness_flags_dark_image():
    result = analyze_brightness(
        np.zeros((20, 20, 3), dtype=np.uint8),
        60,
    )

    assert result["is_low_light"] is True


def test_blur_returns_explainable_fields():
    result = analyze_blur(
        np.zeros((20, 20, 3), dtype=np.uint8),
        100,
    )

    assert {
        "score",
        "is_blurry",
        "threshold",
        "message",
    } <= result.keys()


def test_dimension_checker():
    result = analyze_dimensions(
        640,
        480,
        640,
        480,
    )

    assert result["valid"] is True


def test_plate_validation():
    assert find_indian_plate(
        "vehicle KA 01 AB 1234"
    ) == ("KA01AB1234", True)


def test_normalization():
    assert normalize_text(
        "ka-01 ab 1234"
    ) == "KA01AB1234"