"""Shared, recovery-oriented loaders for HarborFlow source data."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Diagnostic:
    """A recoverable source-data problem."""

    source: str
    code: str
    message: str


@dataclass
class LoadResult:
    """Records accepted by a loader and its recoverable diagnostics."""

    records: list[dict]
    diagnostics: list[Diagnostic]


VESSEL_TEXT_FIELDS = ("vessel_id", "name", "imo")
PORT_CALL_FIELDS = ("call_id", "vessel_id", "port_code", "arrival_date")
MANIFEST_TEXT_FIELDS = ("call_id", "vessel_id")
MANIFEST_LIST_FIELDS = ("shipment_ids", "event_codes")
SHIPMENT_TEXT_FIELDS = ("shipment_id", "customer", "destination", "priority")


def load_json(path: Path) -> dict:
    """Read one UTF-8 JSON object, propagating read and shape errors."""
    with Path(path).open("r", encoding="utf-8") as handle:
        record = json.load(handle)
    if not isinstance(record, dict):
        raise ValueError("top-level value must be a JSON object")
    return record


def _text_problem(record: dict, fields: tuple[str, ...]) -> str | None:
    for field in fields:
        if field not in record:
            return f"{field} is missing"
        if not isinstance(record[field], str) or not record[field].strip():
            return f"{field} must be non-empty text"
    return None


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_vessel(record: dict) -> None:
    problem = _text_problem(record, VESSEL_TEXT_FIELDS)
    if problem:
        raise ValueError(problem)
    capacity = record.get("capacity_teu")
    if "capacity_teu" not in record:
        raise ValueError("capacity_teu is missing")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity_teu must be a non-negative whole number")


def _validate_port_call(record: dict) -> None:
    problem = _text_problem(record, PORT_CALL_FIELDS)
    if problem:
        raise ValueError(problem)


def _validate_manifest(record: dict) -> None:
    problem = _text_problem(record, MANIFEST_TEXT_FIELDS)
    if problem:
        raise ValueError(problem)
    for field in MANIFEST_LIST_FIELDS:
        value = record.get(field)
        if not isinstance(value, list):
            raise ValueError(f"{field} must be a list")
        if any(not isinstance(item, str) for item in value):
            raise ValueError(f"{field} must contain only text values")


def _validate_shipment(record: dict) -> None:
    problem = _text_problem(record, SHIPMENT_TEXT_FIELDS)
    if problem:
        raise ValueError(problem)
    if "weight_kg" not in record:
        raise ValueError("weight_kg is missing")
    if not _is_number(record["weight_kg"]):
        raise ValueError("weight_kg must be a number")
    for field in ("hazardous", "temperature_controlled"):
        if field in record and record[field] is not None and not isinstance(record[field], bool):
            raise ValueError(f"{field} must be true or false")
    if "cargo_type" in record and record["cargo_type"] is not None:
        if not isinstance(record["cargo_type"], str):
            raise ValueError("cargo_type must be text")


def _json_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f"data directory not found: {directory}")
    return sorted(
        (path for path in directory.iterdir() if path.is_file() and path.suffix.casefold() == ".json"),
        key=lambda path: path.name.casefold(),
    )


def _load_records(
    directory: Path,
    validator: Callable[[dict], None],
    identifier: str,
) -> LoadResult:
    records: list[dict] = []
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()

    for path in _json_files(Path(directory)):
        try:
            record = load_json(path)
            validator(record)
        except FileNotFoundError as error:
            diagnostics.append(Diagnostic(str(path), "file_not_found", str(error)))
            continue
        except json.JSONDecodeError as error:
            diagnostics.append(
                Diagnostic(
                    str(path),
                    "malformed_json",
                    f"malformed JSON at line {error.lineno}, column {error.colno}",
                )
            )
            continue
        except ValueError as error:
            diagnostics.append(Diagnostic(str(path), "invalid_record", str(error)))
            continue

        key = record[identifier]
        if key in seen:
            diagnostics.append(
                Diagnostic(str(path), "duplicate_identifier", f"duplicate {identifier} {key}")
            )
            continue
        seen.add(key)
        records.append(record)

    return LoadResult(records, diagnostics)


def load_vessels(directory: Path) -> LoadResult:
    return _load_records(directory, _validate_vessel, "vessel_id")


def load_manifests(directory: Path) -> LoadResult:
    return _load_records(directory, _validate_manifest, "call_id")


def load_shipments(directory: Path) -> LoadResult:
    return _load_records(directory, _validate_shipment, "shipment_id")


def load_port_calls(path: Path) -> LoadResult:
    """Load structurally valid CSV rows while preserving source strings."""
    path = Path(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [field for field in PORT_CALL_FIELDS if field not in header]
        if missing:
            raise ValueError(f"port_calls.csv is missing columns: {', '.join(missing)}")

        records: list[dict] = []
        diagnostics: list[Diagnostic] = []
        seen: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            source = f"{path}:row {row_number}"
            empty = [
                field
                for field in PORT_CALL_FIELDS
                if row.get(field) is None or row[field].strip() == ""
            ]
            if empty:
                diagnostics.append(
                    Diagnostic(source, "invalid_row", f"missing {', '.join(empty)}")
                )
                continue

            call_id = row["call_id"]
            key = call_id
            if key in seen:
                diagnostics.append(
                    Diagnostic(source, "duplicate_identifier", f"duplicate call_id {call_id}")
                )
                continue
            seen.add(key)
            records.append({field: row[field] for field in PORT_CALL_FIELDS})

    return LoadResult(records, diagnostics)
