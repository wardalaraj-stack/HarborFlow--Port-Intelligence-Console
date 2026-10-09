"""Standalone Task 1 service: list registered vessels."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VESSELS_DIRECTORY = PROJECT_ROOT / "data" / "dataset" / "vessels"

REQUIRED_TEXT_FIELDS = ("vessel_id", "name", "imo")


def load_json(path):
    """Read one JSON object from a file and return it as a dictionary."""
    with Path(path).open("r", encoding="utf-8") as json_file:
        record = json.load(json_file)

    if not isinstance(record, dict):
        raise ValueError("top-level value must be a JSON object")

    return record


def validate_vessel(record):
    """Return a problem string for one vessel record, or None if it is valid."""
    for field in REQUIRED_TEXT_FIELDS:
        if field not in record:
            return f"{field} is missing"
        if not isinstance(record[field], str) or not record[field].strip():
            return f"{field} must be non-empty text"

    if "capacity_teu" not in record:
        return "capacity_teu is missing"

    capacity = record["capacity_teu"]
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        return "capacity_teu must be a non-negative whole number"

    return None


def load_vessels(directory):
    """Load valid vessels and return them with skipped-file diagnostics."""
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Vessel data directory not found: {directory}")

    vessels = []
    rejected_files = []
    seen_ids = set()

    for path in sorted(directory.glob("*.json"), key=lambda item: item.name.casefold()):
        try:
            record = load_json(path)
        except FileNotFoundError as error:
            rejected_files.append(f"{path.name}: {error}")
            continue
        except json.JSONDecodeError as error:
            rejected_files.append(
                f"{path.name}: malformed JSON at line {error.lineno}, column {error.colno}"
            )
            continue
        except ValueError as error:
            rejected_files.append(f"{path.name}: {error}")
            continue

        problem = validate_vessel(record)
        if problem is not None:
            rejected_files.append(f"{path.name}: {problem}")
            continue

        vessel_id = record["vessel_id"]
        if vessel_id in seen_ids:
            rejected_files.append(f"{path.name}: duplicate vessel_id {vessel_id}")
            continue

        seen_ids.add(vessel_id)
        vessels.append(record)

    vessels.sort(key=lambda vessel: vessel["name"].casefold())
    return vessels, rejected_files


def print_inventory(vessels, rejected_files):
    """Print the registered vessel inventory in the required display shape."""
    print("Registered HarborFlow vessels:")
    for vessel in vessels:
        print(f"- {vessel['name']} | IMO {vessel['imo']} | {vessel['capacity_teu']:,} TEU")
    print(f"Skipped vessel files: {len(rejected_files)}")


def service():
    """Load the dataset and print the vessel inventory."""
    try:
        vessels, rejected_files = load_vessels(VESSELS_DIRECTORY)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        print(f"Error - {error}")
        return

    print_inventory(vessels, rejected_files)


if __name__ == "__main__":
    service()

