import re
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent[2]
DATASET_DIRECTORY = PROJECT_ROOT / "dataset"
INCIDENTS_DIRECTORY = PROJECT_ROOT / "incidents"
SANITIZED_DIRECTORY = PROJECT_ROOT / "sanitized"

INCIDENTS_REQUIRED_FIELDS = ["incident_id", "call_id", "title", "report"]

CONTAINER_PATTERN = r"\b[A-Za-z]{4}\d{7}\b"
CONTAINER_PATTERN_replacement = re.sub(CONTAINER_PATTERN , "[CONTAINER]", "")

SEAL_PATTERN = r"\bSEAL-\d{6}"
SEAL_PATTERN_replacement = re.sub(SEAL_PATTERN , "[SEAL]", "")

EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
EMAIL_PATTERN_replacement = re.sub(EMAIL_PATTERN , "[EMAIL]", "")

def validate_incidents(record):
    for field in INCIDENTS_REQUIRED_FIELDS:
        if field not in record:
            return f"{field} is missing"
    value = record[field]
    if not isinstance(value, str) or not value.strip():
        return f"{field} must not be empty"
    return None

from data_access import load_incidents

def sanitize_text(text):
    result = text
    text = CONTAINER_PATTERN_replacement
    text = SEAL_PATTERN_replacement
    text = EMAIL_PATTERN_replacement

    if result != text:
        changed = text
    else:
        changed = None

    return result, changed

def sort_incidents(incidents):
    return sorted(incidents, key=lambda incident: incident["title"].casefold())

def write_senitized_report(incident_id, sanitized_text, output_directory):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{incident_id}-sanitized.txt"
    with output_path.open("w", encoding="utf-8" , newline="") as handel:
        handel.write(sanitized_text)
    return output_path

