"""Standalone Task 5 service: find port calls by month."""

# This file keeps Task 5 separate from the shared console entry point.
# It reads port_calls.csv, resolves vessel names from the vessels folder,
# filters by a user-chosen month, and prints a sorted planning report.

import calendar
import csv
import json
from datetime import date
from pathlib import Path


# Walk back from TEST_CODE → tests → ass2 to reach the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIRECTORY = PROJECT_ROOT / "data" / "dataset"
PORT_CALLS_FILE = DATASET_DIRECTORY / "port_calls.csv"
VESSELS_DIRECTORY = DATASET_DIRECTORY / "vessels"

# The four CSV columns this task reads by name, never by column position.
PORT_CALL_FIELDS = ("call_id", "vessel_id", "port_code", "arrival_date")

# Vessel text fields required for a record to be usable in name resolution.
VESSEL_REQUIRED_TEXT = ("vessel_id", "name", "imo")


# ---------------------------------------------------------------------------
# Shared low-level helpers  (same pattern as tasks 1–4, defined locally so
# this file stays standalone without importing from other task files)
# ---------------------------------------------------------------------------

def load_json(path):
    """Read one JSON object from a file and return it as a dictionary."""
    with Path(path).open("r", encoding="utf-8") as json_file:
        record = json.load(json_file)
    # Guard against a valid JSON file whose top-level value is a list or
    # scalar — only a JSON object maps cleanly to a Python dictionary.
    if not isinstance(record, dict):
        raise ValueError("top-level value must be a JSON object")
    return record


def _validate_vessel(record):
    """Return a problem string for one vessel record, or None if it is valid."""
    for field in VESSEL_REQUIRED_TEXT:
        if field not in record:
            return f"{field} is missing"
        if not isinstance(record[field], str) or not record[field].strip():
            return f"{field} must be non-empty text"
    if "capacity_teu" not in record:
        return "capacity_teu is missing"
    capacity = record["capacity_teu"]
    # bool is a subclass of int in Python, so it must be excluded explicitly.
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        return "capacity_teu must be a non-negative whole number"
    return None


def load_vessels(directory):
    """Load valid vessel records and return them with skipped-file diagnostics."""
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Vessel data directory not found: {directory}")

    vessels = []
    diagnostics = []
    seen_ids = set()

    # Sorted filenames make repeated runs report messages in the same order.
    for path in sorted(directory.glob("*.json"), key=lambda p: p.name.casefold()):
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

        problem = _validate_vessel(record)
        if problem is not None:
            diagnostics.append(f"{path.name}: {problem}")
            continue

        vessel_id = record["vessel_id"]
        if vessel_id in seen_ids:
            diagnostics.append(f"{path.name}: duplicate vessel_id {vessel_id}")
            continue

        seen_ids.add(vessel_id)
        vessels.append(record)

    return vessels, diagnostics


def load_port_calls(path):
    """Read port_calls.csv and return its rows with any row-level diagnostics.

    Dates are kept as raw text so Task 5 can validate each row's date
    individually — one unparseable date must not hide later valid rows.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Port call file not found: {path}")

    rows = []
    diagnostics = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [name for name in PORT_CALL_FIELDS if name not in header]
        # A missing column is a schema problem that makes the whole file unusable.
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


# ---------------------------------------------------------------------------
# Task 5 business logic
# ---------------------------------------------------------------------------

def parse_month(text):
    """Parse and range-check a month string; raises ValueError if invalid.

    Strips surrounding whitespace before converting so "  10  " is accepted
    like "10". Both a non-integer string and a value outside 1–12 raise
    ValueError so the caller can use one branch to print the single required
    error message and repeat only the month prompt.
    """
    month = int(text.strip())
    if not 1 <= month <= 12:
        raise ValueError(f"month {month} is out of the allowed range 1–12")
    return month


def build_vessel_lookup(vessels):
    """Return a mapping from vessel_id to display name for fast resolution."""
    return {vessel["vessel_id"]: vessel["name"] for vessel in vessels}


def collect_month_calls(month, call_rows, vessel_lookup):
    """Filter and sort call rows that fall in the requested month.

    For each row the order of checks is:
      1. Parse arrival_date — if invalid, report and skip (date check first).
      2. Resolve vessel_id — if unknown, report and skip.
      3. Keep only rows whose parsed date.month equals the requested month.

    Returns (sorted_calls, diagnostics) where each accepted call is a dict
    with: arrival_date_obj, vessel_name, port_code, call_id.
    Sort order: arrival date ascending, then vessel name (casefolded),
    then call_id as a deterministic tiebreaker for otherwise equal pairs.
    """
    matched = []
    diagnostics = []

    for row in call_rows:
        call_id = row["call_id"]
        arrival_text = row["arrival_date"]

        # Date validation is always the first check; a bad date skips the
        # vessel lookup so each rejected row produces exactly one diagnostic.
        try:
            arrival = date.fromisoformat(arrival_text)
        except ValueError:
            diagnostics.append(
                f"Skipped {call_id}: invalid arrival date '{arrival_text}'"
            )
            continue

        # Vessel resolution is only attempted after the date is confirmed valid.
        vessel_name = vessel_lookup.get(row["vessel_id"])
        if vessel_name is None:
            diagnostics.append(
                f"Skipped {call_id}: unknown vessel_id '{row['vessel_id']}'"
            )
            continue

        # Filter by month; the year is not part of the user's query.
        if arrival.month != month:
            continue

        matched.append({
            "arrival_date_obj": arrival,
            "vessel_name": vessel_name,
            "port_code": row["port_code"],
            "call_id": call_id,
        })

    # Sort after all filtering is done so every accepted row is included.
    matched.sort(
        key=lambda c: (
            c["arrival_date_obj"],
            c["vessel_name"].casefold(),
            c["call_id"],
        )
    )
    return matched, diagnostics


def format_call_line(call):
    """Format one call as the required display line with a zero-padded day.

    The assignment example shows '02 October 2026', so %d is used (which
    zero-pads single-digit days) rather than stripping the leading zero.
    """
    day = call["arrival_date_obj"].strftime("%d")
    month_name = call["arrival_date_obj"].strftime("%B")
    year = call["arrival_date_obj"].strftime("%Y")
    return (
        f"- {day} {month_name} {year} | "
        f"{call['vessel_name']} | "
        f"{call['port_code']} | "
        f"{call['call_id']}"
    )


def format_month_heading(month):
    """Return the heading line for the requested month number."""
    # calendar.month_name is a sequence indexed 1–12, matching the user input.
    return f"Port calls in {calendar.month_name[month]}:"


def service():
    """Run the full Task 5 flow: prompt for month, load data, print report."""

    # --- Month input loop ---
    # Repeat only the month prompt on each invalid entry; never return to the
    # menu or ask for any other field inside this retry loop.
    while True:
        answer = input("Month (1-12): ")
        try:
            month = parse_month(answer)
            break
        except ValueError:
            print("Error - Enter a month from 1 to 12.")

    # --- Load data ---
    try:
        vessels, _vessel_diagnostics = load_vessels(VESSELS_DIRECTORY)
        call_rows, _call_diagnostics = load_port_calls(PORT_CALLS_FILE)
    except (FileNotFoundError, ValueError, csv.Error) as error:
        print(f"Error - {error}")
        return

    # --- Filter and sort ---
    vessel_lookup = build_vessel_lookup(vessels)
    calls, row_diagnostics = collect_month_calls(month, call_rows, vessel_lookup)

    # Print a line for each skipped row; they must not prevent valid rows
    # from appearing and the assignment does not mandate exact wording here.
    for message in row_diagnostics:
        print(message)

    # --- Print report ---
    if not calls:
        print("No port calls found.")
        return

    print(format_month_heading(month))
    for call in calls:
        print(format_call_line(call))


if __name__ == "__main__":
    service()

