"""File loading, validation and path handling for HarborFlow.

Every other module gets its data through the functions in this file.
No function here prints anything: loaders RETURN what they found plus a
list of what they skipped, and main.py decides what to show the user.

Return formats agreed by the team:
- JSON collections -> (records, skipped)
    records: dict keyed by business ID, e.g. {"SHP-1042": {...}, ...}
    skipped: list of (filename, reason) tuples
- CSV files -> (rows, skipped)
    rows:    list of dicts in file order, all values still strings
    skipped: list of (line_number, reason) tuples
"""

import csv
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# PATHS
# All paths are relative to the project root, so the program must be run
# from there with: python main.py
# Never replace these with an absolute path from your own computer.
# ---------------------------------------------------------------------------

DATASET_DIR = Path("dataset")
VESSELS_DIR = DATASET_DIR / "vessels"        # "/" joins path parts in pathlib
MANIFESTS_DIR = DATASET_DIR / "manifests"
SHIPMENTS_DIR = DATASET_DIR / "shipments"
INCIDENTS_DIR = DATASET_DIR / "incidents"
PORT_CALLS_FILE = DATASET_DIR / "port_calls.csv"
WEATHER_FILE = DATASET_DIR / "weather.csv"
INCIDENT_INDEX_FILE = DATASET_DIR / "incident-index.json"   # Task 9 cache

EXPORTS_DIR = Path("exports")
CUSTOMER_PROFILES_FILE = EXPORTS_DIR / "customer-profiles.csv"   # Task 4
SANITIZED_DIR = EXPORTS_DIR / "sanitized"                         # Task 6


# ---------------------------------------------------------------------------
# REQUIRED FIELDS (from DATA-DICTIONARY.md)
# Optional fields (hazardous, temperature_controlled, cargo_type) are
# deliberately NOT listed, so records without them still count as valid.
# ---------------------------------------------------------------------------

VESSEL_FIELDS = ("vessel_id", "name", "imo", "capacity_teu")
MANIFEST_FIELDS = ("call_id", "vessel_id", "shipment_ids", "event_codes")
SHIPMENT_FIELDS = ("shipment_id", "customer", "destination", "weight_kg", "priority")
INCIDENT_FIELDS = ("incident_id", "call_id", "title", "report")

PORT_CALL_COLUMNS = ("call_id", "vessel_id", "port_code", "arrival_date")
WEATHER_COLUMNS = ("port_code", "date", "wind_kmh", "precipitation_mm", "wave_height_m")


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def find_missing_fields(record, required_fields):
    """Return a list of required fields that are absent from record.

    An empty list means the record is valid.
    """
    missing = []
    for field in required_fields:
        if field not in record:
            missing.append(field)
    return missing


# ---------------------------------------------------------------------------
# JSON LOADING
# ---------------------------------------------------------------------------

def load_json(path):
    """Read one JSON file and return its contents as Python objects.

    This function does NOT catch errors. If the file is missing or broken,
    FileNotFoundError or json.JSONDecodeError travels up to the caller,
    who knows whether to skip the file or report it.
    """
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_json_collection(directory, required_fields, id_field):
    """Load and validate every .json file in one folder.

    directory:       folder to read, e.g. VESSELS_DIR
    required_fields: tuple of field names every record must have
    id_field:        the field used as dictionary key, e.g. "vessel_id"

    Returns (records, skipped). One bad file is skipped and recorded;
    it never stops the other files from loading.
    """
    records = {}
    skipped = []

    # sorted() gives the same file order on every computer.
    # If the folder does not exist, glob() simply finds no files.
    for path in sorted(directory.glob("*.json")):

        # Step 1: LOAD. Catch only the errors we can respond to usefully.
        try:
            record = load_json(path)
        except json.JSONDecodeError:
            skipped.append((path.name, "malformed JSON"))
            continue          # move on to the next file
        except FileNotFoundError:
            skipped.append((path.name, "file not found"))
            continue

        # Step 2: VALIDATE shape. A valid JSON file could still contain a
        # list or a number instead of one record (a dict).
        if not isinstance(record, dict):
            skipped.append((path.name, "not a single JSON object"))
            continue

        # Step 3: VALIDATE fields. Every required field must be present.
        missing = find_missing_fields(record, required_fields)
        if missing:
            skipped.append((path.name, "missing " + ", ".join(missing)))
            continue

        # Step 4: VALIDATE uniqueness. Two files with the same ID would
        # silently overwrite each other in the dict, so keep the first.
        record_id = record[id_field]
        if record_id in records:
            skipped.append((path.name, "duplicate " + id_field + " " + str(record_id)))
            continue

        # The key is the business ID read from INSIDE the file, never the
        # filename (the spec says filenames may not match IDs).
        records[record_id] = record

    return records, skipped


# One small wrapper per folder, so other modules never need to know the
# folder paths or required fields.
# The directory parameter has a DEFAULT value: calling load_vessels() reads
# the real dataset, while load_vessels(Path("some_test_folder")) reads a
# different folder, which is useful for testing with broken files.

def load_vessels(directory=VESSELS_DIR):
    """Return (vessels keyed by vessel_id, skipped files)."""
    return load_json_collection(directory, VESSEL_FIELDS, "vessel_id")


def load_manifests(directory=MANIFESTS_DIR):
    """Return (manifests keyed by call_id, skipped files)."""
    return load_json_collection(directory, MANIFEST_FIELDS, "call_id")


def load_shipments(directory=SHIPMENTS_DIR):
    """Return (shipments keyed by shipment_id, skipped files)."""
    return load_json_collection(directory, SHIPMENT_FIELDS, "shipment_id")


def load_incidents(directory=INCIDENTS_DIR):
    """Return (incidents keyed by incident_id, skipped files)."""
    return load_json_collection(directory, INCIDENT_FIELDS, "incident_id")


# ---------------------------------------------------------------------------
# CSV LOADING
# ---------------------------------------------------------------------------

def load_csv_rows(path, required_columns):
    """Read one CSV file and return (rows, skipped).

    Each row is a dict like {"call_id": "HFL-GOT-2048", ...}.
    All values stay STRINGS: converting dates and numbers is done by the
    task that uses them (Tasks 5 and 8 must report bad rows themselves).

    Errors that make the WHOLE file unusable are not caught here:
    - FileNotFoundError: the file does not exist
    - csv.Error:         the file cannot be parsed as CSV
    - ValueError:        the header is missing a required column
    The calling service catches these and prints a useful message.
    """
    rows = []
    skipped = []

    # newline="" is what the csv module expects when opening files.
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)   # uses the first line as the header

        # Check the header once, before reading any rows.
        header = reader.fieldnames or []
        missing_columns = find_missing_fields(header, required_columns)
        if missing_columns:
            raise ValueError(path.name + " is missing columns: " + ", ".join(missing_columns))

        for row in reader:
            # A short row gives None for missing columns; an empty cell
            # gives "". Either way, the row cannot be used.
            empty = []
            for column in required_columns:
                value = row.get(column)
                if value is None or value.strip() == "":
                    empty.append(column)

            if empty:
                # reader.line_num is the current line in the file
                # (line 1 is the header), useful when reporting errors.
                skipped.append((reader.line_num, "empty " + ", ".join(empty)))
                continue

            rows.append(row)

    return rows, skipped


def load_port_calls(path=PORT_CALLS_FILE):
    """Return (port call rows, skipped rows) from port_calls.csv."""
    return load_csv_rows(path, PORT_CALL_COLUMNS)


def load_weather(path=WEATHER_FILE):
    """Return (forecast rows, skipped rows) from weather.csv."""
    return load_csv_rows(path, WEATHER_COLUMNS)