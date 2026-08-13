import re


# Valid Indian state / UT registration prefixes.
INDIAN_STATE_CODES = {
    "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL",
    "DN", "GA", "GJ", "HP", "HR", "JH", "JK", "KA",
    "KL", "LA", "LD", "MH", "ML", "MN", "MP", "MZ",
    "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR",
    "TS", "UK", "UP", "WB"
}


PLATE_PATTERN = re.compile(
    r"([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{4})"
)


def normalize_text(text: str) -> str:
    """
    Normalize OCR text for number plate matching.

    Removes spaces and special characters and converts
    common OCR confusion between I and 1 where possible.
    """

    text = text.upper()

    # Common OCR confusion:
    # I -> 1
    text = text.replace("I", "1")

    return re.sub(r"[^A-Z0-9]", "", text)


def find_indian_plate(text: str) -> tuple[str | None, bool]:
    """
    Search OCR text for a valid-looking Indian vehicle
    registration number.
    """

    normalized = normalize_text(text)

    for match in PLATE_PATTERN.finditer(normalized):
        state_code = match.group(1)
        registration_number = match.group(2)
        series = match.group(3)
        last_four = match.group(4)

        # Only accept genuine Indian state / UT prefixes.
        if state_code not in INDIAN_STATE_CODES:
            continue

        # Reject obvious year-like values such as 2024, 2025, 2026.
        if 1900 <= int(last_four) <= 2099:
            continue

        plate = (
            f"{state_code}"
            f"{registration_number}"
            f"{series}"
            f"{last_four}"
        )

        return plate, True

    return None, False