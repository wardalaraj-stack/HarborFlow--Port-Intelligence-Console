"""Standalone Task 4 service: export a customer operations profile."""

# This file keeps Task 4 separate from the shared console entry point.
# It reads shipment data, builds one customer summary, and writes one CSV row.

import csv
import json
import os
import tempfile
from pathlib import Path


# Start from this file, walk back to the ass2 folder, then reach the dataset.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIRECTORY = PROJECT_ROOT / "data" / "dataset"
SHIPMENTS_DIRECTORY = DATASET_DIRECTORY / "shipments"
EXPORTS_DIRECTORY = PROJECT_ROOT / "exports"
CUSTOMER_PROFILE_PATH = EXPORTS_DIRECTORY / "customer-profiles.csv"

# The export file must always use the exact header and field order below.
CUSTOMER_PROFILE_FIELDS = (
    "customer",
    "shipment_count",
    "total_weight_kg",
    "express_count",
    "destinations",
)


def prompt(message):
    """Print a question without a newline and return the typed answer."""
    # end="" keeps the prompt on one line; flush=True makes it appear right away.
    print(message, end="", flush=True)
    return input()


def load_json(path):
    """Read one JSON object from a file and return it as a dictionary."""
    # Open the file as UTF-8 text so the dataset is read consistently.
    with Path(path).open("r", encoding="utf-8") as json_file:
        record = json.load(json_file)

    # The task expects an object, not a list or other JSON shape.
    if not isinstance(record, dict):
        raise ValueError("top-level value must be a JSON object")

    return record


def _text_fields(record, fields):
    """Return the first missing or empty text field name, or None."""
    # Check required text fields in order so the first problem is reported first.
    for field in fields:
        if field not in record:
            return f"{field} is missing"
        if not isinstance(record[field], str) or not record[field].strip():
            return f"{field} must be non-empty text"
    return None


def _is_number(value):
    """Return True for ints and floats, but never for booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_shipment(record):
    """Check one shipment record and return a problem string or None."""
    # These four text fields must all exist and contain visible text.
    problem = _text_fields(
        record,
        ("shipment_id", "customer", "destination", "priority"),
    )
    if problem is not None:
        return problem

    # weight_kg is required and must be numeric.
    if "weight_kg" not in record:
        return "weight_kg is missing"
    if not _is_number(record["weight_kg"]):
        return "weight_kg must be a number"

    # Optional booleans are allowed when present, and rejected when malformed.
    for field in ("hazardous", "temperature_controlled"):
        if record.get(field) is not None and not isinstance(record[field], bool):
            return f"{field} must be true or false"

    # Optional cargo_type is not needed for Task 4, but a wrong type is still bad.
    if record.get("cargo_type") is not None and not isinstance(record["cargo_type"], str):
        return "cargo_type must be text"

    return None


def _load_records(directory, key_field, validate, label):
    """Load JSON records from a folder and keep the first record for each key."""
    directory = Path(directory)

    # Stop early if the folder itself does not exist.
    if not directory.is_dir():
        raise FileNotFoundError(f"{label} directory not found: {directory}")

    records = []
    diagnostics = []
    seen = set()

    # Sorted names make repeated runs behave the same way.
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

        # Skip records that fail the task's shared validation rules.
        problem = validate(record)
        if problem is not None:
            diagnostics.append(f"{path.name}: {problem}")
            continue

        # Keep the first record for each business key.
        key = record[key_field]
        if key in seen:
            diagnostics.append(f"{path.name}: duplicate {key_field} {key}")
            continue
        seen.add(key)
        records.append(record)

    return records, diagnostics


def load_shipments(directory):
    """Load all valid shipment records from a directory of JSON files."""
    return _load_records(directory, "shipment_id", _validate_shipment, "Shipment data")


def normalize_customer_name(text):
    """Return a trimmed, case-insensitive customer key."""
    return text.strip().casefold()


def aggregate_customer_profile(customer_query, shipments):
    """Build the customer summary for all matching shipment records."""
    wanted = normalize_customer_name(customer_query)
    matches = []

    # Compare the typed name against every loaded shipment customer.
    for shipment in shipments:
        if normalize_customer_name(shipment["customer"]) == wanted:
            matches.append(shipment)

    # No matches means the export file must stay untouched.
    if not matches:
        return None

    # Destinations must be unique and sorted before they are joined.
    destinations = sorted({shipment["destination"] for shipment in matches})
    total_weight = sum(shipment["weight_kg"] for shipment in matches)
    express_count = sum(1 for shipment in matches if shipment["priority"] == "EXPRESS")

    return {
        "customer": matches[0]["customer"],
        "shipment_count": len(matches),
        "total_weight_kg": total_weight,
        "express_count": express_count,
        "destinations": destinations,
    }


def build_profile_row(profile):
    """Format a profile summary into the exact CSV row shape."""
    return {
        "customer": profile["customer"],
        "shipment_count": str(profile["shipment_count"]),
        "total_weight_kg": f"{profile['total_weight_kg']:.2f}",
        "express_count": str(profile["express_count"]),
        "destinations": "|".join(profile["destinations"]),
    }


def read_customer_profiles(path):
    """Read the customer profile CSV or return an empty list when absent."""
    path = Path(path)

    # A missing export file is allowed on the first write.
    if not path.is_file():
        return []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []

        # The file must already use the exact five-field header in the right order.
        if list(header) != list(CUSTOMER_PROFILE_FIELDS):
            raise ValueError(
                "customer-profiles.csv must use the header "
                + ",".join(CUSTOMER_PROFILE_FIELDS)
            )

        rows = []
        for number, row in enumerate(reader, start=2):
            # Extra columns show up under the None key, so reject them.
            if None in row:
                raise ValueError(
                    f"customer-profiles.csv row {number}: too many columns"
                )

            # Keep the original string values so unrelated customers do not change.
            cleaned = {}
            for field in CUSTOMER_PROFILE_FIELDS:
                if field not in row or row[field] is None:
                    raise ValueError(
                        f"customer-profiles.csv row {number}: missing {field}"
                    )
                cleaned[field] = row[field]
            rows.append(cleaned)

    return rows


def write_customer_profiles(path, rows):
    """Write the customer profile CSV with a single header and a safe rewrite."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None
    try:
        # Write to a temporary file first so a failure never corrupts the real CSV.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            delete=False,
            dir=path.parent,
            prefix=f"{path.stem}.",
            suffix=".tmp",
        ) as handle:
            temp_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=CUSTOMER_PROFILE_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        os.replace(temp_path, path)
    except Exception:
        # Clean up only the temp file created by this attempt.
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def upsert_profile_row(existing_rows, new_row):
    """Replace the matching customer row or append a new one at the end."""
    wanted = normalize_customer_name(new_row["customer"])
    merged = []
    replaced = False

    # Keep untouched rows exactly as they already were.
    for row in existing_rows:
        if not replaced and normalize_customer_name(row["customer"]) == wanted:
            merged.append(new_row)
            replaced = True
        else:
            merged.append(row)

    # If no row matched, append the new customer to the end.
    if not replaced:
        merged.append(new_row)

    return merged


def export_customer_profile():
    """Run the full Task 4 flow from prompt to CSV update."""
    customer_name = prompt("Customer name: ")

    try:
        # Load valid shipments once, then aggregate the customer summary in memory.
        shipments, _diagnostics = load_shipments(SHIPMENTS_DIRECTORY)
        profile = aggregate_customer_profile(customer_name, shipments)
        if profile is None:
            print("Customer not found.")
            return

        # Convert the numeric profile into the exact CSV text fields.
        row = build_profile_row(profile)
        existing_rows = read_customer_profiles(CUSTOMER_PROFILE_PATH)
        merged_rows = upsert_profile_row(existing_rows, row)
        write_customer_profiles(CUSTOMER_PROFILE_PATH, merged_rows)
    except (FileNotFoundError, ValueError, csv.Error, OSError) as error:
        print(f"Error - {error}")
        return

    print("Customer profile updated: exports/customer-profiles.csv")

if __name__ == "__main__":
    export_customer_profile()
