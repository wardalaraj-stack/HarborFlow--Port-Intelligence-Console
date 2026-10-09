"""HarborFlow operational business rules.

Keep calculations and record-processing logic separate from user interaction
where practical.
"""

from datetime import date
import re


_DATE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def parse_reference_date(value):
    """Parse a user-entered date, requiring the exact ISO calendar shape."""
    if not isinstance(value, str) or _DATE_SHAPE.fullmatch(value) is None:
        raise ValueError("date must use YYYY-MM-DD")
    return date.fromisoformat(value)


def resolve_vessel(name, vessels):
    """Return the vessel whose trimmed name matches, or ``None``."""
    wanted = name.strip().casefold()
    for vessel in vessels:
        if vessel["name"].strip().casefold() == wanted:
            return vessel
    return None


def parse_arrival_date(value):
    """Return a real ISO date, or ``None`` for an invalid source value."""
    if not isinstance(value, str) or _DATE_SHAPE.fullmatch(value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def select_call(calls, vessel_id, reference_date):
    """Select the earliest eligible call, breaking same-day ties by ID."""
    selected = None
    selected_key = None
    for call in calls:
        if call["vessel_id"] != vessel_id:
            continue
        arrival = parse_arrival_date(call["arrival_date"])
        if arrival is None or arrival < reference_date:
            continue
        key = (arrival, call["call_id"])
        if selected_key is None or key < selected_key:
            selected_key = key
            selected = call
    return selected


def find_manifest(manifests, call):
    """Return the first manifest identified by both call and vessel IDs."""
    for manifest in manifests:
        if (
            manifest["call_id"] == call["call_id"]
            and manifest["vessel_id"] == call["vessel_id"]
        ):
            return manifest
    return None


def index_shipments(shipments):
    """Index validated shipment records by shipment ID."""
    indexed = {}
    for shipment in shipments:
        indexed.setdefault(shipment["shipment_id"], shipment)
    return indexed


def build_manifest_report(vessel, call, manifest, shipment_lookup):
    """Build an ordered, pure-data manifest report."""
    lines = []
    resolved_weight = 0.0
    missing = 0

    for shipment_id in manifest["shipment_ids"]:
        shipment = shipment_lookup.get(shipment_id)
        if shipment is None:
            lines.append({"resolved": False, "shipment_id": shipment_id})
            missing += 1
            continue

        lines.append(
            {
                "resolved": True,
                "shipment_id": shipment_id,
                "customer": shipment["customer"],
                "weight_kg": shipment["weight_kg"],
                "cargo_type": shipment.get("cargo_type") or "NOT PROVIDED",
                "hazardous": shipment.get("hazardous") or False,
                "temperature_controlled": shipment.get("temperature_controlled")
                or False,
            }
        )
        resolved_weight += shipment["weight_kg"]

    parsed = parse_arrival_date(call["arrival_date"])
    if parsed is None:
        raise ValueError("selected call has an invalid arrival date")

    return {
        "vessel_name": vessel["name"],
        "call_id": call["call_id"],
        "date_display": f"{parsed.day} {parsed.strftime('%B %Y')}",
        "lines": lines,
        "declared": len(manifest["shipment_ids"]),
        "resolved_weight": resolved_weight,
        "missing": missing,
    }
