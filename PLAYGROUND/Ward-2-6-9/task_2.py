"""Standalone Task 2 service: inspect a vessel manifest.
"""

# import makes a built-in Python tool available to this file.
# json reads JSON files, csv reads spreadsheet-style files, sys reads the
# command line, io holds text in memory, contextlib redirects printed text,
# and re searches text with patterns.
import csv
import json
import re
from datetime import date
from pathlib import Path
from task_1 import load_json , validate_vessel , load_vessels





# ---------------------------------------------------------------- ----------
# Paths
# --------------------------------------------------------------------------
# Path(__file__) is this file. .resolve() makes it a full path. .parents[2]
# walks up three folders: TEST_CODE -> tests -> ass2. Everything the service
# reads is reached from there, so the file works from any working directory
# and never stores one student's machine-specific absolute path.
DATASET_DIRECTORY = Path(__file__).resolve().parents[2] / "dataset"
VESSELS_DIRECTORY = DATASET_DIRECTORY / "vessels"
PORT_CALLS_FILE = DATASET_DIRECTORY / "port_calls.csv"
MANIFESTS_DIRECTORY = DATASET_DIRECTORY / "manifests"
SHIPMENTS_DIRECTORY = DATASET_DIRECTORY / "shipments"

# The four vessel fields the task requires. An all-capital name is the usual
# convention for a value that never changes.
VESSEL_TEXT_FIELDS = ("vessel_id", "name", "imo")
MANIFEST_TEXT_FIELDS = ("call_id", "vessel_id")
MANIFEST_LIST_FIELDS = ("shipment_ids", "event_codes")
SHIPMENT_TEXT_FIELDS = ("shipment_id", "customer", "destination", "priority")
PORT_CALL_FIELDS = ("call_id", "vessel_id", "port_code", "arrival_date")
# A pattern for a user-typed date: four digits, a dash, two digits, a dash,
# two digits. re.fullmatch means the whole text must match, not just a part.
DATE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}")


# ---------------------------------------------------------------- ----------
# Reading one JSON file
# --------------------------------------------------------------------------
# ---------------------------------------------------------------- ----------
# Small validation helpers
# --------------------------------------------------------------------------
def text_fields(record, fields):
    # This helper collects the names in fields that are missing, empty, or
    # not text. It returns an empty list when everything is acceptable.
    """Return the names from fields that are absent or not non-empty text."""
    problems = []
    for field in fields:
        # "not in record" asks whether the key exists at all.
        if field not in record:
            problems.append(f"{field} is missing")
        # isinstance(value, str) asks "is this value text?" and .strip()
        # removes surrounding spaces so "" or "   " counts as empty.
        elif not isinstance(record[field], str) or not record[field].strip():
            problems.append(f"{field} must be non-empty text")
    return problems


def is_whole_number(value):
    # Numbers in JSON arrive as int or float. bool is a special kind of
    # number in Python, so True must be rejected separately.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_manifest(record):
    """Return a problem message for one manifest record, or None if it is good."""
    problems = text_fields(record, MANIFEST_TEXT_FIELDS)
    if problems:
        return problems[0]
    # shipment_ids and event_codes must exist and be lists whose items are
    # all text. Both lists keep their original order; empty lists are fine.
    for field in MANIFEST_LIST_FIELDS:
        value = record.get(field)
        if not isinstance(value, list):
            return f"{field} must be a list"
        if any(not isinstance(item, str) for item in value):
            return f"{field} must contain only text values"
    return None


def validate_shipment(record):
    """Return a problem message for one shipment record, or None if it is good."""
    # weight_kg is a number, so only the text fields are checked here.
    problems = text_fields(record, SHIPMENT_TEXT_FIELDS)
    if problems:
        return problems[0]
    if "weight_kg" not in record:
        return "weight_kg is missing"
    if not is_whole_number(record["weight_kg"]):
        return "weight_kg must be a number"
    # hazardous and temperature_controlled are optional. When the key is
    # present its value must really be true or false; when it is absent the
    # record is still usable.
    for field in ("hazardous", "temperature_controlled"):
        if record.get(field) is not None and not isinstance(record[field], bool):
            return f"{field} must be true or false"
    # cargo_type is optional text. A missing value is shown as NOT PROVIDED
    # later, but a present value of the wrong type makes the record unusable.
    if record.get("cargo_type") is not None and not isinstance(record["cargo_type"], str):
        return "cargo_type must be text"
    return None


# ---------------------------------------------------------------- ----------
# Loading whole folders of records
# --------------------------------------------------------------------------
def load_records(directory, key_field, validate, label):
    """Load every JSON object in a folder and return records with problems.

    Files are visited in sorted order so the same run always reports the
    same messages. A broken file is recorded and skipped; the remaining
    files are still loaded, so one bad record never hides the good ones.
    """
    directory = Path(directory)
    # is_dir asks whether this location is an existing folder.
    if not directory.is_dir():
        raise FileNotFoundError(f"{label} directory not found: {directory}")

    records = []
    # problems holds one readable explanation for every skipped file.
    problems = []
    # seen remembers the identifier of each record already accepted, so a
    # duplicate identifier keeps its first record and skips later ones.
    seen = set()

    # glob("*.json") finds names ending in .json; * means "any filename".
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name.casefold()):
        try:
            record = load_json(path)
        # except handles one particular kind of problem; error stores it.
        except FileNotFoundError as error:
            problems.append(f"{path.name}: {error}")
            continue
        except json.JSONDecodeError as error:
            # JSONDecodeError means the text is not valid JSON, and the
            # error also says where reading failed.
            problems.append(
                f"{path.name}: malformed JSON at line {error.lineno}, "
                f"column {error.colno}"
            )
            continue
        except ValueError as error:
            # Valid JSON whose top-level value was not an object.
            problems.append(f"{path.name}: {error}")
            continue

        # Ask the matching validator whether this record can be used.
        problem = validate(record)
        if problem is not None:
            problems.append(f"{path.name}: {problem}")
            continue

        key = record[key_field]
        if key in seen:
            problems.append(f"{path.name}: duplicate {key_field} {key}")
            continue
        seen.add(key)
        records.append(record)

    return records, problems


def load_manifests(directory):
    """Load valid manifests together with the rejected-file messages."""
    return load_records(directory, "call_id", validate_manifest, "Manifest data")


def load_shipments(directory):
    """Load valid shipments together with the rejected-file messages."""
    return load_records(directory, "shipment_id", validate_shipment, "Shipment data")


def load_port_calls(path):
    """Read port_calls.csv and return its rows together with row problems.

    Dates are kept exactly as written in the file. Deciding whether a date
    is a real calendar date belongs to the operation that selects a call, so
    one strange row can never stop the rest of the file from loading.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Port call file not found: {path}")

    rows = []
    problems = []
    # newline="" is the recommended setting when a file is read with csv.
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [name for name in PORT_CALL_FIELDS if name not in header]
        # A header that does not describe the expected columns is a schema
        # problem, so it stops this loader instead of pretending the file
        # simply had no rows.
        if missing:
            raise ValueError(
                f"port_calls.csv is missing columns: {', '.join(missing)}"
            )

        seen = set()
        # enumerate numbers each row, starting at 2 because row 1 is the
        # header. That number identifies a row in any problem message.
        for number, row in enumerate(reader, start=2):
            empty = [
                name for name in PORT_CALL_FIELDS
                if row.get(name) is None or str(row[name]).strip() == ""
            ]
            if empty:
                problems.append(
                    f"port_calls.csv row {number}: missing {', '.join(empty)}"
                )
                continue
            call_id = row["call_id"]
            if call_id in seen:
                problems.append(
                    f"port_calls.csv row {number}: duplicate call_id {call_id}"
                )
                continue
            seen.add(call_id)
            # The row is stored as a plain dictionary keyed by the header.
            rows.append({name: row[name] for name in PORT_CALL_FIELDS})

    return rows, problems


# ---------------------------------------------------------------- ----------
# Reading one value from the user
# --------------------------------------------------------------------------
def prompt(message):
    """Print a question without a newline and return the typed answer."""
    # print(..., end="") keeps the cursor on the same line as the question,
    # which is how a console prompt normally looks. flush=True makes sure
    # the question appears before the program waits for typing.
    print(message, end="", flush=True)
    # input() with no text reads one line. The text the user types is not
    # echoed into our captured output; the question above is.
    return input()


def ask_reference_date():
    """Ask for a date until the user types a real YYYY-MM-DD date."""
    while True:
        answer = prompt("Reference date (YYYY-MM-DD): ")
        try:
            # date_shape check first: fromisoformat also accepts dates
            # written without dashes, so the shape is confirmed here.
            if not DATE_SHAPE.fullmatch(answer.strip()):
                raise ValueError(answer)
            # fromisoformat builds a real calendar date. It rejects
            # impossible days such as 2026-02-30 with a ValueError.
            return date.fromisoformat(answer.strip())
        except ValueError:
            # Only the date question is repeated. The vessel name is not
            # asked again and the service does not return to the menu.
            print("Error - Date must use YYYY-MM-DD.")


# ---------------------------------------------------------------- ----------
# Pure business rules (no printing here, so they are easy to test)
# --------------------------------------------------------------------------
def resolve_vessel(name, vessels):
    """Return the vessel whose name matches, or None when there is no match."""
    # strip removes surrounding spaces and casefold compares letters without
    # caring about upper or lower case, so "  nordic relay  " matches.
    wanted = name.strip().casefold()
    for vessel in vessels:
        if vessel["name"].strip().casefold() == wanted:
            return vessel
    return None


def parse_arrival_date(value):
    """Return a real date for a CSV arrival_date, or None when it is not one."""
    if not isinstance(value, str) or not DATE_SHAPE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        # A row such as 2026-02-30 is not a calendar day. It is simply not
        # a candidate; it never crashes the service and never gets picked.
        return None


def select_call(calls, vessel_id, reference_date):
    """Return the earliest eligible call for a vessel, or None if there is none.

    Two rules decide the answer: a call qualifies when its arrival date is on
    or after the reference date, and the earliest date wins. When several
    calls share that date, the alphabetically smallest call_id wins.
    """
    best = None
    for call in calls:
        if call["vessel_id"] != vessel_id:
            continue
        arrival = parse_arrival_date(call["arrival_date"])
        # A call earlier than the reference date does not qualify, and an
        # unparseable date never qualifies either.
        if arrival is None or arrival < reference_date:
            continue
        # The comparison key is a pair: date first, call_id second. Python
        # compares pairs from left to right, so the earliest date is chosen
        # first and only equal dates fall through to the call_id text.
        key = (arrival, call["call_id"])
        if best is None or key < best[0]:
            best = (key, call)
    # best[1] is the winning call; None means no call qualified.
    return best[1] if best is not None else None


def find_manifest(manifests, call):
    """Return the usable manifest for a call, or None when there is none.

    A manifest is found by the call_id stored inside the file, never by a
    filename that happens to look similar.
    """
    for manifest in manifests:
        if manifest["call_id"] != call["call_id"]:
            continue
        # The manifest must also describe the same vessel as the selected
        # call, otherwise it does not belong to this call.
        if manifest["vessel_id"] != call["vessel_id"]:
            continue
        return manifest
    return None


def index_shipments(shipments):
    """Return a lookup from shipment_id to the first valid shipment record."""
    lookup = {}
    for shipment in shipments:
        # setdefault keeps the first record loaded for an identifier; the
        # loader has already diagnosed and skipped later duplicates.
        lookup.setdefault(shipment["shipment_id"], shipment)
    return lookup


def display_date(value):
    """Turn an ISO date such as 2026-10-18 into 18 October 2026."""
    parsed = date.fromisoformat(value)
    # strftime("%B") is the full month name. The day is added separately
    # because %d would print 08 instead of 8 for a single-digit day.
    return f"{parsed.day} {parsed.strftime('%B %Y')}"


def build_report(vessel, call, manifest, shipment_lookup):
    """Collect every value the report needs without printing anything.

    Walking the manifest in its own order keeps the displayed numbering the
    same as the order the shipments were declared in.
    """
    lines = []
    resolved_weight = 0.0
    missing = 0

    for shipment_id in manifest["shipment_ids"]:
        shipment = shipment_lookup.get(shipment_id)
        if shipment is None:
            # The identifier was declared but no readable shipment record
            # exists for it. It keeps its line, is counted as missing, and
            # adds nothing to the resolved weight.
            lines.append({"resolved": False, "shipment_id": shipment_id})
            missing += 1
            continue
        # An optional field that is absent or null becomes NOT PROVIDED.
        cargo_type = shipment.get("cargo_type")
        if cargo_type is None:
            cargo_type = "NOT PROVIDED"
        lines.append({
            "resolved": True,
            "shipment_id": shipment_id,
            "customer": shipment["customer"],
            "weight_kg": shipment["weight_kg"],
            "cargo_type": cargo_type,
        })
        resolved_weight += shipment["weight_kg"]

    return {
        "vessel_name": vessel["name"],
        "call_id": call["call_id"],
        "date_display": display_date(call["arrival_date"]),
        "lines": lines,
        # Declared counts every identifier the manifest lists, whether or
        # not a record could be found for it.
        "declared": len(manifest["shipment_ids"]),
        "resolved_weight": resolved_weight,
        "missing": missing,
    }


def print_report(report):
    """Print one report using the exact wording required by the assignment."""
    print(
        f"Manifest for {report['vessel_name']} | Call {report['call_id']} | "
        f"{report['date_display']}"
    )
    # enumerate(..., start=1) numbers the lines from 1 in manifest order.
    for number, line in enumerate(report["lines"], start=1):
        if line["resolved"]:
            # The weight keeps its natural form here; only the summary line
            # below is forced to two decimal places.
            print(
                f"{number}. {line['shipment_id']} | {line['customer']} | "
                f"{line['weight_kg']} kg | {line['cargo_type']}"
            )
        else:
            # A missing record has fewer parts than a resolved line.
            print(f"{number}. {line['shipment_id']} | MISSING RECORD")
    print(f"Declared shipments: {report['declared']}")
    print(f"Resolved weight: {report['resolved_weight']:.2f} kg")
    print(f"Missing shipment records: {report['missing']}")


def print_inventory(vessels, rejected_files):
    """Display the registered vessels, using the Task 1 display."""
    print("Registered HarborFlow vessels:")
    for vessel in vessels:
        # :, formats a number with a thousands separator for display only.
        capacity = f"{vessel['capacity_teu']:,}"
        print(f"- {vessel['name']} | IMO {vessel['imo']} | {capacity} TEU")
    for rejection in rejected_files:
        print(f"Skipped {rejection}")
    print(f"Skipped vessel files: {len(rejected_files)}")


# ---------------------------------------------------------------- ----------
# The service itself
# --------------------------------------------------------------------------
def service():
    """Run menu option 2 once and print its result.

    In the integrated console this function is called from option 2 and
    control returns to the menu afterwards. This standalone file simply
    reaches the end of the program instead.
    """
    # Load everything first. Each loader raises one of these named errors
    # when a whole file or folder cannot be used at all. Catching them by
    # name keeps real programming mistakes visible instead of hiding them.
    try:
        vessels, vessel_problems = load_vessels(VESSELS_DIRECTORY)
        # The other three problems are read but not printed: this task has
        # no required wording for a bad row or file, and one unusable
        # record must never stop the records that follow it.
        calls, _call_problems = load_port_calls(PORT_CALLS_FILE)
        manifests, _manifest_problems = load_manifests(MANIFESTS_DIRECTORY)
        shipments, _shipment_problems = load_shipments(SHIPMENTS_DIRECTORY)
    except (FileNotFoundError, json.JSONDecodeError, csv.Error, ValueError) as error:
        print(f"Error - {error}")
        return

    # Step 1: show which vessels are registered before asking for a name.
    print_inventory(vessels, vessel_problems)

    # Step 2: read the name. It is only a candidate after trimming spaces
    # and comparing letters without case.
    name = prompt("Vessel name: ")
    vessel = resolve_vessel(name, vessels)
    if vessel is None:
        # The exact message for an unknown vessel, and no date question.
        print("Vessel not found.")
        return

    # Step 3: the date question repeats here, inside this function, until a
    # real YYYY-MM-DD date arrives. Nothing else is asked again.
    reference_date = ask_reference_date()

    # Step 4: choose the call for this vessel on or after that date.
    call = select_call(calls, vessel["vessel_id"], reference_date)
    if call is None:
        print("No upcoming port calls found.")
        return

    # Step 5: find the manifest through the call_id stored inside it.
    manifest = find_manifest(manifests, call)
    if manifest is None:
        print("Manifest unavailable.")
        return

    # Step 6: resolve the declared shipments and print the report.
    report = build_report(vessel, call, manifest, index_shipments(shipments))
    print_report(report)


if __name__ == "__main__":
    service()
