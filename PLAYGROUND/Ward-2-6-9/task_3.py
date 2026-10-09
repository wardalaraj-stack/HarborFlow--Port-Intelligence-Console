"""Standalone Task 3 service: identify priority cargo."""

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIRECTORY = PROJECT_ROOT / "data" / "dataset"
PORT_CALLS_FILE = DATASET_DIRECTORY / "port_calls.csv"
MANIFESTS_DIRECTORY = DATASET_DIRECTORY / "manifests"
SHIPMENTS_DIRECTORY = DATASET_DIRECTORY / "shipments"

CATEGORY_ORDER = ("CONTROLLED", "COLD CHAIN", "EXPEDITE", "STANDARD")
PORT_CALL_FIELDS = ("call_id", "vessel_id", "port_code", "arrival_date")
MANIFEST_TEXT_FIELDS = ("call_id", "vessel_id")
MANIFEST_LIST_FIELDS = ("shipment_ids", "event_codes")
SHIPMENT_TEXT_FIELDS = ("shipment_id", "customer", "destination", "priority")


def prompt(message):
    """Print a question without a newline and return the typed answer."""
    print(message, end="", flush=True)
    return input()


def load_json(path):
    """Read one JSON object from a file and return it as a dictionary."""
    with Path(path).open("r", encoding="utf-8") as json_file:
        record = json.load(json_file)
    if not isinstance(record, dict):
        raise ValueError("top-level value must be a JSON object")
    return record


def _text_fields(record, fields):
    """Return the first missing or empty text field name, or None."""
    for field in fields:
        if field not in record:
            return f"{field} is missing"
        if not isinstance(record[field], str) or not record[field].strip():
            return f"{field} must be non-empty text"
    return None


def _is_number(value):
    """Return True for ints and floats, but never for booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_manifest(record):
    """Return a problem message for one manifest record, or None if it is good."""
    problem = _text_fields(record, MANIFEST_TEXT_FIELDS)
    if problem is not None:
        return problem

    for field in MANIFEST_LIST_FIELDS:
        value = record.get(field)
        if not isinstance(value, list):
            return f"{field} must be a list"
        if any(not isinstance(item, str) for item in value):
            return f"{field} must contain only text values"

    return None


def validate_shipment(record):
    """Return a problem message for one shipment record, or None if it is good."""
    problem = _text_fields(record, SHIPMENT_TEXT_FIELDS)
    if problem is not None:
        return problem

    if "weight_kg" not in record:
        return "weight_kg is missing"
    if not _is_number(record["weight_kg"]):
        return "weight_kg must be a number"

    for field in ("hazardous", "temperature_controlled"):
        if record.get(field) is not None and not isinstance(record[field], bool):
            return f"{field} must be true or false"

    return None


def load_records(directory, validate, label, duplicate_key=None):
    """Load every JSON record in a folder and keep the first matching key."""
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"{label} directory not found: {directory}")

    records = []
    diagnostics = []
    seen = set()

    for path in sorted(directory.glob("*.json"), key=lambda item: item.name.casefold()):
        try:
            record = load_json(path)
        except FileNotFoundError as error:
            diagnostics.append(f"{path.name}: {error}")
            continue
        except json.JSONDecodeError as error:
            diagnostics.append(
                f"{path.name}: malformed JSON at line {error.lineno}, column {error.colno}"
            )
            continue
        except ValueError as error:
            diagnostics.append(f"{path.name}: {error}")
            continue

        problem = validate(record)
        if problem is not None:
            diagnostics.append(f"{path.name}: {problem}")
            continue

        if duplicate_key is not None:
            key = duplicate_key(record)
            if key in seen:
                diagnostics.append(f"{path.name}: duplicate record {key}")
                continue
            seen.add(key)

        records.append(record)

    return records, diagnostics


def load_manifests(directory):
    """Load valid manifests together with the rejected-file messages."""
    return load_records(
        directory,
        validate_manifest,
        "Manifest data",
        duplicate_key=lambda record: (
            record["call_id"].strip().casefold(),
            record["vessel_id"].strip().casefold(),
        ),
    )


def load_shipments(directory):
    """Load valid shipments together with the rejected-file messages."""
    return load_records(
        directory,
        validate_shipment,
        "Shipment data",
        duplicate_key=lambda record: record["shipment_id"].strip().casefold(),
    )


def load_port_calls(path):
    """Read port_calls.csv and return its rows together with row problems."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Port call file not found: {path}")

    rows = []
    diagnostics = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [name for name in PORT_CALL_FIELDS if name not in header]
        if missing:
            raise ValueError(f"port_calls.csv is missing columns: {', '.join(missing)}")

        seen = set()
        for number, row in enumerate(reader, start=2):
            empty = [
                name for name in PORT_CALL_FIELDS
                if row.get(name) is None or str(row[name]).strip() == ""
            ]
            if empty:
                diagnostics.append(
                    f"port_calls.csv row {number}: missing {', '.join(empty)}"
                )
                continue

            call_id = row["call_id"].strip()
            key = call_id.casefold()
            if key in seen:
                diagnostics.append(
                    f"port_calls.csv row {number}: duplicate call_id {call_id}"
                )
                continue

            seen.add(key)
            rows.append({name: row[name] for name in PORT_CALL_FIELDS})

    return rows, diagnostics


def resolve_call(call_id_text, calls):
    """Return the port call whose call_id matches, or None when there is no match."""
    wanted = call_id_text.strip().casefold()
    for call in calls:
        if call["call_id"].strip().casefold() == wanted:
            return call
    return None


def find_manifest(manifests, call):
    """Return the first usable manifest for a call, or None when there is none."""
    for manifest in manifests:
        if manifest["call_id"].strip().casefold() != call["call_id"].strip().casefold():
            continue
        if manifest["vessel_id"].strip().casefold() != call["vessel_id"].strip().casefold():
            continue
        return manifest
    return None


def index_shipments(shipments):
    """Return a lookup from shipment_id to the first valid shipment record."""
    lookup = {}
    for shipment in shipments:
        lookup.setdefault(shipment["shipment_id"].strip().casefold(), shipment)
    return lookup


def classify_shipment(shipment):
    """Return the category and reason for one shipment record."""
    if shipment.get("hazardous", False):
        return "CONTROLLED", "hazardous cargo"
    if shipment.get("temperature_controlled", False):
        return "COLD CHAIN", "temperature controlled"

    weight = shipment.get("weight_kg", 0)
    if not _is_number(weight):
        weight = 0
    if shipment.get("priority") == "EXPRESS" or weight >= 5000:
        return "EXPEDITE", "express service"
    return "STANDARD", "standard handling"


def build_priority_report(manifest, shipment_lookup):
    """Collect the report lines and category totals without printing anything."""
    lines = []
    totals = {category: 0 for category in CATEGORY_ORDER}

    for shipment_id in manifest["shipment_ids"]:
        shipment = shipment_lookup.get(shipment_id.strip().casefold())
        if shipment is None:
            continue

        category, reason = classify_shipment(shipment)
        lines.append((shipment["shipment_id"], category, reason))
        totals[category] += 1

    return {"lines": lines, "totals": totals}


def print_priority_report(report):
    """Print the priority-cargo report in the exact output shape."""
    for shipment_id, category, reason in report["lines"]:
        print(f"{shipment_id} | {category} | {reason}")
    totals = report["totals"]
    print(
        "Category totals: "
        f"CONTROLLED={totals['CONTROLLED']}, "
        f"COLD CHAIN={totals['COLD CHAIN']}, "
        f"EXPEDITE={totals['EXPEDITE']}, "
        f"STANDARD={totals['STANDARD']}"
    )


def resolve_priority_task(call_id_text, calls, manifests, shipments):
    """Return either an error string or a ready-to-print report."""
    call = resolve_call(call_id_text, calls)
    if call is None:
        return "Port call not found."

    manifest = find_manifest(manifests, call)
    if manifest is None:
        return "Manifest unavailable."

    return build_priority_report(manifest, index_shipments(shipments))


def service():
    """Run the Task 3 flow once and print its result."""
    try:
        calls, _call_diagnostics = load_port_calls(PORT_CALLS_FILE)
        manifests, _manifest_diagnostics = load_manifests(MANIFESTS_DIRECTORY)
        shipments, _shipment_diagnostics = load_shipments(SHIPMENTS_DIRECTORY)
    except (FileNotFoundError, json.JSONDecodeError, csv.Error, ValueError) as error:
        print(f"Error - {error}")
        return

    call_id = prompt("Call ID: ")
    result = resolve_priority_task(call_id, calls, manifests, shipments)
    if isinstance(result, str):
        print(result)
        return

    print_priority_report(result)


if __name__ == "__main__":
    service()
